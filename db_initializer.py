"""
GEE-OGE 算子映射知识库 - 数据库初始化与数据导入模块

本模块负责：
1. 根据 db_schema.sql 创建所有表结构
2. 从 gee.json 导入 GEE API 全量信息
3. 从 oge.json 导入 OGE API 全量信息（含三级过滤标记）
4. 根据 GEE/OGE 类对应关系填充 class_mapping
5. 从 gee_to_oge_matches.xlsx 导入已匹配的映射关系到 operator_mapping
6. 从 gee_python_functions.py 和 gee_unmatched_functions.py 导入 Python 实现到 operator_mapping

数据源：
- gee.json: GEE API 全量详细信息
- oge.json: OGE API 全量详细信息
- gee_to_oge_matches.xlsx: Excel 映射表（已匹配的算子）
- gee_python_functions.py: Python 实现的 GEE 函数（基础版）
- gee_unmatched_functions.py: Python 实现的 GEE 函数（扩展版）
"""

import json
import os
import re
import sqlite3
import sys
from typing import Dict, List, Optional, Tuple

# 添加项目根目录到 sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 导入项目内已有模块
from gee_to_ge_mapping import GeeToOgeConverter, ExcelParser, GeeJsonParser  # noqa: E402
# 导入 GEE 示例代码生成器（从 examples 提取并清洗注释）
from gee_sample_generator import _extract_example_code, _gen_sample_code_fallback  # noqa: E402

# ============================================================
# 常量定义
# ============================================================
# 资源文件（数据源、建表脚本、数据库）统一存放在 resource/ 目录
RESOURCE_DIR = os.path.join(PROJECT_ROOT, 'resource')
DB_PATH = os.path.join(RESOURCE_DIR, 'gee_oge.db')
SCHEMA_PATH = os.path.join(RESOURCE_DIR, 'db_schema.sql')
GEE_JSON_PATH = os.path.join(RESOURCE_DIR, 'gee.json')
OGE_JSON_PATH = os.path.join(RESOURCE_DIR, 'oge.json')
XLSX_PATH = os.path.join(RESOURCE_DIR, 'gee_to_oge_matches.xlsx')
# Python 实现源码资产保留在项目根目录（既是可导入模块也是源码资产）
PY_FUNCS_PATH = os.path.join(PROJECT_ROOT, 'gee_python_functions.py')
PY_UNMATCHED_PATH = os.path.join(PROJECT_ROOT, 'gee_unmatched_functions.py')

# GEE 类到 OGE 类的对应关系（基于《GEE-OGE进一步设计.md》方式二的分类映射）
GEE_TO_OGE_CLASS = {
    'ee.Image': 'Coverage',
    'ee.ImageCollection': 'CoverageCollection',
    'ee.Feature': 'Feature',
    'ee.FeatureCollection': 'FeatureCollection',
    'ee.Geometry': 'Geometry',
    'ee.Filter': 'Filter',
    'ee.Reducer': 'Reducer',
    'ee.Classifier': 'Classifier',
    'ee.Clusterer': 'Clusterer',
    'ee.Kernel': 'Kernel',
    'ee.Array': 'Array',
    'ee.List': None,           # 非分析类，无对应
    'ee.Dictionary': None,     # 非分析类，无对应
    'ee.Date': None,
    'ee.DateRange': None,
    'ee.Number': None,
    'ee.String': None,
    'ee.Terrain': 'Coverage',  # 地形处理映射到 Coverage
    'ee.Algorithms': None,
    'Map': None,
    'Export': None,
    'ui': None,                # UI 控件直接跳过
    'print': None,
}

# 非分析类 GEE 类（is_analytical = FALSE，匹配时跳过）
NON_ANALYTICAL_CLASSES = {
    'ee.List', 'ee.Dictionary', 'ee.Number', 'ee.String',
    'ee.Date', 'ee.DateRange', 'ee.Array'
}

