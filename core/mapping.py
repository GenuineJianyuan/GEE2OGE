"""GEE-to-OGE 算子映射库与匹配算法。

从主项目 ``db_dao.py`` 的 ``match_apis_v2`` 和 ``calculate_match_rate``
中提取核心匹配算法，去除 SQLite 依赖，改用 JSON 映射文件。

支持的映射类型：
- one_to_one: 一个 GEE API 对应一个 OGE API
- one_to_many: 一个 GEE API 对应多个 OGE API
- many_to_one: 多个 GEE API 组合对应一个 OGE API
- many_to_many: 多个 GEE API 组合对应多个 OGE API
- native_python: GEE API 对应 Python 原生实现（无 OGE 算子）
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


# ============================================================
# 数据结构定义
# ============================================================

@dataclass
class OperatorMapping:
    """单条算子映射记录。

    Attributes:
        gee_api: GEE API 全名（one_to_one/one_to_many 时为单个，many_to_* 时为组合中的第一个）
        gee_api_names: GEE API 全名列表（用于组合映射）
        oge_apis: 对应的 OGE API 全名列表
        mapping_type: 映射类型：one_to_one / one_to_many / many_to_one / many_to_many / native_python
        mapping_name: 映射名称（组合映射的标识名）
        note: 备注说明
        gee_example: GEE 调用示例
        oge_example: OGE 调用示例
        python_implementation: Python 原生实现代码（native_python 类型）
        confidence: 置信度（0~1）
    """
    gee_api: str = ''
    gee_api_names: List[str] = field(default_factory=list)
    oge_apis: List[str] = field(default_factory=list)
    mapping_type: str = 'one_to_one'
    mapping_name: str = ''
    note: str = ''
    gee_example: str = ''
    oge_example: str = ''
    python_implementation: str = ''
    confidence: float = 1.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperatorMapping':
        """从字典构造映射对象。

        Args:
            data: 字典数据

        Returns:
            OperatorMapping: 映射对象
        """
        gee_api_names = data.get('gee_api_names', []) or []
        if not gee_api_names and data.get('gee_api'):
            gee_api_names = [data['gee_api']]
        return cls(
            gee_api=data.get('gee_api', gee_api_names[0] if gee_api_names else ''),
            gee_api_names=gee_api_names,
            oge_apis=data.get('oge_apis', []) or [],
            mapping_type=data.get('mapping_type', 'one_to_one'),
            mapping_name=data.get('mapping_name', ''),
            note=data.get('note', ''),
            gee_example=data.get('gee_example', ''),
            oge_example=data.get('oge_example', ''),
            python_implementation=data.get('python_implementation', ''),
            confidence=float(data.get('confidence', 1.0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。

        Returns:
            Dict: 字典表示
        """
        return {
            'gee_api': self.gee_api,
            'gee_api_names': self.gee_api_names,
            'oge_apis': self.oge_apis,
            'mapping_type': self.mapping_type,
            'mapping_name': self.mapping_name,
            'note': self.note,
            'gee_example': self.gee_example,
            'oge_example': self.oge_example,
            'python_implementation': self.python_implementation,
            'confidence': self.confidence,
        }


@dataclass
class MatchDetail:
    """单个 API 的匹配详情。

    Attributes:
        gee_api: GEE API 全名
        status: 匹配状态：matched / missing
        mapping_type: 映射类型
        oge_api: 对应的 OGE API 字符串（多个用 + 连接）
        oge_api_names: OGE API 列表
        mapping_id: 映射 ID（可选）
        part_of_combo: 是否属于组合映射
        mapping_name: 映射名称（组合映射时使用）
    """
    gee_api: str = ''
    status: str = 'missing'
    mapping_type: str = ''
    oge_api: str = ''
    oge_api_names: List[str] = field(default_factory=list)
    mapping_id: Optional[int] = None
    part_of_combo: bool = False
    mapping_name: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            'gee_api': self.gee_api,
            'status': self.status,
            'mapping_type': self.mapping_type,
            'oge_api': self.oge_api,
            'oge_api_names': self.oge_api_names,
            'mapping_id': self.mapping_id,
            'part_of_combo': self.part_of_combo,
            'mapping_name': self.mapping_name,
        }


