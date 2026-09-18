"""代码迁移验证规则：输入校验、映射覆盖和输出质量检查。

从主项目中提取验证相关逻辑，提供纯规则的输入输出检查，
不执行代码，不依赖外部服务。
"""

from __future__ import annotations

import re
from typing import Dict, List

from .analysis import extract_gee_apis
from .mapping import MappingLibrary


def validate_gee_source(gee_code: str) -> List[Dict[str, str]]:
    """检测 GEE 源代码的常见问题（不执行 JavaScript）。

    检查项：
    - 空代码
    - 大括号不平衡
    - 圆括号不平衡
    - 方括号不平衡
    - 未识别到 GEE API 调用
    - 存在明显的语法错误标记

    Args:
        gee_code: GEE JavaScript 代码

    Returns:
        List[Dict]: 问题列表，每个元素包含 severity 和 message
    """
    issues: List[Dict[str, str]] = []

    if not gee_code.strip():
        return [{'severity': 'error', 'message': '源代码为空。'}]

    # 括号平衡检查
    if gee_code.count('{') != gee_code.count('}'):
        issues.append({
            'severity': 'warning',
            'message': '检测到大括号不平衡。',
        })

    if gee_code.count('(') != gee_code.count(')'):
        issues.append({
            'severity': 'warning',
            'message': '检测到圆括号不平衡。',
        })

    if gee_code.count('[') != gee_code.count(']'):
        issues.append({
            'severity': 'warning',
            'message': '检测到方括号不平衡。',
        })

    # 引号平衡检查（粗略）
    # 简单计算单双引号数量是否为偶数
    single_quotes = gee_code.count("'")
    double_quotes = gee_code.count('"')
    if single_quotes % 2 != 0:
        issues.append({
            'severity': 'warning',
            'message': '检测到单引号数量为奇数，可能存在字符串未闭合。',
        })
    if double_quotes % 2 != 0:
        issues.append({
            'severity': 'warning',
            'message': '检测到双引号数量为奇数，可能存在字符串未闭合。',
        })

    # GEE API 识别检查
    apis = extract_gee_apis(gee_code)
    if not apis:
        issues.append({
            'severity': 'warning',
            'message': '未识别到任何 GEE API 调用。',
        })

    # 检查是否有 ee. 开头的构造调用
    if not re.search(r'\bee\.', gee_code):
        issues.append({
            'severity': 'info',
            'message': '代码中未发现 ee. 前缀的调用，可能不是标准 GEE 代码。',
        })

    return issues


def validate_mapping_coverage(
    gee_code: str,
    library: MappingLibrary,
) -> Dict[str, Any]:
    """检查 GEE 代码中的 API 在映射库中的覆盖情况。

    Args:
        gee_code: GEE JavaScript 代码
        library: 映射库实例

    Returns:
        Dict: 包含 total, matched, missing, match_rate, mapped_apis, missing_apis 的字典
    """
    apis = extract_gee_apis(gee_code)
    report = library.match_report(apis)
    report['mapped_apis'] = [api for api in apis if library.find_gee(api)]
    report['total_unique'] = len(set(apis))
    return report


def validate_oge_workflow(oge_code: str) -> List[Dict[str, str]]:
    """检查生成的 OGE 工作流代码的常见问题。

    检查项：
    - 重复的 import oge 语句
    - 重复的 oge.initialize() 调用
    - 重复的 oge.Service() 初始化
    - 存在占位符（... 或 TODO）
    - 缺少必要的初始化代码

    Args:
        oge_code: OGE Python 代码

    Returns:
        List[Dict]: 问题列表
    """
    issues: List[Dict[str, str]] = []

    # 重复 import 检查
    import_count = len(re.findall(r'\bimport\s+oge\b', oge_code))
    if import_count > 1:
        issues.append({
            'severity': 'warning',
            'message': f'检测到 {import_count} 处 oge import 语句，存在重复。',
        })

    # 初始化重复检查
    init_count = len(re.findall(r'\boge\.initialize\(\)', oge_code))
    if init_count > 1:
        issues.append({
            'severity': 'warning',
            'message': f'检测到 {init_count} 处 oge.initialize() 调用，存在重复。',
        })

    service_count = len(re.findall(r'\bservice\s*=\s*oge\.Service\(\)', oge_code))
    if service_count > 1:
        issues.append({
            'severity': 'warning',
            'message': f'检测到 {service_count} 处 OGE service 初始化，存在重复。',
        })

    # 占位符检查
    if '...' in oge_code:
        issues.append({
            'severity': 'warning',
            'message': '工作流代码中包含 "..." 占位符，需要手动补充参数。',
        })

    if 'TODO' in oge_code or 'todo' in oge_code:
        issues.append({
            'severity': 'warning',
            'message': '工作流代码中包含 TODO 标记，需要手动完成。',
        })

    if '[MISSING]' in oge_code or '[BLOCKED]' in oge_code:
        issues.append({
            'severity': 'error',
            'message': '工作流代码中包含缺失/阻断的 API 标记，无法直接运行。',
        })

    # 缺少初始化检查
    if 'oge.initialize()' not in oge_code and 'oge.Service()' not in oge_code:
        if re.search(r'service\.getProcess\(', oge_code):
            issues.append({
                'severity': 'warning',
                'message': '使用了 service.getProcess 但未找到 oge.initialize() 和 service 初始化。',
            })

    return issues


def validate_mapping_consistency(library: MappingLibrary) -> List[Dict[str, str]]:
    """检查映射库内部的一致性问题。

    检查项：
    - 空 GEE API 名或 OGE API 名
    - one_to_one 映射但 OGE API 数量不为 1
    - many_to_one/many_to_many 映射但 GEE API 数量小于 2
    - 重复的 GEE API 映射（同类型重复）

    Args:
        library: 映射库实例

    Returns:
        List[Dict]: 问题列表
    """
    issues: List[Dict[str, str]] = []
    mappings = library.get_all_mappings()

    gee_api_count: Dict[str, int] = {}

    for i, mapping in enumerate(mappings):
        gee_apis = mapping.gee_api_names or [mapping.gee_api]
        oge_apis = mapping.oge_apis
        mtype = mapping.mapping_type

        # 空 API 名检查
        if not gee_apis or all(not g for g in gee_apis):
            issues.append({
                'severity': 'error',
                'message': f'第 {i + 1} 条映射缺少 GEE API 名称。',
            })
            continue

        # 映射类型与 API 数量一致性检查
        if mtype == 'one_to_one' and len(oge_apis) != 1:
            issues.append({
                'severity': 'warning',
                'message': f'映射 {gee_apis[0]} 类型为 one_to_one 但 OGE API 数量为 {len(oge_apis)}。',
            })

        if mtype in ('many_to_one', 'many_to_many') and len(gee_apis) < 2:
            issues.append({
                'severity': 'warning',
                'message': f'映射 {mapping.mapping_name or gee_apis[0]} 类型为 {mtype} 但 GEE API 数量小于 2。',
            })

        # 重复映射检查
        for gee_api in gee_apis:
            if mtype == 'one_to_one':
                gee_api_count[gee_api] = gee_api_count.get(gee_api, 0) + 1

    for gee_api, count in gee_api_count.items():
        if count > 1:
            issues.append({
                'severity': 'info',
                'message': f'GEE API {gee_api} 存在 {count} 条 one_to_one 映射。',
            })

    return issues
