"""GEE 示例代码生成器

数据来源优先级：
1. gee.json 中 examples[order=1].code（JavaScript 官方示例）—— 删除 // 注释，只保留纯代码
2. 无 examples 时回退到根据签名/参数类型自动生成的示例代码

注释清洗策略（针对 JavaScript）：
- 删除整行 // 注释
- 删除行内 // 注释（保留 // 之前的代码）
- 删除 /* */ 块注释
- 字符串感知：不删除字符串字面量内的 //（如 URL、正则）
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# gee.json 资源路径（resource 目录位于项目根目录下）
GEE_JSON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resource', 'gee.json'
)

# 已加载的 GEE API 数据缓存（避免重复读文件）
_GEE_API_CACHE: Optional[List[Dict[str, Any]]] = None

# 示例代码最小长度阈值：处理注释后短于此值视为无效，回退到生成逻辑
MIN_CODE_LENGTH = 30


def _load_gee_apis() -> List[Dict[str, Any]]:
    """加载 gee.json 全量数据（带缓存）"""
    global _GEE_API_CACHE
    if _GEE_API_CACHE is None:
        with open(GEE_JSON_PATH, 'r', encoding='utf-8') as f:
            _GEE_API_CACHE = json.load(f)
    return _GEE_API_CACHE


# ============================================================
# JavaScript 注释清洗（字符串感知）
# ============================================================

def _strip_js_comments(code: str) -> str:
    """删除 JavaScript 代码中的注释，保留纯代码

    处理规则：
    - 删除 // 行注释（整行和行内），但保留字符串字面量内的 //
    - 删除 /* ... */ 块注释
    - 删除处理后的纯空行（连续空行压缩为一个）

    Args:
        code: 原始 JavaScript 代码

    Returns:
        str: 删除注释后的纯代码
    """
    if not code:
        return ''

    result = []
    i = 0
    n = len(code)
    # 字符串状态标记
    in_single_quote = False   # 单引号字符串
    in_double_quote = False   # 双引号字符串
    in_template = False       # 反引号模板字符串

    while i < n:
        ch = code[i]
        nxt = code[i + 1] if i + 1 < n else ''

        # 处理转义字符（在字符串内时跳过下一个字符）
        if ch == '\\' and (in_single_quote or in_double_quote or in_template):
            result.append(ch)
            if i + 1 < n:
                result.append(code[i + 1])
                i += 2
                continue
            i += 1
            continue

        # 字符串边界检测
        if ch == "'" and not in_double_quote and not in_template:
            in_single_quote = not in_single_quote
            result.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single_quote and not in_template:
            in_double_quote = not in_double_quote
            result.append(ch)
            i += 1
            continue
        if ch == '`' and not in_single_quote and not in_double_quote:
            in_template = not in_template
            result.append(ch)
            i += 1
            continue

        # 仅在不在字符串内时处理注释
        if not in_single_quote and not in_double_quote and not in_template:
            # 块注释 /* ... */
            if ch == '/' and nxt == '*':
                # 找到结束 */
                end = code.find('*/', i + 2)
                if end == -1:
                    # 未闭合的块注释，删除到末尾
                    i = n
                else:
                    i = end + 2
                continue
            # 行注释 //
            if ch == '/' and nxt == '/':
                # 跳过到行尾
                end = code.find('\n', i)
                if end == -1:
                    i = n
                else:
                    i = end  # 保留换行符，下一轮处理
                continue

        result.append(ch)
        i += 1

    cleaned = ''.join(result)
    # 压缩连续空行为一个，并去除每行尾部空白
    lines = [line.rstrip() for line in cleaned.split('\n')]
    # 删除纯空行（连续空行压缩）
    compressed = []
    prev_blank = False
    for line in lines:
        if line.strip() == '':
            if not prev_blank:
                compressed.append('')
            prev_blank = True
        else:
            compressed.append(line)
            prev_blank = False
    # 去除首尾空行
    while compressed and compressed[0] == '':
        compressed.pop(0)
    while compressed and compressed[-1] == '':
        compressed.pop()
    return '\n'.join(compressed)


def _extract_example_code(api: Dict[str, Any]) -> Optional[str]:
    """从 examples 字段提取并清洗 JavaScript 示例代码

    提取策略：
    - 优先取 order=1 的 code（JavaScript 官方示例）
    - 删除 // 和 /* */ 注释
    - 处理后长度 < MIN_CODE_LENGTH 视为无效，返回 None

    Args:
        api: gee.json 中的 API 元数据对象

    Returns:
        str or None: 清洗后的纯代码，无可用示例返回 None
    """
    examples = api.get('examples')
    if not examples or not isinstance(examples, list):
        return None

    # 收集所有 code，按 order 排序，优先 order=1
    candidates = []
    for ex in examples:
        if not isinstance(ex, dict):
            continue
        code = ex.get('code', '')
        order = ex.get('order', 99)
        if code and len(code) >= MIN_CODE_LENGTH:
            candidates.append((order, code))

    # 按 order 升序，优先取 order=1（JavaScript）
    candidates.sort(key=lambda x: x[0])

    for order, code in candidates:
        cleaned = _strip_js_comments(code)
        # 清洗后仍需足够长
        if len(cleaned.strip()) >= MIN_CODE_LENGTH:
            return cleaned

    return None


# ============================================================
# 回退方案：根据签名自动生成示例代码
# ============================================================

# 简单类型默认值（纯字面量）
_TYPE_DEFAULTS_LITERAL: Dict[str, str] = {
    'Number': '10',
    'Float': '1.5',
    'Integer': '1',
    'Long': '1',
    'String': '"value"',
    'Boolean': 'true',
    'Object': '{}',
    'List': '[1, 2, 3]',
    'Dictionary': '{"key": "value"}',
    'Projection': 'ee.Projection("EPSG:4326")',
}

# 复杂类型默认值（需要 ee.Xxx() 构造）
_TYPE_DEFAULTS_COMPLEX: Dict[str, str] = {
    'Image': 'ee.Image("COPERNICUS/S2_SR/20210101")',
    'ImageCollection': 'ee.ImageCollection("LANDSAT/LC08/C02/T1_SR")',
    'Feature': 'ee.Feature(ee.Geometry.Point([116.0, 39.0]))',
    'FeatureCollection': 'ee.FeatureCollection(ee.Geometry.Point([116.0, 39.0]))',
    'Geometry': 'ee.Geometry.Point([116.0, 39.0])',
    'Date': 'ee.Date("2021-01-01")',
    'DateRange': 'ee.DateRange("2021-01-01", "2021-12-31")',
    'Filter': 'ee.Filter.eq("name", "value")',
    'Kernel': 'ee.Kernel.circle(3)',
    'Reducer': 'ee.Reducer.sum()',
    'Array': 'ee.Array([[1, 2], [3, 4]])',
    'Classifier': 'ee.Classifier.smileCart()',
    'Clusterer': 'ee.Clusterer.wekaKMeans(2)',
    'ConfusionMatrix': 'ee.ConfusionMatrix(ee.Array([[10, 2], [3, 15]]))',
    'PixelType': 'ee.PixelType.int16()',
    'ErrorMargin': 'ee.ErrorMargin(0.1)',
    'Terrain': 'ee.Terrain',
    'Blob': 'ee.Blob("gs://bucket/file.txt")',
    'Model': 'ee.Model.fromFrame(ee.Feature(ee.Geometry.Point([0, 0])))',
}

# 实例变量的类型推断（用于为方法生成宿主实例）
_CLASS_INSTANCE_BUILDERS: Dict[str, str] = {
    'ee.Image': 'ee.Image("COPERNICUS/S2_SR/20210101")',
    'ee.ImageCollection': 'ee.ImageCollection("LANDSAT/LC08/C02/T1_SR")',
    'ee.Feature': 'ee.Feature(ee.Geometry.Point([116.0, 39.0]))',
    'ee.FeatureCollection': 'ee.FeatureCollection(ee.Geometry.Point([116.0, 39.0]))',
    'ee.Geometry': 'ee.Geometry.Point([116.0, 39.0])',
    'ee.Number': 'ee.Number(10)',
    'ee.String': 'ee.String("value")',
    'ee.List': 'ee.List([1, 2, 3])',
    'ee.Dictionary': 'ee.Dictionary({"key": "value"})',
    'ee.Date': 'ee.Date("2021-01-01")',
    'ee.DateRange': 'ee.DateRange("2021-01-01", "2021-12-31")',
    'ee.Filter': 'ee.Filter.eq("name", "value")',
    'ee.Kernel': 'ee.Kernel.circle(3)',
    'ee.Reducer': 'ee.Reducer.sum()',
    'ee.Array': 'ee.Array([[1, 2], [3, 4]])',
    'ee.Classifier': 'ee.Classifier.smileCart()',
    'ee.Clusterer': 'ee.Clusterer.wekaKMeans(2)',
    'ee.Projection': 'ee.Projection("EPSG:4326")',
    'ee.ConfusionMatrix': 'ee.ConfusionMatrix(ee.Array([[10, 2], [3, 15]]))',
    'ee.PixelType': 'ee.PixelType.int16()',
}


def _normalize_type(type_str: str) -> str:
    """规范化类型字符串，提取主类型名

    处理 "Float, default: 1" / "List[Number]" / "Date|Number|String" 等格式。

    Args:
        type_str: 原始类型字符串

    Returns:
        str: 规范化后的主类型名
    """
    if not type_str:
        return 'Object'
    raw = type_str.split(',')[0].strip()
    if '|' in raw:
        raw = raw.split('|')[0].strip()
    if '[' in raw:
        raw = raw.split('[')[0].strip()
    if raw.startswith('this:'):
        raw = raw.split(':', 1)[1].strip()
    return raw


def _gen_arg_value(type_str: str, arg_name: str = '') -> str:
    """根据参数类型生成默认值表达式"""
    norm = _normalize_type(type_str)
    name_lower = arg_name.lower()
    if name_lower in ('coords', 'coordinates', 'coord'):
        return '[116.0, 39.0]'
    if name_lower in ('start', 'startdate', 'begindate'):
        return '"2021-01-01"'
    if name_lower in ('end', 'enddate'):
        return '"2021-12-31"'
    if name_lower == 'radius':
        return '3'
    if name_lower == 'threshold':
        return '1.0'
    if name_lower == 'sigma':
        return '1'
    if name_lower in ('bandnames', 'bands'):
        return '["B4", "B8"]'
    if name_lower in ('name', 'key', 'property'):
        return '"value"'
    if name_lower == 'value':
        return '1'
    if norm in _TYPE_DEFAULTS_LITERAL:
        return _TYPE_DEFAULTS_LITERAL[norm]
    if norm in _TYPE_DEFAULTS_COMPLEX:
        return _TYPE_DEFAULTS_COMPLEX[norm]
    if norm == 'List':
        return '[1, 2, 3]'
    if norm.startswith('Geometry.'):
        return 'ee.Geometry.Point([116.0, 39.0])'
    return 'null'


def _result_var_name(returns: str) -> str:
    """根据返回类型生成结果变量名"""
    ret = _normalize_type(returns).lower()
    name_map = {
        'image': 'image', 'imagecollection': 'collection', 'feature': 'feature',
        'featurecollection': 'fc', 'geometry': 'geometry', 'geometry.point': 'point',
        'geometry.polygon': 'polygon', 'number': 'num', 'string': 'str',
        'list': 'list', 'dictionary': 'dict', 'date': 'date', 'daterange': 'dateRange',
        'filter': 'filter', 'kernel': 'kernel', 'reducer': 'reducer', 'array': 'array',
        'classifier': 'classifier', 'clusterer': 'clusterer', 'projection': 'projection',
        'boolean': 'flag', 'object': 'result', 'void': 'result', 'computedobject': 'result',
    }
    return name_map.get(ret, 'result')


def _gen_sample_code_fallback(api: Dict[str, Any]) -> str:
    """回退方案：根据 API 签名自动生成示例代码（无 examples 时使用）

    Args:
        api: gee.json 中的 API 元数据对象

    Returns:
        str: 生成的纯代码示例
    """
    full_name = api.get('fullName', '')
    usage = api.get('usage', '')
    args = api.get('arguments', []) or []
    returns = api.get('returns', '')
    class_name = api.get('className', '')

    is_ctor_or_static = usage.strip().startswith('ee.')
    explicit_args = []
    implicit_type = None
    for arg in args:
        arg_name = arg.get('name', '')
        arg_type = arg.get('type', '')
        if arg_name.startswith('this:'):
            implicit_type = _normalize_type(arg_type)
        else:
            explicit_args.append((arg_name, arg_type))

    if is_ctor_or_static:
        arg_values = [_gen_arg_value(t, n) for n, t in explicit_args]
        call_expr = f'{full_name}({", ".join(arg_values)})'
        var_name = _result_var_name(returns)
        return f'var {var_name} = {call_expr};'
    else:
        host_expr = _CLASS_INSTANCE_BUILDERS.get(class_name)
        if not host_expr and implicit_type:
            host_expr = _CLASS_INSTANCE_BUILDERS.get(f'ee.{implicit_type}')
        if not host_expr and implicit_type:
            host_expr = _CLASS_INSTANCE_BUILDERS.get(implicit_type)
        if not host_expr:
            host_expr = 'null'
        var_name = _result_var_name(returns)
        method_name = full_name.split('.')[-1] if '.' in full_name else full_name
        arg_values = [_gen_arg_value(t, n) for n, t in explicit_args]
        return (f'var input = {host_expr};\n'
                f'var {var_name} = input.{method_name}({", ".join(arg_values)});')


def _gen_sample_code(api: Dict[str, Any]) -> str:
    """为单个 GEE API 生成纯代码示例

    优先级：
    1. examples[order=1].code（JavaScript 官方示例，删除 // 注释）
    2. 回退到根据签名自动生成

    Args:
        api: gee.json 中的 API 元数据对象

    Returns:
        str: 纯代码示例（无注释）
    """
    # 优先从 examples 提取
    example_code = _extract_example_code(api)
    if example_code:
        return example_code
    # 回退到生成
    return _gen_sample_code_fallback(api)


# ============================================================
# 对外查询接口
# ============================================================

def get_all_samples() -> List[Dict[str, Any]]:
    """获取全部 GEE API 的示例代码列表

    Returns:
        List[Dict]: 每项包含 fullName/className/usage/returns/samplecode/source
        source 标记示例来源：'example'（官方示例）或 'generated'（自动生成）
    """
    apis = _load_gee_apis()
    result = []
    for api in apis:
        full_name = api.get('fullName', '')
        if not full_name:
            continue
        example_code = _extract_example_code(api)
        source = 'example' if example_code else 'generated'
        sample = example_code if example_code else _gen_sample_code_fallback(api)
        result.append({
            'fullName': full_name,
            'className': api.get('className', ''),
            'methodName': api.get('methodName', ''),
            'usage': api.get('usage', ''),
            'returns': api.get('returns', ''),
            'description': api.get('description', ''),
            'samplecode': sample,
            'source': source,
        })
    return result


def get_sample_by_name(full_name: str) -> Optional[Dict[str, Any]]:
    """根据 GEE API 全名获取单个示例代码详情

    Args:
        full_name: GEE API 全名（如 ee.Image.abs）

    Returns:
        Dict or None: 示例代码详情，未找到返回 None
    """
    apis = _load_gee_apis()
    for api in apis:
        if api.get('fullName') == full_name:
            example_code = _extract_example_code(api)
            source = 'example' if example_code else 'generated'
            sample = example_code if example_code else _gen_sample_code_fallback(api)
            return {
                'fullName': api.get('fullName', ''),
                'className': api.get('className', ''),
                'methodName': api.get('methodName', ''),
                'usage': api.get('usage', ''),
                'returns': api.get('returns', ''),
                'description': api.get('description', ''),
                'arguments': api.get('arguments', []),
                'samplecode': sample,
                'source': source,
            }
    return None


if __name__ == '__main__':
    # 自测：打印几个示例
    test_names = [
        'ee.Image.abs',
        'ee.Image.normalizedDifference',
        'ee.Geometry.Point',
        'ee.Filter.date',
        'ee.Number.add',
        'ee.Kernel.circle',
        'ee.Algorithms.CannyEdgeDetector',
    ]
    for name in test_names:
        sample = get_sample_by_name(name)
        if sample:
            print(f'=== {name} (source={sample["source"]}) ===')
            print(sample['samplecode'])
            print()