@dataclass
class ComboMatch:
    """组合匹配结果。

    Attributes:
        mapping_name: 组合映射名称
        mapping_type: many_to_one / many_to_many
        gee_apis: GEE API 组合列表
        oge_apis: OGE API 列表
        match_count: 匹配次数
        gee_example: GEE 示例
        oge_example: OGE 示例
        remark: 备注说明
    """
    mapping_name: str = ''
    mapping_type: str = 'many_to_one'
    gee_apis: List[str] = field(default_factory=list)
    oge_apis: List[str] = field(default_factory=list)
    match_count: int = 0
    gee_example: str = ''
    oge_example: str = ''
    remark: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            'mapping_name': self.mapping_name,
            'mapping_type': self.mapping_type,
            'gee_apis': self.gee_apis,
            'oge_apis': self.oge_apis,
            'match_count': self.match_count,
            'gee_example': self.gee_example,
            'oge_example': self.oge_example,
            'remark': self.remark,
        }


@dataclass
class MatchResult:
    """API 匹配结果汇总。

    Attributes:
        total: 总 API 调用次数
        matched: 已匹配次数
        missing_count: 未匹配次数
        match_rate: 匹配率（0~1）
        details: 每个 API 调用的匹配详情（保留顺序和重复）
        dedup_details: 按 GEE API 去重后的匹配详情
        combo_matches: 组合匹配列表
        missing_apis: 未匹配的 API 列表（去重）
        api_lookup: GEE API → 映射信息的查找表（用于代码生成）
    """
    total: int = 0
    matched: int = 0
    missing_count: int = 0
    match_rate: float = 0.0
    details: List[MatchDetail] = field(default_factory=list)
    dedup_details: List[Dict[str, Any]] = field(default_factory=list)
    combo_matches: List[ComboMatch] = field(default_factory=list)
    missing_apis: List[str] = field(default_factory=list)
    api_lookup: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            'total': self.total,
            'matched': self.matched,
            'missing_count': self.missing_count,
            'match_rate': self.match_rate,
            'details': [d.to_dict() for d in self.details],
            'dedup_details': self.dedup_details,
            'combo_matches': [c.to_dict() for c in self.combo_matches],
            'missing_apis': self.missing_apis,
            'api_lookup': self.api_lookup,
        }


# ============================================================
# 映射库类
# ============================================================

