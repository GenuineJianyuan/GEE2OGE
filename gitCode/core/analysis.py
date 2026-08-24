"""Static GEE JavaScript analysis: steps, parameters, types, and API discovery."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Set


METHODS_BY_TYPE: Mapping[str, Set[str]] = {
    'ee.Image': {
        'select', 'subtract', 'add', 'multiply', 'divide', 'rename', 'clip', 'mask',
        'unmask', 'updateMask', 'where', 'eq', 'gt', 'gte', 'lt', 'lte', 'abs',
        'sqrt', 'pow', 'log', 'exp', 'min', 'max', 'reduce', 'reduceRegion',
        'normalizedDifference', 'expression', 'unitScale', 'addBands', 'toFloat',
        'toDouble', 'classify', 'sample', 'sampleRegions', 'visualize', 'convolve',
    },
    'ee.ImageCollection': {
        'filter', 'filterDate', 'filterBounds', 'map', 'select', 'first', 'limit',
        'sort', 'size', 'mean', 'median', 'min', 'max', 'sum', 'mosaic', 'toList',
    },
    'ee.FeatureCollection': {
        'filter', 'filterBounds', 'map', 'first', 'limit', 'sort', 'size', 'merge',
        'flatten', 'geometry', 'reduceColumns', 'toList',
    },
    'ee.Geometry': {
        'buffer', 'bounds', 'centroid', 'contains', 'intersects', 'distance',
        'intersection', 'union', 'difference', 'simplify', 'area', 'length',
    },
    'ee.Number': {'add', 'subtract', 'multiply', 'divide', 'abs', 'sqrt', 'pow', 'format'},
    'ee.Date': {'advance', 'difference', 'get', 'format', 'millis'},
    'ee.List': {'get', 'map', 'iterate', 'slice', 'sort', 'size', 'contains', 'flatten'},
    'ee.Dictionary': {'get', 'set', 'keys', 'values', 'contains'},
}

IMAGE_RESULT_METHODS = {
    'select', 'subtract', 'add', 'multiply', 'divide', 'rename', 'clip', 'mask',
    'unmask', 'updateMask', 'where', 'eq', 'gt', 'gte', 'lt', 'lte', 'abs', 'sqrt',
    'pow', 'log', 'exp', 'min', 'max', 'normalizedDifference', 'expression',
    'unitScale', 'addBands', 'toFloat', 'toDouble', 'convolve',
}


def split_steps(gee_code: str) -> List[Dict[str, str]]:
    """Use `//` comments as workflow step labels while preserving executable code."""
    result: List[Dict[str, str]] = []
    description: Optional[str] = None
    lines: List[str] = []

    def flush() -> None:
        nonlocal description, lines
        code = '\n'.join(lines).strip()
        if code:
            result.append({'description': description or 'Code execution', 'code': code})
        description, lines = None, []

    for line in gee_code.splitlines():
        match = re.match(r'^\s*//\s*(.*?)\s*$', line)
        if match:
            text = match.group(1)
            if not re.sub(r'[-=#!\s]', '', text):
                flush()
            else:
                flush()
                description = text
        else:
            lines.append(line)
    flush()
    return result or [{'description': 'Whole script', 'code': gee_code.strip()}]


def infer_variable_types(gee_code: str) -> Dict[str, str]:
    """Infer base GEE object types from constructors, copies, and chained calls."""
    types: Dict[str, str] = {}
    constructor = re.compile(
        r'(?:var|let|const)\s+([A-Za-z_]\w*)\s*=\s*'
        r'(ee\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\('
    )
    for variable, constructor_name in constructor.findall(gee_code):
        types[variable] = '.'.join(constructor_name.split('.')[:2])

    for _ in range(3):
        for target, source in re.findall(r'(?:var|let|const)\s+(\w+)\s*=\s+(\w+)\s*[;\n]', gee_code):
            if source in types:
                types.setdefault(target, types[source])
        for target, source, method in re.findall(
            r'(?:var|let|const)\s+(\w+)\s*=\s+(\w+)\.([A-Za-z_]\w*)\s*\(', gee_code
        ):
            if types.get(source) == 'ee.Image' and method in IMAGE_RESULT_METHODS:
                types.setdefault(target, 'ee.Image')
            elif method in {'buffer', 'bounds', 'centroid', 'intersection', 'union', 'difference', 'simplify'}:
                types.setdefault(target, 'ee.Geometry')
    return types


def extract_gee_apis(gee_code: str, variable_types: Optional[Mapping[str, str]] = None) -> List[str]:
    """Extract constructors, static calls, Map/Export calls, and typed instance methods."""
    apis = set(re.findall(r'\b(ee\.[A-Za-z_]\w*)\s*\(', gee_code))
    apis.update(re.findall(r'\b(ee\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\s*\(', gee_code))
    apis.update(re.findall(r'\b(Map\.[A-Za-z_]\w*)\s*\(', gee_code))
    apis.update(re.findall(r'\b(Export\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\(', gee_code))
    if re.search(r'\bprint\s*\(', gee_code):
        apis.add('print')
    for variable, object_type in (variable_types or infer_variable_types(gee_code)).items():
        methods = METHODS_BY_TYPE.get(object_type, set())
        for method in re.findall(rf'\b{re.escape(variable)}\.([A-Za-z_]\w*)\s*\(', gee_code):
            if method in methods:
                apis.add(f'{object_type}.{method}')
    return sorted(apis)


def extract_key_parameters(gee_code: str) -> Dict[str, Any]:
    """Extract datasets, bands, renamed indices, dates, point coordinates, and map center."""
    parameters: Dict[str, Any] = {}
    datasets = re.findall(r"ee\.Image(?:Collection)?\(['\"]([^'\"]+)['\"]\)", gee_code)
    if datasets:
        parameters['datasets'] = sorted(set(datasets))
    bands = re.findall(r"\.select\(['\"]([^'\"]+)['\"]\)", gee_code)
    if bands:
        parameters['bands'] = sorted(set(bands))
    indices = re.findall(r"\.rename\(['\"]([^'\"]+)['\"]\)", gee_code)
    if indices:
        parameters['indices'] = sorted(set(indices))
    dates = re.findall(r"['\"](\d{4}-\d{2}-\d{2})['\"]", gee_code)
    if dates:
        parameters['dates'] = sorted(set(dates))
    center = re.search(r'Map\.setCenter\(([\d.-]+),\s*([\d.-]+),\s*(\d+)\)', gee_code)
    if center:
        parameters['map_center'] = {'longitude': float(center[1]), 'latitude': float(center[2]), 'zoom': int(center[3])}
    return parameters


def analyze_gee(gee_code: str) -> Dict[str, Any]:
    """Run static analysis and return structured data for mapping and generation."""
    variable_types = infer_variable_types(gee_code)
    steps = split_steps(gee_code)
    return {
        'steps': steps,
        'variable_types': variable_types,
        'apis': extract_gee_apis(gee_code, variable_types),
        'parameters': extract_key_parameters(gee_code),
    }
