"""GEE JavaScript 静态分析：步骤拆分、参数提取、类型推断与 API 识别。

从主项目 ``case_study_pipeline.py`` 中提取核心算法，去除 Flask、数据库、
LLM 等应用层依赖，保留纯规则解析逻辑。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple


# ============================================================
# 各 GEE 类型的常用方法集合（用于变量.方法() 形式的 API 识别）
# ============================================================

IMAGE_METHODS: Set[str] = {
    'select', 'subtract', 'add', 'multiply', 'divide', 'rename', 'clip', 'mask',
    'unmask', 'updateMask', 'where', 'and', 'or', 'not', 'eq', 'gt', 'gte', 'lt',
    'lte', 'abs', 'sqrt', 'pow', 'log', 'exp', 'cos', 'sin', 'tan', 'min', 'max',
    'sum', 'mean', 'median', 'count', 'reduce', 'reduceRegion', 'reduceRegions',
    'reduceNeighborhood', 'neighborhoodToBands',
    'sample', 'sampleRegions', 'classify', 'visualize', 'unitScale',
    'normalizedDifference', 'expression', 'bandNames', 'bandTypes', 'set', 'get',
    'toArray', 'toDouble', 'toFloat', 'toInt', 'toInt32', 'addBands',
    'selectBands', 'resample', 'reduceResolution', 'reproject', 'cast', 'unmix',
    'trim', 'convolve', 'focalMean', 'focalMax', 'focalMin', 'focalMode',
    'focal_mean', 'focal_max', 'focal_min', 'gradient', 'kernel',
    'bitwiseAnd', 'bitwiseOr', 'bitwiseXor', 'leftShift', 'rightShift',
    'projection', 'geometry',
}

FEATURE_METHODS: Set[str] = {
    'set', 'get', 'geometry', 'area', 'length', 'perimeter', 'buffer', 'bounds',
    'centroid', 'contains', 'intersects', 'withinDistance', 'distance',
    'intersection', 'union', 'difference', 'symmetricDifference', 'simplify',
    'transform',
}

COLLECTION_METHODS: Set[str] = {
    'filter', 'filterDate', 'filterBounds', 'filterMetadata', 'map', 'select',
    'first', 'limit', 'sort', 'size', 'getInfo', 'geometry', 'union',
    'aggregate_array', 'aggregate_stats', 'aggregate_count', 'aggregate_max',
    'aggregate_min', 'aggregate_mean', 'aggregate_sum', 'aggregate_product',
    'reduceToImage', 'reduceToVectors', 'randomColumn', 'style', 'merge',
    'flatten', 'distinct', 'toList', 'mosaic', 'mean', 'median', 'max', 'min',
    'sum', 'count', 'reduceColumns',
}

GEOMETRY_METHODS: Set[str] = FEATURE_METHODS | {
    'coordinates', 'geodesic', 'srid', 'type',
}

NUMBER_METHODS: Set[str] = {
    'add', 'subtract', 'multiply', 'divide', 'abs', 'sqrt', 'pow', 'round',
    'floor', 'ceil', 'toInt', 'toFloat', 'format', 'lt', 'lte', 'gt', 'gte',
    'eq', 'neq', 'and', 'or', 'not', 'min', 'max', 'log', 'exp', 'sin', 'cos', 'tan',
}

STRING_METHODS: Set[str] = {
    'cat', 'slice', 'indexOf', 'toUpperCase', 'toLowerCase', 'replace', 'split',
    'length', 'regexpExtract',
}

DATE_METHODS: Set[str] = {
    'advance', 'difference', 'get', 'format', 'millis', 'getRange', 'getRelative',
    'unitDifference',
}

LIST_METHODS: Set[str] = {
    'get', 'map', 'iterate', 'slice', 'reverse', 'sort', 'size', 'contains',
    'indexOf', 'add', 'remove', 'set', 'repeat', 'flatten', 'cat', 'reduce',
    'sort_combined',
}

DICTIONARY_METHODS: Set[str] = {
    'get', 'set', 'keys', 'values', 'size', 'contains', 'rename', 'select',
}

METHODS_BY_TYPE: Mapping[str, Set[str]] = {
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


# ============================================================
# 静态方法 / 链式调用的返回类型映射（用于变量类型推断）
# ============================================================

STATIC_METHOD_RETURN_TYPES: Dict[str, str] = {
    # ee.Terrain 系列
    'ee.Terrain.slope': 'ee.Image',
    'ee.Terrain.aspect': 'ee.Image',
    'ee.Terrain.hillshade': 'ee.Image',
    'ee.Terrain.hillShadow': 'ee.Image',
    'ee.Terrain.flowAccumulation': 'ee.Image',
    'ee.Terrain.roughness': 'ee.Image',
    # ee.Algorithms 系列
    'ee.Algorithms.CannyEdgeDetector': 'ee.Image',
    'ee.Algorithms.HoughTransformVectors': 'ee.Image',
    'ee.Algorithms.If': 'ee.Image',
    # ee.Image 静态方法
    'ee.Image.constant': 'ee.Image',
    'ee.Image.rgb': 'ee.Image',
    'ee.Image.cat': 'ee.Image',
    # ee.ImageCollection 归约方法
    'ee.ImageCollection.closest': 'ee.Image',
    'ee.ImageCollection.first': 'ee.Image',
    'ee.ImageCollection.mosaic': 'ee.Image',
    'ee.ImageCollection.mean': 'ee.Image',
    'ee.ImageCollection.median': 'ee.Image',
    'ee.ImageCollection.max': 'ee.Image',
    'ee.ImageCollection.min': 'ee.Image',
    'ee.ImageCollection.sum': 'ee.Image',
}

METHOD_RETURN_TYPES: Dict[str, str] = {
    # ee.Image 方法返回 ee.Image
    'select': 'ee.Image', 'subtract': 'ee.Image', 'add': 'ee.Image',
    'multiply': 'ee.Image', 'divide': 'ee.Image', 'rename': 'ee.Image',
    'clip': 'ee.Image', 'mask': 'ee.Image', 'unmask': 'ee.Image',
    'updateMask': 'ee.Image', 'where': 'ee.Image', 'and': 'ee.Image',
    'or': 'ee.Image', 'not': 'ee.Image', 'eq': 'ee.Image',
    'gt': 'ee.Image', 'gte': 'ee.Image', 'lt': 'ee.Image',
    'lte': 'ee.Image', 'abs': 'ee.Image', 'sqrt': 'ee.Image',
    'pow': 'ee.Image', 'log': 'ee.Image', 'exp': 'ee.Image',
    'cos': 'ee.Image', 'sin': 'ee.Image', 'tan': 'ee.Image',
    'min': 'ee.Image', 'max': 'ee.Image', 'unitScale': 'ee.Image',
    'normalizedDifference': 'ee.Image', 'expression': 'ee.Image',
    'addBands': 'ee.Image', 'selectBands': 'ee.Image',
    'cast': 'ee.Image', 'toDouble': 'ee.Image', 'toFloat': 'ee.Image',
    'toInt': 'ee.Image', 'toInt32': 'ee.Image', 'unmix': 'ee.Image',
    'focal_mean': 'ee.Image', 'focal_max': 'ee.Image',
    'focal_min': 'ee.Image', 'resample': 'ee.Image',
    'reproject': 'ee.Image', 'convolve': 'ee.Image',
    'reduceNeighborhood': 'ee.Image', 'neighborhoodToBands': 'ee.Image',
    'focalMean': 'ee.Image', 'focalMax': 'ee.Image',
    'focalMin': 'ee.Image', 'focalMode': 'ee.Image',
    'reduce': 'ee.Image', 'mean': 'ee.Image',
    'median': 'ee.Image', 'sum': 'ee.Image', 'count': 'ee.Image',
    'trim': 'ee.Image', 'visualize': 'ee.Image', 'gradient': 'ee.Image',
    # ee.ImageCollection 归约方法
    'mosaic': 'ee.Image', 'first': 'ee.Image',
    'reduceColumns': 'ee.Dictionary',
    # ee.Geometry 方法返回 ee.Geometry
    'buffer': 'ee.Geometry', 'bounds': 'ee.Geometry',
    'centroid': 'ee.Geometry', 'simplify': 'ee.Geometry',
    'transform': 'ee.Geometry', 'intersection': 'ee.Geometry',
    'union': 'ee.Geometry', 'difference': 'ee.Geometry',
    'symmetricDifference': 'ee.Geometry',
    # ee.Feature 方法
    'geometry': 'ee.Geometry',
}


# ============================================================
# 步骤拆分算法
# ============================================================

def _is_pure_separator(text: str) -> bool:
    """判断注释文本是否为纯分隔符（如 "---", "====", "!!!" 等）。

    Args:
        text: 注释文本内容

    Returns:
        bool: 是纯分隔符返回 True
    """
    return not re.sub(r'[-=#!\s]', '', text)


def split_steps(gee_code: str) -> List[Dict[str, str]]:
    """按单行注释分割 GEE 脚本为有序的工作流步骤。

    以 ``// 步骤描述`` 形式的注释行作为步骤边界，纯分隔符注释
    （如 ``// ----``）仅触发步骤刷新而不产生新的步骤描述。
    无注释时将整个脚本作为单个步骤返回。

    Args:
        gee_code: 原始 GEE JavaScript 代码

    Returns:
        List[Dict]: 步骤列表，每个元素包含 ``description`` 和 ``code``
    """
    result: List[Dict[str, str]] = []
    current_description: Optional[str] = None
    current_lines: List[str] = []

    def _flush() -> None:
        """将当前累积的代码行作为一个步骤保存。"""
        nonlocal current_description, current_lines
        code = '\n'.join(current_lines).strip()
        if code:
            result.append({
                'description': current_description or 'Code execution',
                'code': code,
            })
        current_description, current_lines = None, []

    for line in gee_code.splitlines():
        comment_match = re.match(r'^\s*//\s*(.+?)\s*$', line)
        if comment_match:
            comment_text = comment_match.group(1).strip()
            if _is_pure_separator(comment_text):
                _flush()
            else:
                _flush()
                # 清理连续的分隔符字符（如 "=== Step 1 ===" → "Step 1"）
                cleaned = re.sub(r'[-=#!]{2,}', '', comment_text).strip()
                current_description = cleaned or 'Code execution'
        else:
            current_lines.append(line)
    _flush()

    return result or [{'description': 'Whole script', 'code': gee_code.strip()}]


def verify_step_coverage(gee_code: str, steps: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """校验步骤拆分的代码行覆盖率，将遗漏的代码行补到最后一个步骤。

    比较原始代码（去注释去空行）与各步骤中的代码行，确保不遗漏任何可执行代码。

    Args:
        gee_code: 原始 GEE 代码
        steps: 已拆分的步骤列表（会被就地修改）

    Returns:
        List[Dict]: 补全后的步骤列表
    """
    if not steps:
        return steps

    # 提取原始代码的所有非注释、非空行（归一化后用于比较）
    original_lines: List[str] = []
    for line in gee_code.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('//'):
            continue
        if stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('*/'):
            continue
        original_lines.append(stripped)

    # 提取步骤中的所有代码行（归一化后）
    step_lines_set: Set[str] = set()
    for step in steps:
        code = step.get('code', '')
        for line in code.splitlines():
            stripped = line.strip()
            if stripped:
                step_lines_set.add(stripped)

    # 找出遗漏的行
    missing_lines = [line for line in original_lines if line not in step_lines_set]

    # 如果有遗漏，追加到最后一个步骤
    if missing_lines:
        last_step = steps[-1]
        existing_code = last_step.get('code', '')
        supplement_code = '\n'.join(missing_lines)
        if existing_code:
            last_step['code'] = existing_code + '\n' + supplement_code
        else:
            last_step['code'] = supplement_code

    return steps


# ============================================================
# 变量类型推断算法
# ============================================================

def infer_variable_types(gee_code: str) -> Dict[str, str]:
    """从 GEE 代码中推断变量的 GEE 对象类型。

    通过以下策略推断变量类型：
    1. 构造函数赋值：``var x = ee.Image(...)`` → x 是 ee.Image
    2. 静态方法调用：``var x = ee.Terrain.slope(...)`` → x 是 ee.Image
    3. 变量间赋值：``var y = x`` → y 继承 x 的类型
    4. 方法调用结果：``var z = x.select(...)`` → 根据方法返回类型推断

    Args:
        gee_code: GEE JavaScript 代码

    Returns:
        Dict[str, str]: 变量名到 GEE 类型的映射，如 ``{'winterImage': 'ee.Image'}``
    """
    variable_types: Dict[str, str] = {}

    # 1. 匹配构造函数和静态方法调用赋值
    # 如 var x = ee.Image(...), var y = ee.Geometry.LineString(...)
    #    var z = ee.Terrain.slope(...)
    var_decl_pattern = re.compile(
        r'(?:var|let|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
        r'(ee\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\('
    )
    for match in var_decl_pattern.finditer(gee_code):
        var_name = match.group(1)
        gee_api = match.group(2)

        # 检查是否是已知返回类型的静态方法调用
        if gee_api in STATIC_METHOD_RETURN_TYPES:
            variable_types[var_name] = STATIC_METHOD_RETURN_TYPES[gee_api]
            continue

        # 提取基础类名（前两级），如 ee.Geometry.LineString → ee.Geometry
        parts = gee_api.split('.')
        if len(parts) >= 2:
            base_class = f'{parts[0]}.{parts[1]}'
        else:
            base_class = gee_api
        variable_types[var_name] = base_class

    # 2~4. 多轮迭代处理变量赋值传播和方法返回类型
    # 多轮迭代是因为可能存在链式依赖：a = ee.Image(); b = a.select(); c = b.add(...)
    for _ in range(3):
        # 变量间赋值传播：var y = x
        var_assign_pattern = re.compile(
            r'(?:var|let|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
            r'([A-Za-z_][A-Za-z0-9_]*)\s*[;\n]'
        )
        for match in var_assign_pattern.finditer(gee_code):
            target_var = match.group(1)
            source_var = match.group(2)
            if source_var in variable_types and target_var not in variable_types:
                variable_types[target_var] = variable_types[source_var]

        # 方法调用返回类型推断：var z = x.method(...)
        var_op_pattern = re.compile(
            r'(?:var|let|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
            r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\('
        )
        for match in var_op_pattern.finditer(gee_code):
            target_var = match.group(1)
            source_var = match.group(2)
            method_name = match.group(3)

            if target_var in variable_types:
                continue  # 已推断过，跳过

            if source_var not in variable_types:
                continue  # 源变量类型未知，无法推断

            source_type = variable_types[source_var]
            return_type = METHOD_RETURN_TYPES.get(method_name)

            if return_type:
                variable_types[target_var] = return_type
            elif source_type == 'ee.Image' and method_name in IMAGE_METHODS:
                # 默认 Image 上的大多数方法仍返回 Image
                variable_types[target_var] = 'ee.Image'

    return variable_types


# ============================================================
# GEE API 提取算法
# ============================================================

def _extract_chain_methods(code: str, start_pos: int) -> List[str]:
    """从代码的指定位置开始，提取链式调用中后续的所有方法名。

    使用括号计数法处理嵌套参数，准确识别每个链式方法的边界。

    Args:
        code: 完整代码字符串
        start_pos: 第一个方法调用的左括号之后的位置

    Returns:
        List[str]: 链式调用中后续方法名的列表
    """
    methods: List[str] = []
    pos = start_pos
    depth = 1  # 已经有一个左括号

    # 跳过第一个方法的参数（括号计数）
    while pos < len(code) and depth > 0:
        if code[pos] == '(':
            depth += 1
        elif code[pos] == ')':
            depth -= 1
        pos += 1

    # 跳过空白字符
    while pos < len(code) and code[pos] in ' \t\n\r':
        pos += 1

    # 继续提取后续的 .method( 调用
    while pos < len(code) and code[pos] == '.':
        # 提取方法名
        method_match = re.match(r'\.([A-Za-z_][A-Za-z0-9_]*)\s*\(', code[pos:])
        if not method_match:
            break
        method_name = method_match.group(1)
        methods.append(method_name)

        # 跳过这个方法的参数（括号计数）
        pos += method_match.end()  # 移到左括号之后
        depth = 1
        while pos < len(code) and depth > 0:
            if code[pos] == '(':
                depth += 1
            elif code[pos] == ')':
                depth -= 1
            pos += 1

        # 跳过空白字符
        while pos < len(code) and code[pos] in ' \t\n\r':
            pos += 1

    return methods


def extract_gee_apis(
    gee_code: str,
    variable_types: Optional[Mapping[str, str]] = None,
) -> List[str]:
    """从 GEE 代码中提取所有 GEE API 调用（保留调用顺序和重复）。

    识别以下形式的 API 调用：
    1. 构造函数：``ee.Image(...)``
    2. 静态/多级方法：``ee.Algorithms.CannyEdgeDetector(...)``
    3. Map 方法：``Map.addLayer(...)``
    4. Export 方法：``Export.image.toDrive(...)``
    5. print 函数
    6. 变量方法调用：``image.select(...)``（基于变量类型表识别）
    7. 链式调用中的方法（括号计数法准确提取）

    Args:
        gee_code: GEE JavaScript 代码
        variable_types: 变量类型字典，不传则自动推断

    Returns:
        List[str]: GEE API 全名列表（按调用顺序，保留重复）
    """
    apis: List[str] = []

    # 1. 匹配 ee.XXX( 形式的构造函数调用
    ctor_pattern = re.compile(r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*)\s*\(')
    for match in ctor_pattern.finditer(gee_code):
        apis.append(match.group(1))

    # 2. 匹配 ee.XXX.yyy( 形式的多级直接调用
    api_pattern = re.compile(
        r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\s*\('
    )
    for match in api_pattern.finditer(gee_code):
        apis.append(match.group(1))

    # 3. 匹配 Map.xxx( 形式
    map_pattern = re.compile(r'\b(Map\.[A-Za-z_][A-Za-z0-9_]*)\s*\(')
    for match in map_pattern.finditer(gee_code):
        apis.append(match.group(1))

    # 4. 匹配 Export.xxx( 形式
    export_pattern = re.compile(
        r'\b(Export\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\('
    )
    for match in export_pattern.finditer(gee_code):
        apis.append(match.group(1))

    # 5. 匹配 print( 形式
    if re.search(r'\bprint\s*\(', gee_code):
        apis.append('print')

    # 6 & 7. 使用变量类型表，识别变量.方法( 形式及链式调用
    var_types = variable_types if variable_types is not None else infer_variable_types(gee_code)

    for var_name, gee_class in var_types.items():
        allowed_methods = METHODS_BY_TYPE.get(gee_class, set())
        if not allowed_methods:
            continue

        # 单次调用：var.method(
        var_call_pattern = re.compile(
            rf'\b{re.escape(var_name)}\.([A-Za-z_][A-Za-z0-9_]*)\s*\('
        )
        for match in var_call_pattern.finditer(gee_code):
            method = match.group(1)
            if method in allowed_methods:
                apis.append(f'{gee_class}.{method}')

        # 链式调用：var.method1(...).method2(...).method3(...)
        # 第一个方法已被上面匹配，这里提取链式调用中从第二个开始的方法
        chain_start_pattern = re.compile(
            rf'\b{re.escape(var_name)}\.[A-Za-z_][A-Za-z0-9_]*\s*\('
        )
        for sm in chain_start_pattern.finditer(gee_code):
            chain_methods = _extract_chain_methods(gee_code, sm.end())
            for method in chain_methods:
                if method in allowed_methods:
                    apis.append(f'{gee_class}.{method}')

    return apis


# ============================================================
# 关键参数提取算法
# ============================================================

def extract_key_parameters(gee_code: str) -> Dict[str, Any]:
    """从 GEE 脚本中提取迁移相关的关键参数。

    提取内容包括：
    - 数据集 ID（Image / ImageCollection 构造参数）
    - 波段名（select 调用参数）
    - 指数名（rename 调用参数）
    - 日期（YYYY-MM-DD 格式字符串）
    - 地图中心点（Map.setCenter 参数）
    - 几何点坐标（ee.Geometry.Point 参数）

    Args:
        gee_code: GEE JavaScript 代码

    Returns:
        Dict[str, Any]: 参数字典
    """
    params: Dict[str, Any] = {}

    # 数据集 ID
    datasets = re.findall(r"ee\.Image(?:Collection)?\(['\"]([^'\"]+)['\"]\)", gee_code)
    if datasets:
        params['datasets'] = sorted(set(datasets))

    # 波段名
    bands = re.findall(r"\.select\(['\"]([^'\"]+)['\"]\)", gee_code)
    if bands:
        params['bands'] = sorted(set(bands))

    # 指数 / 重命名后的名称
    indices = re.findall(r"\.rename\(['\"]([^'\"]+)['\"]\)", gee_code)
    if indices:
        params['indices'] = sorted(set(indices))

    # 日期
    dates = re.findall(r"['\"](\d{4}-\d{2}-\d{2})['\"]", gee_code)
    if dates:
        params['dates'] = sorted(set(dates))

    # 地图中心点
    center = re.search(
        r'Map\.setCenter\(([\d.\-]+),\s*([\d.\-]+),\s*(\d+)\)', gee_code
    )
    if center:
        params['map_center'] = {
            'longitude': float(center.group(1)),
            'latitude': float(center.group(2)),
            'zoom': int(center.group(3)),
        }

    # 几何点坐标
    points = re.findall(
        r'ee\.Geometry\.Point\(\[([\d.\-]+),\s*([\d.\-]+)\]\)', gee_code
    )
    if points:
        params['geometry_points'] = [
            {'longitude': float(x), 'latitude': float(y)} for x, y in points
        ]

    return params


# ============================================================
# 综合分析入口
# ============================================================

def analyze_gee(gee_code: str) -> Dict[str, Any]:
    """对 GEE 代码执行完整的静态分析。

    整合步骤拆分、变量类型推断、API 提取和关键参数提取。

    Args:
        gee_code: GEE JavaScript 代码

    Returns:
        Dict[str, Any]: 分析结果，包含 steps, variable_types, apis, parameters
    """
    variable_types = infer_variable_types(gee_code)
    steps = split_steps(gee_code)
    steps = verify_step_coverage(gee_code, steps)
    apis = extract_gee_apis(gee_code, variable_types)
    parameters = extract_key_parameters(gee_code)

    return {
        'steps': steps,
        'variable_types': variable_types,
        'apis': apis,
        'parameters': parameters,
    }