# 伪 OGE API 名称集合
# Excel 映射表中部分 OGE 端填写的是 "Python xxx" 形式的占位符，
# 表示该 GEE API 没有真正的 OGE 算子对应，而是用 Python 原生语法实现。
# 这些占位符不应被当作真实 OGE 算子入库，而应归类为 native_python。
PSEUDO_OGE_PREFIXES = ('Python ',)


def _is_pseudo_oge_name(oge_api_name: str) -> bool:
    """判断单个 OGE API 名是否为伪映射占位符

    伪映射特征：
    - 以 "Python " 开头（如 "Python List"、"Python Function"、"Python Int"）
    - 等于 "print"（特殊：print 是 GEE 内置函数，无 OGE 对应）

    Args:
        oge_api_name: OGE API 名称

    Returns:
        bool: 是伪映射返回 True
    """
    if not oge_api_name:
        return False
    if oge_api_name == 'print':
        return True
    for prefix in PSEUDO_OGE_PREFIXES:
        if oge_api_name.startswith(prefix):
            return True
    return False


def _is_pseudo_oge_mapping(oge_full_names: List[str]) -> bool:
    """判断一组 OGE API 名是否全部为伪映射

    当且仅当所有 OGE API 名都是伪映射时，整个映射才视为伪映射。
    若其中包含至少一个真实 OGE 算子，则按真实映射处理。

    Args:
        oge_full_names: OGE API 名称列表

    Returns:
        bool: 全部为伪映射返回 True
    """
    if not oge_full_names:
        return False
    return all(_is_pseudo_oge_name(name) for name in oge_full_names)


# ============================================================
# 数据库初始化
# ============================================================

def init_database(db_path: str = DB_PATH, force: bool = True) -> None:
    """初始化数据库，创建所有表结构

    Args:
        db_path: 数据库文件路径
        force: 是否强制重建（删除已存在的表）
    """
    if force and os.path.exists(db_path):
        os.remove(db_path)

    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"[OK] 数据库已初始化: {db_path}")
    finally:
        conn.close()


# ============================================================
# 表 1: class_mapping 导入
# ============================================================

def import_class_mapping(conn: sqlite3.Connection) -> int:
    """填充类映射表（class_mapping）

    根据 GEE_TO_OGE_CLASS 字典填充 GEE 类与 OGE 类的对应关系

    Args:
        conn: 数据库连接

    Returns:
        int: 导入的记录数
    """
    count = 0
    for gee_class, oge_class in GEE_TO_OGE_CLASS.items():
        is_valid = 1 if oge_class is not None else 0
        if is_valid:
            remark = f"GEE的 {gee_class} 对应 OGE的 {oge_class}"
        else:
            remark = f"GEE的 {gee_class} 为非分析类或 UI 控件，无 OGE 对应，直接跳过"

        conn.execute(
            "INSERT INTO class_mapping (gee_class, oge_class, is_valid, remark) VALUES (?, ?, ?, ?)",
            (gee_class, oge_class, is_valid, remark)
        )
        count += 1

    conn.commit()
    print(f"[OK] class_mapping 已导入 {count} 条记录")
    return count


# ============================================================
# 表 2: gee_api_info 导入
# ============================================================

