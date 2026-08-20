"""GEE → OGE 的纯算法实现。

本文件从 ``case_study_pipeline.py`` 中抽取核心规则，去除了 Flask、
SQLite、LLM、缓存和结果持久化等工程代码。调用方只需自行提供 API 映射字典。
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional


IMAGE_METHODS = {
    'select', 'subtract', 'add', 'multiply', 'divide', 'rename', 'clip', 'mask',
    'unmask', 'updateMask', 'where', 'and', 'or', 'not', 'eq', 'gt', 'gte', 'lt',
    'lte', 'abs', 'sqrt', 'pow', 'log', 'exp', 'cos', 'sin', 'tan', 'min', 'max',
    'sum', 'mean', 'median', 'count', 'reduce', 'reduceRegion', 'reduceRegions',
    'sample', 'sampleRegions', 'classify', 'visualize', 'unitScale',
    'normalizedDifference', 'expression', 'bandNames', 'bandTypes', 'set', 'get',
    'toArray', 'toDouble', 'toFloat', 'toInt', 'toInt32', 'addBands',
    'selectBands', 'resample', 'reduceResolution', 'reproject', 'cast', 'unmix',
    'trim', 'convolve', 'focal_mean', 'focal_max', 'focal_min', 'gradient', 'kernel',
}
FEATURE_METHODS = {
    'set', 'get', 'geometry', 'area', 'length', 'perimeter', 'buffer', 'bounds',
    'centroid', 'contains', 'intersects', 'withinDistance', 'distance',
    'intersection', 'union', 'difference', 'symmetricDifference', 'simplify',
    'transform',
}
COLLECTION_METHODS = {
    'filter', 'filterDate', 'filterBounds', 'filterMetadata', 'map', 'select',
    'first', 'limit', 'sort', 'size', 'getInfo', 'geometry', 'union',
    'aggregate_array', 'aggregate_stats', 'aggregate_count', 'aggregate_max',
    'aggregate_min', 'aggregate_mean', 'aggregate_sum', 'aggregate_product',
    'reduceToImage', 'reduceToVectors', 'randomColumn', 'style', 'merge',
    'flatten', 'distinct', 'toList',
}
GEOMETRY_METHODS = FEATURE_METHODS | {
    'coordinates', 'geodesic', 'srid', 'type',
}
NUMBER_METHODS = {
    'add', 'subtract', 'multiply', 'divide', 'abs', 'sqrt', 'pow', 'round',
    'floor', 'ceil', 'toInt', 'toFloat', 'format', 'lt', 'lte', 'gt', 'gte',
    'eq', 'neq', 'and', 'or', 'not', 'min', 'max', 'log', 'exp', 'sin', 'cos', 'tan',
}
STRING_METHODS = {
    'cat', 'slice', 'indexOf', 'toUpperCase', 'toLowerCase', 'replace', 'split',
    'length', 'regexpExtract',
}
DATE_METHODS = {'advance', 'difference', 'get', 'format', 'millis', 'getRange', 'getRelative', 'unitDifference'}
LIST_METHODS = {'get', 'map', 'iterate', 'slice', 'reverse', 'sort', 'size', 'contains', 'indexOf', 'add', 'remove', 'set', 'repeat', 'flatten', 'cat', 'reduce', 'sort_combined'}
DICTIONARY_METHODS = {'get', 'set', 'keys', 'values', 'size', 'contains', 'rename', 'select'}

METHODS_BY_TYPE = {
    'ee.Image': IMAGE_METHODS,
    'ee.Feature': FEATURE_METHODS,
    'ee.FeatureCollection': COLLECTION_METHODS,
    'ee.ImageCollection': COLLECTION_METHODS,
    'ee.Geometry': GEOMETRY_METHODS,
    'ee.Number': NUMBER_METHODS,
    'ee.String': STRING_METHODS,
    'ee.Date': DATE_METHODS,
    'ee.List': LIST_METHODS,
    'ee.Dictionary': DICTIONARY_METHODS,
}

RETURN_TYPES = {
    # 保持影像类型的方法
    **{name: 'ee.Image' for name in IMAGE_METHODS - {'bandNames', 'bandTypes', 'get', 'reduce', 'reduceRegion', 'reduceRegions', 'sample', 'sampleRegions', 'classify', 'visualize', 'mean', 'median', 'count', 'sum'}},
    # 返回几何对象的方法
    'buffer': 'ee.Geometry', 'bounds': 'ee.Geometry', 'centroid': 'ee.Geometry',
    'simplify': 'ee.Geometry', 'transform': 'ee.Geometry', 'intersection': 'ee.Geometry',
    'union': 'ee.Geometry', 'difference': 'ee.Geometry', 'symmetricDifference': 'ee.Geometry',
    'geometry': 'ee.Geometry',
}


def split_steps(gee_code: str) -> List[Dict[str, str]]:
    """按单行注释分割 GEE 脚本；无注释时返回整个脚本作为一个步骤。"""
    groups: List[Dict[str, str]] = []
    current_description: Optional[str] = None
    current_lines: List[str] = []

    def flush() -> None:
        nonlocal current_description, current_lines
        code = '\n'.join(current_lines).strip()
        if code:
            groups.append({
                'step_description': current_description or 'Code Execution',
                'code_snippet': code,
            })
        current_description, current_lines = None, []

    for line in gee_code.splitlines():
        comment = re.match(r'^\s*//\s*(.+?)\s*$', line)
        if comment:
            text = comment.group(1).strip()
            if not re.sub(r'[-=#!\s]', '', text):
                flush()
            else:
                flush()
                current_description = re.sub(r'[-=#!]{2,}', '', text).strip() or 'Code Execution'
        else:
            current_lines.append(line)
    flush()
    return groups or [{'step_description': 'Whole script', 'code_snippet': gee_code.strip()}]


def extract_key_parameters(gee_code: str) -> Dict[str, Any]:
    """从脚本中提取数据源、波段、坐标、日期和常用属性等迁移关键信息。"""
    params: Dict[str, Any] = {}
    datasets = re.findall(r"ee\.Image(?:Collection)?\(['\"]([^'\"]+)['\"]\)", gee_code)
    if datasets:
        params['datasets'] = sorted(set(datasets))
    bands = re.findall(r"\.select\(['\"]([^'\"]+)['\"]\)", gee_code)
    if bands:
        params['bands'] = sorted(set(bands))
    indices = re.findall(r"\.rename\(['\"]([^'\"]+)['\"]\)", gee_code)
    if indices:
        params['indices'] = sorted(set(indices))
    dates = re.findall(r"['\"](\d{4}-\d{2}-\d{2})['\"]", gee_code)
    if dates:
        params['dates'] = sorted(set(dates))
    centers = re.search(r'Map\.setCenter\(([\d.\-]+),\s*([\d.\-]+),\s*(\d+)\)', gee_code)
    if centers:
        params['map_center'] = {'lng': float(centers[1]), 'lat': float(centers[2]), 'zoom': int(centers[3])}
    points = re.findall(r'ee\.Geometry\.Point\(\[([\d.\-]+),\s*([\d.\-]+)\]\)', gee_code)
    if points:
        params['geometry_points'] = [{'lng': float(x), 'lat': float(y)} for x, y in points]
    return params


def infer_variable_types(code: str) -> Dict[str, str]:
    """从构造、复制和常见链式赋值推断变量的 GEE 基础类型。"""
    types: Dict[str, str] = {}
    declaration = re.compile(
        r'(?:var|let|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
        r'(ee\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\('
    )
    for variable, api in declaration.findall(code):
        parts = api.split('.')
        types[variable] = '.'.join(parts[:2])

    # 迭代允许 y = x 和 y = x.method() 依赖前面的推断结果。
    for _ in range(2):
        for target, source in re.findall(
            r'(?:var|let|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\s*[;\n]', code
        ):
            if source in types:
                types.setdefault(target, types[source])
        for target, source, method in re.findall(
            r'(?:var|let|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
            r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(', code
        ):
            inferred = RETURN_TYPES.get(method)
            if source in types and inferred and (inferred == types[source] or inferred == 'ee.Geometry'):
                types.setdefault(target, inferred)
    return types


def extract_gee_apis(code: str, variable_types: Optional[Mapping[str, str]] = None) -> List[str]:
    """识别构造、静态、Map/Export 和已知类型变量上的 GEE API 调用。"""
    apis = set(re.findall(r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*)\s*\(', code))
    apis.update(re.findall(r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\s*\(', code))
    apis.update(re.findall(r'\b(Map\.[A-Za-z_][A-Za-z0-9_]*)\s*\(', code))
    apis.update(re.findall(r'\b(Export\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\(', code))
    if re.search(r'\bprint\s*\(', code):
        apis.add('print')

    for variable, gee_type in (variable_types or infer_variable_types(code)).items():
        allowed = METHODS_BY_TYPE.get(gee_type, set())
        for method in re.findall(rf'\b{re.escape(variable)}\.([A-Za-z_][A-Za-z0-9_]*)\s*\(', code):
            if method in allowed:
                apis.add(f'{gee_type}.{method}')
    return sorted(apis)


def match_apis(
    api_names: Iterable[str],
    mappings: Mapping[str, Mapping[str, Any]],
    fallback: Optional[Callable[[str], Optional[Mapping[str, Any]]]] = None,
    min_confidence: float = 0.6,
) -> Dict[str, Any]:
    """用传入的映射字典匹配 API；可选 fallback 用于外部语义匹配。"""
    details = []
    for api in api_names:
        mapping = mappings.get(api)
        if mapping and mapping.get('mapping_type') != 'missing':
            details.append({'gee_api': api, 'status': 'matched', **dict(mapping)})
            continue
        rescue = fallback(api) if fallback else None
        if rescue and rescue.get('matched') and rescue.get('confidence', 0) >= min_confidence:
            details.append({'gee_api': api, 'status': 'matched', 'mapping_type': 'semantic', **dict(rescue)})
        else:
            details.append({'gee_api': api, 'status': 'missing'})
    matched = sum(item['status'] == 'matched' for item in details)
    return {
        'details': details,
        'matched_count': matched,
        'missing_apis': [item['gee_api'] for item in details if item['status'] == 'missing'],
        'match_rate': matched / len(details) if details else 0.0,
    }


def classify_feasibility(missing_apis: Iterable[str]) -> Dict[str, Any]:
    """将缺失 API 分为阻断性、非阻断性和可用 Python 补充的辅助缺口。"""
    blocking_keywords = ('Image', 'ImageCollection', 'Feature', 'FeatureCollection', 'Reducer', 'Classifier', 'Filter')
    ui_keywords = ('Map.addLayer', 'Map.setCenter', 'Map.setOptions', 'print', 'Export')
    blocking, non_blocking, suggestions = [], [], []
    for api in missing_apis:
        if any(token in api for token in ui_keywords):
            non_blocking.append(api)
            suggestions.append({'api': api, 'suggestion': 'UI/可视化缺口，可改用 print 或注释。'})
        elif any(token in api for token in blocking_keywords):
            blocking.append(api)
            suggestions.append({'api': api, 'suggestion': '核心分析算子缺失，需补充 Python 实现或替代 OGE 算子。'})
        else:
            non_blocking.append(api)
            suggestions.append({'api': api, 'suggestion': '辅助算子缺失，可用 Python 原生逻辑补充。'})
    return {
        'overall_feasible': not blocking,
        'blocking_apis': blocking,
        'non_blocking_gaps': non_blocking,
        'rescue_suggestions': suggestions,
    }


def analyze_gee_code(gee_code: str, mappings: Optional[Mapping[str, Mapping[str, Any]]] = None) -> Dict[str, Any]:
    """执行不依赖工程服务的核心分析：分步、参数提取、类型推断、API 提取和可行性。"""
    steps = split_steps(gee_code)
    variable_types = infer_variable_types(gee_code)
    all_apis = extract_gee_apis(gee_code, variable_types)
    result: Dict[str, Any] = {
        'steps': steps,
        'key_params': extract_key_parameters(gee_code),
        'variable_types': variable_types,
        'all_apis': all_apis,
    }
    if mappings is not None:
        result['matching'] = match_apis(all_apis, mappings)
        result['feasibility'] = classify_feasibility(result['matching']['missing_apis'])
    return result