class MappingLibrary:
    """GEE-to-OGE 算子映射库。

    从 JSON 文件加载映射数据，提供正向查找、反向查找、
    批量匹配、组合匹配等核心算法。
    """

    def __init__(self, mappings: Iterable[OperatorMapping]):
        """初始化映射库。

        Args:
            mappings: 映射记录列表
        """
        self._all_mappings: List[OperatorMapping] = list(mappings)

        # 正向索引：GEE API → 映射列表（可能有多个映射类型匹配同一个 GEE API）
        self._by_gee: Dict[str, List[OperatorMapping]] = {}
        # 反向索引：OGE API → 映射列表
        self._by_oge: Dict[str, List[OperatorMapping]] = {}
        # 组合映射列表（many_to_one / many_to_many）
        self._combo_mappings: List[OperatorMapping] = []

        for mapping in self._all_mappings:
            # 正向索引：对组合映射，每个 GEE API 都能查到
            gee_apis = mapping.gee_api_names or [mapping.gee_api]
            for gee_api in gee_apis:
                self._by_gee.setdefault(gee_api, []).append(mapping)

            # 反向索引
            for oge_api in mapping.oge_apis:
                self._by_oge.setdefault(oge_api, []).append(mapping)

            # 组合映射单独保存
            if mapping.mapping_type in ('many_to_one', 'many_to_many'):
                self._combo_mappings.append(mapping)

    @classmethod
    def from_json(cls, path: str | Path) -> 'MappingLibrary':
        """从 JSON 文件加载映射库。

        Args:
            path: JSON 文件路径

        Returns:
            MappingLibrary: 映射库实例
        """
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        items = [OperatorMapping.from_dict(item) for item in raw]
        return cls(items)

    # ----- 基础查找 -----

    def find_gee(self, gee_api: str) -> Optional[OperatorMapping]:
        """根据 GEE API 名查找映射（返回第一个匹配的一对一/一对多映射）。

        Args:
            gee_api: GEE API 全名

        Returns:
            Optional[OperatorMapping]: 匹配的映射，未找到返回 None
        """
        mappings = self._by_gee.get(gee_api, [])
        # 优先返回非组合映射
        for m in mappings:
            if m.mapping_type not in ('many_to_one', 'many_to_many'):
                return m
        return mappings[0] if mappings else None

    def find_all_gee(self, gee_api: str) -> List[OperatorMapping]:
        """根据 GEE API 名查找所有相关映射（包括组合映射）。

        Args:
            gee_api: GEE API 全名

        Returns:
            List[OperatorMapping]: 所有相关的映射
        """
        return list(self._by_gee.get(gee_api, []))

    def find_oge(self, oge_api: str) -> List[OperatorMapping]:
        """根据 OGE API 名反向查找对应的 GEE 映射。

        Args:
            oge_api: OGE API 全名

        Returns:
            List[OperatorMapping]: 包含该 OGE API 的所有映射
        """
        return list(self._by_oge.get(oge_api, []))

    def get_all_mappings(self) -> List[OperatorMapping]:
        """获取所有映射记录。

        Returns:
            List[OperatorMapping]: 全部映射列表
        """
        return list(self._all_mappings)

    def get_combo_mappings(self) -> List[OperatorMapping]:
        """获取所有组合映射（many_to_one / many_to_many）。

        Returns:
            List[OperatorMapping]: 组合映射列表
        """
        return list(self._combo_mappings)

    # ----- 匹配率计算 -----

    def match_report(self, gee_apis: Iterable[str]) -> Dict[str, Any]:
        """计算简单匹配率（仅一对一匹配，不含组合匹配）。

        Args:
            gee_apis: GEE API 列表

        Returns:
            Dict: 包含 total, matched, missing, match_rate, missing_apis 的字典
        """
        api_list = list(gee_apis)
        matched = [name for name in api_list if self.find_gee(name)]
        missing = [name for name in api_list if not self.find_gee(name)]
        return {
            'total': len(api_list),
            'matched': len(matched),
            'missing': len(missing),
            'match_rate': len(matched) / len(api_list) if api_list else 0.0,
            'missing_apis': sorted(set(missing)),
        }

    # ----- 核心：组合匹配 + 一对一匹配完整算法 -----

    def match_apis(self, gee_api_names: List[str]) -> MatchResult:
        """基于完整匹配策略计算 GEE API 列表的匹配情况。

        匹配策略：
        1. 先匹配组合映射（many_to_one + many_to_many）：
           - 组合按 GEE API 数量降序排列，更大、更具体的组合优先匹配
           - 相同大小按稀缺度升序（越稀缺越先匹配，保证组合多样性）
           - 同一个 API 可以参与多个组合（只要出现次数足够）
           - 每个组合一次性贪婪匹配尽可能多次
        2. 剩余未被消费的 API 逐个匹配 one_to_one / one_to_many / native_python
        3. 都没匹配上 → missing

        Args:
            gee_api_names: GEE API 全名列表（按调用顺序，可重复）

        Returns:
            MatchResult: 完整匹配结果
        """
        result = MatchResult()
        total = len(gee_api_names)
        result.total = total

        if total == 0:
            return result

        # 统计每个 API 出现的次数
        api_counts = Counter(gee_api_names)
        # 剩余可用次数（用于组合匹配消耗）
        remaining_counts = dict(api_counts)

        details: List[MatchDetail] = []
        combo_matches: List[ComboMatch] = []
        api_lookup: Dict[str, Dict[str, Any]] = {}

        # ---- Step 1: 匹配组合映射（many_to_one + many_to_many） ----
        # 准备组合列表并计算初始稀缺度
        all_combos: List[tuple] = []
        for mapping in self._combo_mappings:
            gee_apis = mapping.gee_api_names
            gee_set = set(gee_apis)
            if not gee_set:
                continue
            combo_size = len(gee_apis)
            # 计算瓶颈稀缺度：受限于出现次数最少的那个 API
            scarcity = min(
                api_counts.get(api, 0) // gee_apis.count(api)
                for api in gee_set
            )
            # 排序 key: (-大小, 稀缺度) → 大小降序，稀缺度升序
            all_combos.append((-combo_size, scarcity, mapping, gee_apis, gee_set))

        # 按优先级排序：大组合优先，同大小稀缺的优先
        all_combos.sort(key=lambda x: (x[0], x[1]))

        for _, _, mapping, gee_apis, gee_set in all_combos:
            # 计算这个组合最多能匹配多少次（受限于每个 API 的剩余次数）
            max_matches = float('inf')
            for api in gee_set:
                count_in_combo = gee_apis.count(api)
                available = remaining_counts.get(api, 0)
                max_matches = min(max_matches, available // count_in_combo)

            max_matches = int(max_matches)
            if max_matches <= 0:
                continue

            # 记录组合匹配
            combo_matches.append(ComboMatch(
                mapping_name=mapping.mapping_name,
                mapping_type=mapping.mapping_type,
                gee_apis=list(gee_apis),
                oge_apis=list(mapping.oge_apis),
                match_count=max_matches,
                gee_example=mapping.gee_example,
                oge_example=mapping.oge_example,
                remark=mapping.note,
            ))

            # 消耗这些 API 的次数
            for api in gee_set:
                count_in_combo = gee_apis.count(api)
                remaining_counts[api] -= count_in_combo * max_matches

            # 存入 api_lookup（每个 GEE API 都指向同一个组合映射）
            for gee_api in gee_apis:
                api_lookup[gee_api] = {
                    'mapping_type': mapping.mapping_type,
                    'mapping_name': mapping.mapping_name,
                    'oge_api_names': list(mapping.oge_apis),
                    'gee_example': mapping.gee_example,
                    'oge_example': mapping.oge_example,
                    'remark': mapping.note,
                    'part_of_combo': True,
                }

        # ---- Step 2: 剩余 API 逐个匹配 ----
        # 跟踪每个 API 已被组合消费的次数
        consumed_in_combos: Dict[str, int] = {}
        for cm in combo_matches:
            for api in cm.gee_apis:
                consumed_in_combos[api] = consumed_in_combos.get(api, 0) + cm.match_count

        # 逐个处理输入列表中的每个 API 调用
        # 先消耗组合的配额，再消耗一对一映射
        combo_usage: Dict[str, int] = {}  # 每个 API 在组合中已被分配的次数

        for gee_name in gee_api_names:
            # 检查这个 API 是否属于某个组合，且还有未分配的组合次数
            in_combo = gee_name in api_lookup and api_lookup[gee_name].get('part_of_combo')
            if in_combo:
                used = combo_usage.get(gee_name, 0)
                total_combo_count = consumed_in_combos.get(gee_name, 0)
                if used < total_combo_count:
                    # 这个调用属于组合匹配
                    combo_usage[gee_name] = used + 1
                    lookup_info = api_lookup.get(gee_name, {})
                    actual_mtype = lookup_info.get('mapping_type', 'many_to_one')
                    details.append(MatchDetail(
                        gee_api=gee_name,
                        status='matched',
                        mapping_type=actual_mtype,
                        oge_api_names=lookup_info.get('oge_api_names', []),
                        oge_api=' + '.join(lookup_info.get('oge_api_names', [])),
                        part_of_combo=True,
                        mapping_name=lookup_info.get('mapping_name', ''),
                    ))
                    continue

            # 不在组合中或组合次数已用完 → 尝试一对一/一对多/native_python 匹配
            single_mapping = self._find_single_mapping(gee_name)
            if single_mapping:
                oge_api_str = ' + '.join(single_mapping.oge_apis)
                details.append(MatchDetail(
                    gee_api=gee_name,
                    status='matched',
                    mapping_type=single_mapping.mapping_type,
                    oge_api=oge_api_str,
                    oge_api_names=list(single_mapping.oge_apis),
                    mapping_name=single_mapping.mapping_name,
                ))
                # 如果还没在 api_lookup 中，就存进去
                if gee_name not in api_lookup:
                    api_lookup[gee_name] = {
                        'mapping_type': single_mapping.mapping_type,
                        'mapping_name': single_mapping.mapping_name,
                        'oge_api_names': list(single_mapping.oge_apis),
                        'gee_example': single_mapping.gee_example,
                        'oge_example': single_mapping.oge_example,
                        'python_implementation': single_mapping.python_implementation,
                        'note': single_mapping.note,
                        'part_of_combo': False,
                    }
            else:
                details.append(MatchDetail(
                    gee_api=gee_name,
                    status='missing',
                    mapping_type='',
                    oge_api='',
                    oge_api_names=[],
                ))

        # ---- Step 3: 统计与去重 ----
        matched = sum(1 for d in details if d.status == 'matched')
        missing = total - matched

        result.details = details
        result.matched = matched
        result.missing_count = missing
        result.match_rate = matched / total if total > 0 else 0.0
        result.combo_matches = combo_matches
        result.api_lookup = api_lookup

        # 按 GEE API 去重
        dedup_map: Dict[str, Dict[str, Any]] = {}
        for detail in details:
            gee_api = detail.gee_api
            if not gee_api:
                continue
            existing = dedup_map.get(gee_api)
            if existing is None:
                dedup_map[gee_api] = detail.to_dict()
            else:
                # 优先级：part_of_combo > matched > missing
                def _priority(d: Dict[str, Any]) -> int:
                    if d.get('part_of_combo'):
                        return 3
                    if d.get('status') == 'matched':
                        return 2
                    return 1
                if _priority(detail.to_dict()) > _priority(existing):
                    dedup_map[gee_api] = detail.to_dict()

        result.dedup_details = list(dedup_map.values())
        result.missing_apis = list(set(
            d['gee_api'] for d in result.dedup_details if d.get('status') == 'missing'
        ))

        return result

    def _find_single_mapping(self, gee_api: str) -> Optional[OperatorMapping]:
        """查找单个 GEE API 的非组合映射。

        Args:
            gee_api: GEE API 全名

        Returns:
            Optional[OperatorMapping]: 匹配的映射，未找到返回 None
        """
        mappings = self._by_gee.get(gee_api, [])
        for m in mappings:
            if m.mapping_type in ('one_to_one', 'one_to_many', 'native_python', 'gee_python'):
                return m
        return None

    # ----- 批量查询 -----

    def batch_query(self, gee_api_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量查询多个 GEE API 的映射详情。

        Args:
            gee_api_names: GEE API 全名列表

        Returns:
            Dict[str, Optional[Dict]]: {api_name: mapping_dict}
        """
        result: Dict[str, Optional[Dict[str, Any]]] = {}
        for name in gee_api_names:
            mapping = self.find_gee(name)
            result[name] = mapping.to_dict() if mapping else None
        return result

    # ----- 可行性分类 -----

    def classify_feasibility(self, missing_apis: Iterable[str]) -> Dict[str, Any]:
        """将缺失 API 分为阻断性、非阻断性和可用 Python 补充的辅助缺口。

        Args:
            missing_apis: 缺失的 GEE API 列表

        Returns:
            Dict: 包含 overall_feasible, blocking_apis, non_blocking_gaps, rescue_suggestions
        """
        blocking_keywords = (
            'Image', 'ImageCollection', 'Feature', 'FeatureCollection',
            'Reducer', 'Classifier', 'Filter',
        )
        ui_keywords = ('Map.addLayer', 'Map.setCenter', 'Map.setOptions', 'print', 'Export')

        blocking: List[str] = []
        non_blocking: List[str] = []
        suggestions: List[Dict[str, str]] = []

        for api in missing_apis:
            if any(token in api for token in ui_keywords):
                non_blocking.append(api)
                suggestions.append({
                    'api': api,
                    'suggestion': 'UI/可视化缺口，可改用 print 或注释。',
                })
            elif any(token in api for token in blocking_keywords):
                blocking.append(api)
                suggestions.append({
                    'api': api,
                    'suggestion': '核心分析算子缺失，需补充 Python 实现或替代 OGE 算子。',
                })
            else:
                non_blocking.append(api)
                suggestions.append({
                    'api': api,
                    'suggestion': '辅助算子缺失，可用 Python 原生逻辑补充。',
                })

        return {
            'overall_feasible': not blocking,
            'blocking_apis': blocking,
            'non_blocking_gaps': non_blocking,
            'rescue_suggestions': suggestions,
        }
