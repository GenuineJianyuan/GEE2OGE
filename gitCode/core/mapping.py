"""Lightweight mapping loading, bidirectional lookup, and coverage calculation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class OperatorMapping:
    gee_api: str
    oge_apis: List[str]
    mapping_type: str = 'one_to_one'
    note: str = ''


class MappingLibrary:
    """Load GEE-to-OGE mappings from JSON and expose bidirectional API lookup."""

    def __init__(self, mappings: Iterable[OperatorMapping]):
        self.by_gee = {item.gee_api: item for item in mappings}
        self.by_oge: Dict[str, List[OperatorMapping]] = {}
        for item in mappings:
            for oge_api in item.oge_apis:
                self.by_oge.setdefault(oge_api, []).append(item)

    @classmethod
    def from_json(cls, path: str | Path) -> 'MappingLibrary':
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        items = [OperatorMapping(**item) for item in raw]
        return cls(items)

    def find_gee(self, gee_api: str) -> Optional[OperatorMapping]:
        return self.by_gee.get(gee_api)

    def find_oge(self, oge_api: str) -> List[OperatorMapping]:
        return self.by_oge.get(oge_api, [])

    def match_report(self, gee_apis: Iterable[str]) -> Dict[str, object]:
        api_list = list(gee_apis)
        matched = [name for name in api_list if name in self.by_gee]
        missing = [name for name in api_list if name not in self.by_gee]
        return {
            'total': len(api_list), 'matched': len(matched), 'missing': missing,
            'match_rate': len(matched) / len(api_list) if api_list else 0.0,
        }
