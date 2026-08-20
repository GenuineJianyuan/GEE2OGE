"""
GEE-OGE 算子映射知识库 - 数据访问层（DAO）

封装对 SQLite 数据库的所有查询操作，业务代码不直接操作数据表。
本模块提供统一的查询接口，支持：
- 单条/批量查询 GEE API 信息
- 单条/批量查询 OGE API 信息
- 按映射类型筛选算子映射
- 按 GEE API 名查询对应的 OGE 实现（含 Python 实现）
- 按版本号加载知识库（预留）
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


# ============================================================
# 默认数据库路径
# ============================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 资源文件（数据源、建表脚本、数据库）统一存放在 resource/ 目录
RESOURCE_DIR = os.path.join(PROJECT_ROOT, 'resource')
DEFAULT_DB_PATH = os.path.join(RESOURCE_DIR, 'gee_oge.db')


# ============================================================
# 数据访问对象
# ============================================================

class GeeOgeDao:
    """GEE-OGE 算子映射知识库数据访问对象

    封装所有数据库查询操作，提供面向业务的接口

    Attributes:
        db_path: SQLite 数据库文件路径
        conn: 数据库连接（懒加载）
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """初始化 DAO

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ----- 连接管理 -----

    @property
    def conn(self) -> sqlite3.Connection:
        """获取数据库连接（懒加载）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row  # 启用字典式访问
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ----- 通用工具 -----

    @staticmethod
    def _parse_json(value: Any) -> Any:
        """安全解析 JSON 字段

        Args:
            value: 数据库字段值

        Returns:
            Any: 解析后的 Python 对象，解析失败返回原值
        """
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    # ============================================================
    # 类映射表 (class_mapping) 查询
    # ============================================================

    def get_all_class_mappings(self) -> List[Dict[str, Any]]:
        """获取全部类映射关系

        Returns:
            List[Dict]: 类映射列表
        """
        cursor = self.conn.execute("SELECT * FROM class_mapping ORDER BY gee_class")
        return [dict(row) for row in cursor.fetchall()]

    def get_class_mapping(self, gee_class: str) -> Optional[Dict[str, Any]]:
        """根据 GEE 类名查询对应的 OGE 类

        Args:
            gee_class: GEE 类名（如 ee.Image）

        Returns:
            Optional[Dict]: 类映射字典，未找到返回 None
        """
        cursor = self.conn.execute(
            "SELECT * FROM class_mapping WHERE gee_class = ?", (gee_class,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def is_class_mappable(self, gee_class: str) -> bool:
        """判断 GEE 类是否可映射

        Args:
            gee_class: GEE 类名

        Returns:
            bool: 可映射返回 True
        """
        mapping = self.get_class_mapping(gee_class)
        return bool(mapping and mapping['is_valid'])

    # ============================================================
    # GEE API 信息表 (gee_api_info) 查询
    # ============================================================

    def get_gee_api_by_name(self, api_full_name: str) -> Optional[Dict[str, Any]]:
        """根据 GEE API 全名查询 API 详情

        Args:
            api_full_name: GEE API 全名（如 ee.Image.abs）

        Returns:
            Optional[Dict]: API 详情字典，未找到返回 None
        """
        cursor = self.conn.execute(
            "SELECT * FROM gee_api_info WHERE api_full_name = ?", (api_full_name,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['arg_types'] = self._parse_json(result.get('arg_types'))
            return result
        return None

    def get_gee_api_by_id(self, api_id: int) -> Optional[Dict[str, Any]]:
        """根据 id 查询 GEE API 详情

        Args:
            api_id: GEE API 内部 id

        Returns:
            Optional[Dict]: API 详情字典
        """
        cursor = self.conn.execute(
            "SELECT * FROM gee_api_info WHERE id = ?", (api_id,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['arg_types'] = self._parse_json(result.get('arg_types'))
            return result
        return None

    def get_gee_apis_by_class(self, class_name: str, analytical_only: bool = False) -> List[Dict[str, Any]]:
        """根据类名查询所有 GEE API

        Args:
            class_name: GEE 类名（如 ee.Image）
            analytical_only: 是否只返回分析类 API（is_analytical=1）

        Returns:
            List[Dict]: GEE API 列表
        """
        if analytical_only:
            sql = """SELECT * FROM gee_api_info
                     WHERE class_name = ? AND is_analytical = 1
                     ORDER BY method_name"""
        else:
            sql = """SELECT * FROM gee_api_info
                     WHERE class_name = ? ORDER BY method_name"""
        cursor = self.conn.execute(sql, (class_name,))
        results = []
        for row in cursor.fetchall():
            item = dict(row)
            item['arg_types'] = self._parse_json(item.get('arg_types'))
            results.append(item)
        return results

    def search_gee_apis(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """按关键词搜索 GEE API

        Args:
            keyword: 搜索关键词
            limit: 最大返回数量

        Returns:
            List[Dict]: 匹配的 GEE API 列表
        """
        cursor = self.conn.execute(
            """SELECT * FROM gee_api_info
               WHERE api_full_name LIKE ? OR description LIKE ? OR method_name LIKE ?
               LIMIT ?""",
            (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    # ============================================================
    # OGE API 信息表 (oge_api_info) 查询
    # ============================================================

    def get_oge_api_by_name(self, api_name: str) -> Optional[Dict[str, Any]]:
        """根据 OGE API 名查询 API 详情

        Args:
            api_name: OGE API 名（如 Coverage.abs）

        Returns:
            Optional[Dict]: API 详情字典
        """
        cursor = self.conn.execute(
            "SELECT * FROM oge_api_info WHERE api_name = ?", (api_name,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['input_types'] = self._parse_json(result.get('input_types'))
            result['raw_definition_json'] = self._parse_json(result.get('raw_definition_json'))
            return result
        return None

    def get_oge_api_by_id(self, api_id: int) -> Optional[Dict[str, Any]]:
        """根据 id 查询 OGE API 详情"""
        cursor = self.conn.execute(
            "SELECT * FROM oge_api_info WHERE id = ?", (api_id,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['input_types'] = self._parse_json(result.get('input_types'))
            result['raw_definition_json'] = self._parse_json(result.get('raw_definition_json'))
            return result
        return None

    def get_oge_apis_by_catalog(self, catalog_name: str) -> List[Dict[str, Any]]:
        """根据目录名查询 OGE API 列表

        Args:
            catalog_name: 目录名（如"预处理"）

        Returns:
            List[Dict]: OGE API 列表
        """
        cursor = self.conn.execute(
            "SELECT * FROM oge_api_info WHERE catalog_name = ? ORDER BY api_name",
            (catalog_name,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_general_purpose_oge_apis(self) -> List[Dict[str, Any]]:
        """获取所有通用处理的 OGE API（第二级过滤结果）

        Returns:
            List[Dict]: 通用 OGE API 列表
        """
        cursor = self.conn.execute(
            """SELECT * FROM oge_api_info
               WHERE is_general_purpose = 1 AND is_custom_model = 0 AND is_deprecated = 0
               ORDER BY api_name"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def search_oge_apis(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """按关键词搜索 OGE API"""
        cursor = self.conn.execute(
            """SELECT * FROM oge_api_info
               WHERE api_name LIKE ? OR description LIKE ?
               LIMIT ?""",
            (f'%{keyword}%', f'%{keyword}%', limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    # ============================================================
    # 算子映射表 (operator_mapping) 查询 - 核心接口
    # ============================================================

    def get_mapping_by_gee_name(self, gee_api_name: str) -> Optional[Dict[str, Any]]:
        """根据 GEE API 名查询映射关系（核心查询接口）

        这是流水线最常用的查询接口，输入 GEE API 名，
        返回完整的映射信息（含 OGE API 详情或 Python 实现代码）

        Args:
            gee_api_name: GEE API 全名（如 ee.Image.abs）

        Returns:
            Optional[Dict]: 映射详情，结构如下：
                {
                    'gee_api': {...},       # GEE API 详情
                    'oge_api': {...},       # OGE API 详情（native_python/missing 时为 None）
                    'mapping_type': str,    # 映射类型
                    'combo_steps': [...],   # 组合步骤（仅 one_to_many）
                    'native_python_code': str,  # Python 实现（仅 native_python）
                    'confidence': float,    # 置信度
                    'verification_status': str,
                    'review_comment': str
                }
            未找到映射返回 None
        """
        # 查询映射记录
        cursor = self.conn.execute(
            """SELECT m.*, g.api_full_name as gee_full_name
               FROM operator_mapping m
               JOIN gee_api_info g ON m.gee_api_id = g.id
               WHERE g.api_full_name = ?""",
            (gee_api_name,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        mapping = dict(row)
        gee_api_id = mapping['gee_api_id']
        oge_api_id = mapping['oge_api_id']

        # 查询 GEE API 详情
        gee_api = self.get_gee_api_by_id(gee_api_id)

        # 查询 OGE API 详情
        oge_api = None
        if oge_api_id:
            oge_api = self.get_oge_api_by_id(oge_api_id)

        return {
            'gee_api': gee_api,
            'oge_api': oge_api,
            'mapping_type': mapping['mapping_type'],
            'combo_steps': self._parse_json(mapping.get('combo_steps')),
            'native_python_code': mapping.get('native_python_code'),
            'confidence': mapping.get('confidence'),
            'verification_status': mapping.get('verification_status'),
            'review_comment': mapping.get('review_comment'),
        }

    def get_mappings_batch(self, gee_api_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """批量查询多个 GEE API 的映射关系

        Args:
            gee_api_names: GEE API 全名列表

        Returns:
            Dict[str, Optional[Dict]]: {api_name: mapping_detail}
        """
        return {name: self.get_mapping_by_gee_name(name) for name in gee_api_names}

    def get_mappings_by_type(self, mapping_type: str) -> List[Dict[str, Any]]:
        """按映射类型查询所有映射

        Args:
            mapping_type: 映射类型 (one_to_one/one_to_many/many_to_one/native_python/missing)

        Returns:
            List[Dict]: 映射详情列表
        """
        cursor = self.conn.execute(
            """SELECT m.*, g.api_full_name as gee_full_name
               FROM operator_mapping m
               JOIN gee_api_info g ON m.gee_api_id = g.id
               WHERE m.mapping_type = ?""",
            (mapping_type,)
        )
        results = []
        for row in cursor.fetchall():
            mapping = dict(row)
            gee_api = self.get_gee_api_by_id(mapping['gee_api_id'])
            oge_api = None
            if mapping['oge_api_id']:
                oge_api = self.get_oge_api_by_id(mapping['oge_api_id'])
            results.append({
                'gee_api': gee_api,
                'oge_api': oge_api,
                'mapping_type': mapping['mapping_type'],
                'combo_steps': self._parse_json(mapping.get('combo_steps')),
                'native_python_code': mapping.get('native_python_code'),
                'confidence': mapping.get('confidence'),
                'verification_status': mapping.get('verification_status'),
                'review_comment': mapping.get('review_comment'),
            })
        return results

    def get_all_mappings(self) -> List[Dict[str, Any]]:
        """获取所有映射记录

        Returns:
            List[Dict]: 全部映射详情列表
        """
        cursor = self.conn.execute(
            """SELECT m.*, g.api_full_name as gee_full_name
               FROM operator_mapping m
               JOIN gee_api_info g ON m.gee_api_id = g.id
               ORDER BY g.api_full_name"""
        )
        results = []
        for row in cursor.fetchall():
            mapping = dict(row)
            gee_api = self.get_gee_api_by_id(mapping['gee_api_id'])
            oge_api = None
            if mapping['oge_api_id']:
                oge_api = self.get_oge_api_by_id(mapping['oge_api_id'])
            results.append({
                'gee_api': gee_api,
                'oge_api': oge_api,
                'mapping_type': mapping['mapping_type'],
                'combo_steps': self._parse_json(mapping.get('combo_steps')),
                'native_python_code': mapping.get('native_python_code'),
                'confidence': mapping.get('confidence'),
                'verification_status': mapping.get('verification_status'),
                'review_comment': mapping.get('review_comment'),
            })
        return results

    def get_missing_apis(self) -> List[Dict[str, Any]]:
        """获取所有缺失映射的 GEE API（mapping_type='missing'）

        Returns:
            List[Dict]: 缺失映射的 GEE API 列表
        """
        return self.get_mappings_by_type('missing')

    def get_native_python_implementations(self) -> List[Dict[str, Any]]:
        """获取所有 Python 实现的映射

        Returns:
            List[Dict]: Python 实现的映射列表
        """
        return self.get_mappings_by_type('native_python')

    # ============================================================
    # 统计接口
    # ============================================================

    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息

        Returns:
            Dict: 统计信息
        """
        stats = {}

        # 总数统计
        stats['total_gee_apis'] = self.conn.execute(
            "SELECT COUNT(*) FROM gee_api_info"
        ).fetchone()[0]
        stats['total_oge_apis'] = self.conn.execute(
            "SELECT COUNT(*) FROM oge_api_info"
        ).fetchone()[0]
        stats['total_mappings'] = self.conn.execute(
            "SELECT COUNT(*) FROM operator_mapping"
        ).fetchone()[0]

        # 按映射类型统计
        cursor = self.conn.execute(
            """SELECT mapping_type, COUNT(*) as cnt
               FROM operator_mapping GROUP BY mapping_type"""
        )
        stats['by_mapping_type'] = {row['mapping_type']: row['cnt'] for row in cursor.fetchall()}

        # 按校验状态统计
        cursor = self.conn.execute(
            """SELECT verification_status, COUNT(*) as cnt
               FROM operator_mapping GROUP BY verification_status"""
        )
        stats['by_verification_status'] = {
            row['verification_status']: row['cnt'] for row in cursor.fetchall()
        }

        # GEE API 分类统计
        cursor = self.conn.execute(
            """SELECT class_name, COUNT(*) as cnt
               FROM gee_api_info GROUP BY class_name ORDER BY cnt DESC"""
        )
        stats['gee_by_class'] = {row['class_name']: row['cnt'] for row in cursor.fetchall()}

        # OGE API 通用/弃用统计
        stats['oge_general_purpose'] = self.conn.execute(
            "SELECT COUNT(*) FROM oge_api_info WHERE is_general_purpose = 1"
        ).fetchone()[0]
        stats['oge_custom_model'] = self.conn.execute(
            "SELECT COUNT(*) FROM oge_api_info WHERE is_custom_model = 1"
        ).fetchone()[0]
        stats['oge_deprecated'] = self.conn.execute(
            "SELECT COUNT(*) FROM oge_api_info WHERE is_deprecated = 1"
        ).fetchone()[0]

        return stats

    # ============================================================
    # 匹配率计算（供流水线使用）
    # ============================================================

    def calculate_match_rate(self, gee_api_names: List[str]) -> Dict[str, Any]:
        """计算给定 GEE API 列表的匹配率

        Args:
            gee_api_names: GEE API 全名列表

        Returns:
            Dict: 匹配率详情，包含：
                - total: API 总数
                - matched: 已匹配数（含 one_to_one/one_to_many/native_python）
                - missing: 未匹配数
                - match_rate: 匹配率 (0~1)
                - details: 每个 API 的匹配状态
        """
        total = len(gee_api_names)
        matched = 0
        missing = 0
        details = []

        for name in gee_api_names:
            mapping = self.get_mapping_by_gee_name(name)
            if mapping is None:
                # 没有任何映射记录，视为缺失
                missing += 1
                details.append({
                    'gee_api': name,
                    'status': 'missing',
                    'reason': '数据库中无映射记录'
                })
            elif mapping['mapping_type'] == 'missing':
                missing += 1
                details.append({
                    'gee_api': name,
                    'status': 'missing',
                    'reason': mapping.get('review_comment', '标记为缺失')
                })
            else:
                matched += 1
                details.append({
                    'gee_api': name,
                    'status': 'matched',
                    'mapping_type': mapping['mapping_type'],
                    'oge_api': mapping['oge_api']['api_name'] if mapping['oge_api'] else None,
                    'has_python': mapping['mapping_type'] == 'native_python'
                })

        match_rate = matched / total if total > 0 else 0.0

        return {
            'total': total,
            'matched': matched,
            'missing': missing,
            'match_rate': round(match_rate, 4),
            'details': details
        }

    # ============================================================
    # Case Study 流水线记录表 (case_study_pipeline) 接口
    # ============================================================

    def save_pipeline_result(self, case_name: str, gee_code: str,
                             step1_summary: Any, step2_apis: Any,
                             step3_match: Any, step4_codegen: Any,
                             step5_feasible: Any, step6_workflow: str,
                             match_rate: float, feasibility: str) -> int:
        """保存一次 Case Study 流水线执行结果

        Args:
            case_name: 案例名称
            gee_code: 原始 GEE 代码
            step1_summary: 步骤 1 语义抽象结果（dict 或 JSON 字符串）
            step2_apis: 步骤 2 API 需求清单
            step3_match: 步骤 3 匹配结果
            step4_codegen: 步骤 4 代码生成结果
            step5_feasible: 步骤 5 可行性补全结果
            step6_workflow: 步骤 6 最终 OGE 工作流代码
            match_rate: API 匹配率
            feasibility: 整体可行性标签 (full_feasible/partial_feasible/infeasible)

        Returns:
            int: 新记录的 id
        """
        def _to_json_str(v: Any) -> Optional[str]:
            """将 dict 转为 JSON 字符串，字符串原样返回"""
            if v is None:
                return None
            if isinstance(v, str):
                return v
            return json.dumps(v, ensure_ascii=False)

        cursor = self.conn.execute(
            """INSERT INTO case_study_pipeline
               (case_name, gee_code, step1_summary, step2_apis, step3_match,
                step4_codegen, step5_feasible, step6_workflow, match_rate, feasibility)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (case_name, gee_code,
             _to_json_str(step1_summary), _to_json_str(step2_apis),
             _to_json_str(step3_match), _to_json_str(step4_codegen),
             _to_json_str(step5_feasible), step6_workflow,
             match_rate, feasibility)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_pipeline_result(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据 id 查询完整的流水线执行记录

        Args:
            record_id: 记录 id

        Returns:
            Optional[Dict]: 完整记录，JSON 字段已解析为 Python 对象；未找到返回 None
        """
        cursor = self.conn.execute(
            "SELECT * FROM case_study_pipeline WHERE id = ?", (record_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        # 解析各步骤的 JSON 字段
        for key in ['step1_summary', 'step2_apis', 'step3_match',
                    'step4_codegen', 'step5_feasible']:
            result[key] = self._parse_json(result.get(key))
        return result

    def list_pipeline_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出历史流水线执行记录（简要信息，不含完整代码）

        Args:
            limit: 最大返回数量

        Returns:
            List[Dict]: 简要记录列表，含 id、案例名、匹配率、可行性、时间
        """
        cursor = self.conn.execute(
            """SELECT id, case_name, match_rate, feasibility, created_at
               FROM case_study_pipeline
               ORDER BY id DESC LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_pipeline_step(self, record_id: int, step: int) -> Optional[Any]:
        """获取某条流水线记录中指定步骤的详细结果

        Args:
            record_id: 记录 id
            step: 步骤号 (1~6)

        Returns:
            Optional[Any]: 该步骤的结果对象（步骤 6 为字符串，其余为 dict）；未找到返回 None
        """
        if step not in (1, 2, 3, 4, 5, 6):
            raise ValueError(f"step 必须为 1~6，收到: {step}")
        column_map = {
            1: 'step1_summary', 2: 'step2_apis', 3: 'step3_match',
            4: 'step4_codegen', 5: 'step5_feasible', 6: 'step6_workflow'
        }
        column = column_map[step]
        cursor = self.conn.execute(
            f"SELECT {column} FROM case_study_pipeline WHERE id = ?",
            (record_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        value = row[0]
        if step == 6:
            return value
        return self._parse_json(value)
