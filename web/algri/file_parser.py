"""CSV/JSON 代码条目解析：只负责文件结构和代码字段提取。"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, Iterable, List, Optional


CODE_KEYS = {
    'gee', 'gee_code', 'geeCode', 'javascript', 'js', 'code_gee',
    'oge', 'oge_code', 'ogeCode', 'python', 'py', 'code_oge', 'code', 'script',
}


def _is_code(value: Any) -> bool:
    if not isinstance(value, str) or len(value.strip()) < 8:
        return False
    text = value.lower()
    return any(token in text for token in ('ee.', 'oge.', 'getprocess', 'import oge', 'map.', 'var ')) or '\n' in value


def _flatten_json(value: Any, path: str = '') -> Iterable[Dict[str, Any]]:
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from _flatten_json(item, f'{path}[{index}]')
    elif isinstance(value, dict):
        yield {'path': path or '$', 'value': value, 'keys': sorted(value.keys())}
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                yield from _flatten_json(item, f'{path}.{key}' if path else key)


def _detect_codes(record: Dict[str, Any]) -> Dict[str, str]:
    codes: Dict[str, str] = {}
    for key, value in record.items():
        if not isinstance(value, str) or not _is_code(value):
            continue
        lower = key.lower()
        if 'gee' in lower or 'javascript' in lower or lower in {'js'}:
            codes['gee'] = value
        elif 'oge' in lower or 'python' in lower or lower in {'py'}:
            codes['oge'] = value
        elif lower in {'code', 'script'}:
            codes.setdefault('gee' if ('ee.' in value or 'var ' in value) else 'oge', value)
    return codes


def parse_content(content: str, filename: str, selected_keys: Optional[List[str]] = None, selected_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """解析 JSON/CSV，返回可选择的结构信息与逐条代码记录。"""
    suffix = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    if suffix == 'csv':
        rows = list(csv.DictReader(io.StringIO(content)))
        columns = list(rows[0].keys()) if rows else []
        chosen = selected_columns or columns
        items = []
        for index, row in enumerate(rows):
            subset = {key: row.get(key, '') for key in chosen if key in row}
            codes = _detect_codes(subset)
            if codes:
                items.append({'id': str(index + 1), 'label': row.get('name') or row.get('id') or f'CSV 第 {index + 1} 条', 'fields': subset, 'codes': codes})
        return {'format': 'csv', 'columns': columns, 'categories': [], 'items': items}

    data = json.loads(content)
    nodes = list(_flatten_json(data))
    categories = sorted({key for node in nodes for key in node.get('keys', [])})
    chosen = set(selected_keys or [])
    items = []
    for index, node in enumerate(nodes):
        record = node['value']
        if not isinstance(record, dict):
            continue
        if chosen and not (chosen & set(record.keys())) and node['path'] not in chosen:
            continue
        codes = _detect_codes(record)
        if codes:
            items.append({'id': node['path'] or str(index + 1), 'label': record.get('name') or record.get('id') or node['path'], 'fields': record, 'codes': codes})
    return {'format': 'json', 'columns': [], 'categories': categories, 'items': items}