def import_gee_api_info(conn: sqlite3.Connection) -> int:
    """从 gee.json 导入 GEE API 全量信息（含示例代码）

    Args:
        conn: 数据库连接

    Returns:
        int: 导入的记录数
    """
    with open(GEE_JSON_PATH, 'r', encoding='utf-8') as f:
        gee_data = json.load(f)

    count = 0
    for item in gee_data:
        full_name = item.get('fullName', '')
        if not full_name:
            continue

        class_name = item.get('className', '')
        method_name = item.get('methodName', '')
        return_type = item.get('returns', '')
        description = item.get('description', '')

        # 解析参数
        arguments = item.get('arguments', [])
        arg_types = [arg.get('type', '') for arg in arguments]
        arg_count = len(arguments)

        # 计算示例代码（优先从 examples 提取，无则自动生成）
        example_code = _extract_example_code(item)
        if example_code:
            samplecode = example_code
            sample_source = 'example'
        else:
            samplecode = _gen_sample_code_fallback(item)
            sample_source = 'generated'

        # 判断是否为分析类
        is_analytical = 1
        for non_analytical in NON_ANALYTICAL_CLASSES:
            if full_name.startswith(non_analytical + '.') or full_name == non_analytical:
                is_analytical = 0
                break
        # ui.* 全部为非分析类
        if full_name.startswith('ui.') or full_name.startswith('ee.ui.'):
            is_analytical = 0

        conn.execute(
            """INSERT OR IGNORE INTO gee_api_info
               (api_full_name, class_name, method_name, return_type, arg_types, arg_count, description, samplecode, sample_source, is_analytical)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (full_name, class_name, method_name, return_type,
             json.dumps(arg_types, ensure_ascii=False), arg_count, description,
             samplecode, sample_source, is_analytical)
        )
        count += 1

    conn.commit()
    print(f"[OK] gee_api_info 已导入 {count} 条记录（含示例代码）")
    return count


# ============================================================
# 表 3: oge_api_info 导入
# ============================================================

def _parse_oge_definition(definition_str: str) -> Tuple[List[str], str]:
    """解析 OGE API 的 definitionJson 字段，提取输入输出类型

    Args:
        definition_str: definitionJson 字段的字符串内容

    Returns:
        Tuple[List[str], str]: (输入类型列表, 输出类型)
    """
    if not definition_str:
        return [], ''

    try:
        definition = json.loads(definition_str) if isinstance(definition_str, str) else definition_str
    except (json.JSONDecodeError, TypeError):
        return [], ''

    args = definition.get('args', [])
    input_types = [arg.get('type', '') for arg in args if arg.get('type')]

    output = definition.get('output', {})
    output_type = output.get('type', '') or definition.get('returns', '')

    return input_types, output_type


def import_oge_api_info(conn: sqlite3.Connection) -> int:
    """从 oge.json 导入 OGE API 全量信息（含三级过滤标记）

    三级过滤：
    - 第一级：catalogId=117（林业模型）或 type=2（AI模型）→ is_custom_model=TRUE，弃用
    - 第二级：属于"预处理/单要素/多要素/地形/时空分析"等通用类 → is_general_purpose=TRUE
    - 第三级：名称含 _deprecated → is_deprecated=TRUE，低优先级

    Args:
        conn: 数据库连接

    Returns:
        int: 导入的记录数
    """
    with open(OGE_JSON_PATH, 'r', encoding='utf-8') as f:
        oge_data = json.load(f)

    # 通用处理的 catalog 关键词（用于第二级过滤）
    general_purpose_keywords = [
        '预处理', '单要素', '多要素', '地形', '时空分析',
        '基础处理', '对象获取', '空间分析', '栅格统计',
        'spark算子', '系统基础算法'
    ]

    count = 0
    for item in oge_data:
        api_name = item.get('name', '')
        if not api_name:
            continue

        oge_id = item.get('id', 0)  # OGE 原始业务 ID
        catalog_id = item.get('catalogId', 0)
        catalog_name = item.get('catalogName', '')
        description = item.get('description', '')
        definition_str = item.get('definitionJson', '{}')
        samplecode = item.get('sampleCode', '')
        item_type = item.get('type', 1)

        # 解析输入输出
        input_types, output_type = _parse_oge_definition(definition_str)

        # 第一级过滤：行业模型、AI 模型
        is_custom_model = 0
        if catalog_id == 117 or item_type == 2:
            is_custom_model = 1
        # 也检查 catalog_name 中是否包含"林业"、"行业"等关键词
        if any(kw in catalog_name for kw in ['林业', '行业模型', '广西']):
            is_custom_model = 1

        # 第三级过滤：deprecated
        is_deprecated = 1 if '_deprecated' in api_name.lower() else 0

        # 第二级过滤：通用处理
        is_general_purpose = 0
        if not is_custom_model and not is_deprecated:
            for kw in general_purpose_keywords:
                if kw in catalog_name:
                    is_general_purpose = 1
                    break
            # 如果 API 名称以 Coverage./Feature./FeatureCollection./Geometry. 开头，也视为通用
            if any(api_name.startswith(prefix) for prefix in
                   ['Coverage.', 'Feature.', 'FeatureCollection.', 'Geometry.', 'Service.']):
                is_general_purpose = 1

        conn.execute(
            """INSERT OR IGNORE INTO oge_api_info
               (oge_id, api_name, catalog_id, catalog_name, input_types, output_type, description,
                is_custom_model, is_deprecated, is_general_purpose, raw_definition_json, samplecode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (oge_id, api_name, catalog_id, catalog_name,
             json.dumps(input_types, ensure_ascii=False), output_type, description,
             is_custom_model, is_deprecated, is_general_purpose,
             definition_str, samplecode)
        )
        count += 1

    conn.commit()
    print(f"[OK] oge_api_info 已导入 {count} 条记录")
    return count


# ============================================================
# 表 4: operator_mapping 导入
# ============================================================

def _get_gee_api_id(conn: sqlite3.Connection, api_full_name: str) -> Optional[int]:
    """根据 GEE API 全名查询其内部 id

    Args:
        conn: 数据库连接
        api_full_name: GEE API 全名（如 ee.Image.abs）

    Returns:
        Optional[int]: 数据库中的 id，未找到返回 None
    """
    cursor = conn.execute(
        "SELECT id FROM gee_api_info WHERE api_full_name = ?", (api_full_name,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _get_oge_api_id(conn: sqlite3.Connection, api_name: str) -> Optional[int]:
    """根据 OGE API 名查询其内部 id

    Args:
        conn: 数据库连接
        api_name: OGE API 名（如 Coverage.abs）

    Returns:
        Optional[int]: 数据库中的 id，未找到返回 None
    """
    cursor = conn.execute(
        "SELECT id FROM oge_api_info WHERE api_name = ?", (api_name,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _ensure_gee_api_exists(conn: sqlite3.Connection, api_full_name: str) -> int:
    """确保 GEE API 记录存在，不存在则插入占位记录

    Args:
        conn: 数据库连接
        api_full_name: GEE API 全名

    Returns:
        int: 数据库中的 id
    """
    api_id = _get_gee_api_id(conn, api_full_name)
    if api_id is not None:
        return api_id

    # 解析 class_name 和 method_name
    parts = api_full_name.split('.')
    if len(parts) >= 2:
        class_name = '.'.join(parts[:-1])
        method_name = parts[-1]
    else:
        class_name = ''
        method_name = api_full_name

    cursor = conn.execute(
        """INSERT OR IGNORE INTO gee_api_info
           (api_full_name, class_name, method_name, return_type, arg_types, arg_count, description, is_analytical)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (api_full_name, class_name, method_name, '', '[]', 0, '', 1)
    )
    conn.commit()
    return cursor.lastrowid


def _ensure_oge_api_exists(conn: sqlite3.Connection, api_name: str) -> Optional[int]:
    """确保 OGE API 记录存在，不存在则插入占位记录

    Args:
        conn: 数据库连接
        api_name: OGE API 名

    Returns:
        Optional[int]: 数据库中的 id
    """
    api_id = _get_oge_api_id(conn, api_name)
    if api_id is not None:
        return api_id

    cursor = conn.execute(
        """INSERT OR IGNORE INTO oge_api_info
           (oge_id, api_name, catalog_id, catalog_name, input_types, output_type, description,
            is_custom_model, is_deprecated, is_general_purpose, raw_definition_json, samplecode)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (0, api_name, 0, '', '[]', '', '', 0, 0, 1, '{}', '')
    )
    conn.commit()
    return cursor.lastrowid


def _determine_mapping_type(oge_apis: List[str], native_python: bool = False) -> str:
    """判断映射类型

    Args:
        oge_apis: OGE API 名称列表
        native_python: 是否为 Python 实现

    Returns:
        str: 映射类型 (one_to_one / one_to_many / native_python / missing)
    """
    if native_python:
        return 'native_python'
    if not oge_apis:
        return 'missing'
    if len(oge_apis) == 1:
        return 'one_to_one'
    return 'one_to_many'


def import_operator_mapping_from_xlsx(conn: sqlite3.Connection) -> int:
    """从 Excel 映射表导入已匹配的映射关系

    导入规则：
    1. 真 OGE 映射（OGE API 名非 "Python xxx"）：按 one_to_one / one_to_many 导入
    2. 伪 OGE 映射（OGE API 名为 "Python xxx" 或 "print"）：跳过，
       由 import_native_python_implementations 统一导入为 native_python
    3. 未匹配的 GEE API：导入为 missing

    Args:
        conn: 数据库连接

    Returns:
        int: 导入的记录数（不含跳过的伪映射）
    """
    converter = GeeToOgeConverter(XLSX_PATH, GEE_JSON_PATH)
    matched = converter.get_all_matched()

    count = 0
    skipped_pseudo = 0
    for item in matched:
        gee_name = item.gee_api.canonical_name
        gee_id = _ensure_gee_api_exists(conn, gee_name)

        oge_full_names = item.get_oge_full_names() if item.matched else []

        if not oge_full_names:
            # 未匹配的算子，记录为 missing
            conn.execute(
                """INSERT INTO operator_mapping
                   (gee_api_id, oge_api_id, mapping_type, confidence, verification_status, review_comment)
                   VALUES (?, NULL, 'missing', 0.0, 'pending_review', ?)""",
                (gee_id, item.reason or 'Excel 表标记为未匹配')
            )
            count += 1
            continue

        # 伪 OGE 映射跳过（由 Python 函数文件统一导入为 native_python）
        if _is_pseudo_oge_mapping(oge_full_names):
            skipped_pseudo += 1
            continue

        # 判断映射类型
        mapping_type = _determine_mapping_type(oge_full_names)

        # 一对多映射，记录组合步骤
        combo_steps = None
        if mapping_type == 'one_to_many':
            steps = []
            for idx, oge_name in enumerate(oge_full_names, 1):
                steps.append({"step": idx, "oge_api": oge_name})
            combo_steps = json.dumps(steps, ensure_ascii=False)

        # 第一个 OGE API 作为主映射
        primary_oge_id = _ensure_oge_api_exists(conn, oge_full_names[0])

        # 置信度：Excel 已匹配的算子默认 0.85（视为高置信度自动通过）
        confidence = 0.8500
        status = 'auto_approved'

        conn.execute(
            """INSERT INTO operator_mapping
               (gee_api_id, oge_api_id, mapping_type, combo_steps, native_python_code,
                confidence, llm_judge_detail, verification_status, review_comment)
               VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?)""",
            (gee_id, primary_oge_id, mapping_type, combo_steps,
             confidence, json.dumps({"source": "excel", "reason": item.reason}, ensure_ascii=False),
             status, item.reason)
        )
        count += 1

    conn.commit()
    print(f"[OK] operator_mapping (Excel 真映射) 已导入 {count} 条记录"
          f"（跳过 {skipped_pseudo} 条伪 OGE 映射，由 Python 实现统一处理）")
    return count


# ============================================================
# 从 Python 函数文件导入 native_python 映射
# ============================================================

def _extract_function_source(file_path: str, func_name: str) -> Optional[str]:
    """从 Python 文件中提取指定函数的完整源代码

    使用 AST 解析定位函数的行范围，然后从源代码中切片

    Args:
        file_path: Python 文件路径
        func_name: 函数名

    Returns:
        Optional[str]: 函数完整源代码，未找到返回 None
    """
    import ast

    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            # 起始行（考虑装饰器）
            start_line = node.lineno
            if node.decorator_list:
                start_line = node.decorator_list[0].lineno
            # 结束行
            if node.body:
                end_line = max(
                    child.end_lineno if hasattr(child, 'end_lineno') else node.lineno
                    for child in ast.walk(node)
                )
            else:
                end_line = node.lineno
            return '\n'.join(lines[start_line - 1: end_line])
    return None


def _load_python_function_registry() -> Dict[str, Tuple[str, str]]:
    """加载两个 Python 函数文件的权威注册表

    直接使用 gee_python_functions.GEE_PYTHON_FUNCTIONS 和
    gee_unmatched_functions.UNMATCHED_API_FUNCTIONS 字典作为权威映射，
    避免 by函数名解析的不准确性

    Returns:
        Dict[str, Tuple[str, str]]: {gee_api_name: (source_file_basename, python_func_name)}
    """
    registry: Dict[str, Tuple[str, str]] = {}

    # 基础 Python 实现
    try:
        from gee_python_functions import GEE_PYTHON_FUNCTIONS
        for gee_name, func in GEE_PYTHON_FUNCTIONS.items():
            registry[gee_name] = ('gee_python_functions.py', func.__name__)
    except ImportError as e:
        print(f"[WARN] 无法导入 gee_python_functions: {e}")

    # 扩展 Python 实现
    try:
        from gee_unmatched_functions import UNMATCHED_API_FUNCTIONS
        for gee_name, func in UNMATCHED_API_FUNCTIONS.items():
            # 若与基础实现冲突，保留基础实现（基础实现更成熟）
            if gee_name not in registry:
                registry[gee_name] = ('gee_unmatched_functions.py', func.__name__)
    except ImportError as e:
        print(f"[WARN] 无法导入 gee_unmatched_functions: {e}")

    return registry


def _has_real_oge_mapping(conn: sqlite3.Connection, gee_api_id: int) -> bool:
    """检查指定 GEE API 是否已存在真 OGE 映射（one_to_one / one_to_many / many_to_one）

    用于去重：若已有真 OGE 算子映射，则不再导入 native_python 实现，
    避免同一 API 出现两条映射记录造成歧义

    Args:
        conn: 数据库连接
        gee_api_id: GEE API 内部 id

    Returns:
        bool: 已存在真 OGE 映射返回 True
    """
    cursor = conn.execute(
        """SELECT id FROM operator_mapping
           WHERE gee_api_id = ? AND mapping_type IN ('one_to_one', 'one_to_many', 'many_to_one')""",
        (gee_api_id,)
    )
    return cursor.fetchone() is not None


def import_native_python_implementations(conn: sqlite3.Connection) -> int:
    """从 Python 函数文件导入 native_python 类型的映射

    使用 GEE_PYTHON_FUNCTIONS 和 UNMATCHED_API_FUNCTIONS 字典作为权威映射源，
    确保 GEE API 名与 Python 函数的对应关系准确无误。

    去重规则：
    - 若 GEE API 在 Excel 中已有真 OGE 映射（one_to_one/one_to_many/many_to_one），
      则不导入 native_python，以 OGE 映射为准
    - 若 GEE API 在 Excel 中是伪映射或无映射，则导入 native_python

    Args:
        conn: 数据库连接

    Returns:
        int: 导入的记录数
    """
    registry = _load_python_function_registry()
    print(f"  - Python 函数注册表共 {len(registry)} 个 GEE API")

    total_count = 0
    skipped_has_oge = 0
    skipped_no_source = 0

    for gee_api_name, (source_file, func_name) in registry.items():
        # 确保 GEE API 记录存在
        gee_id = _ensure_gee_api_exists(conn, gee_api_name)

        # 去重：已有真 OGE 映射则跳过
        if _has_real_oge_mapping(conn, gee_id):
            skipped_has_oge += 1
            continue

        # 检查是否已存在 native_python 映射
        existing = conn.execute(
            """SELECT id FROM operator_mapping
               WHERE gee_api_id = ? AND mapping_type = 'native_python'""",
            (gee_id,)
        ).fetchone()
        if existing:
            continue

        # 提取函数源代码
        py_file_path = os.path.join(PROJECT_ROOT, source_file)
        func_source = _extract_function_source(py_file_path, func_name)
        if not func_source:
            print(f"[WARN] 未找到函数源代码: {source_file}::{func_name}")
            skipped_no_source += 1
            continue

        # 插入 native_python 映射
        conn.execute(
            """INSERT INTO operator_mapping
               (gee_api_id, oge_api_id, mapping_type, combo_steps, native_python_code,
                confidence, llm_judge_detail, verification_status, review_comment)
               VALUES (?, NULL, 'native_python', NULL, ?, ?, ?, ?, ?)""",
            (gee_id, func_source, 0.9000,
             json.dumps({"source": source_file, "function_name": func_name}, ensure_ascii=False),
             'manually_approved', f'Python 实现来自 {source_file}::{func_name}')
        )
        total_count += 1

    conn.commit()
    print(f"[OK] operator_mapping (Python 实现) 已导入 {total_count} 条记录"
          f"（跳过 {skipped_has_oge} 条已有 OGE 映射，{skipped_no_source} 条无源代码）")
    return total_count


# ============================================================
# 主入口
# ============================================================

def build_database(db_path: str = DB_PATH, force: bool = True) -> None:
    """完整构建数据库：建表 + 导入所有数据

    Args:
        db_path: 数据库文件路径
        force: 是否强制重建
    """
    print("=" * 70)
    print("GEE-OGE 算子映射知识库 - 数据库构建开始")
    print("=" * 70)

    # 1. 初始化数据库
    print("\n[1/5] 初始化数据库...")
    init_database(db_path, force)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        # 2. 导入类映射
        print("\n[2/5] 导入 class_mapping...")
        import_class_mapping(conn)

        # 3. 导入 GEE API 信息
        print("\n[3/5] 导入 gee_api_info...")
        import_gee_api_info(conn)

        # 4. 导入 OGE API 信息
        print("\n[4/5] 导入 oge_api_info...")
        import_oge_api_info(conn)

        # 5. 导入算子映射关系
        print("\n[5/5] 导入 operator_mapping...")
        print("  - 从 Excel 映射表导入...")
        excel_count = import_operator_mapping_from_xlsx(conn)
        print("  - 从 Python 实现文件导入...")
        py_count = import_native_python_implementations(conn)

        # 统计结果
        print("\n" + "=" * 70)
        print("数据库构建完成！统计信息：")
        print("=" * 70)

        stats = {
            'class_mapping': "SELECT COUNT(*) FROM class_mapping",
            'gee_api_info': "SELECT COUNT(*) FROM gee_api_info",
            'oge_api_info': "SELECT COUNT(*) FROM oge_api_info",
            'operator_mapping (total)': "SELECT COUNT(*) FROM operator_mapping",
            '  - one_to_one': "SELECT COUNT(*) FROM operator_mapping WHERE mapping_type='one_to_one'",
            '  - one_to_many': "SELECT COUNT(*) FROM operator_mapping WHERE mapping_type='one_to_many'",
            '  - many_to_one': "SELECT COUNT(*) FROM operator_mapping WHERE mapping_type='many_to_one'",
            '  - native_python': "SELECT COUNT(*) FROM operator_mapping WHERE mapping_type='native_python'",
            '  - missing': "SELECT COUNT(*) FROM operator_mapping WHERE mapping_type='missing'",
        }

        for name, sql in stats.items():
            cursor = conn.execute(sql)
            count = cursor.fetchone()[0]
            print(f"  {name}: {count}")

    finally:
        conn.close()

    print(f"\n[OK] 数据库文件: {db_path}")


if __name__ == '__main__':
    build_database()
