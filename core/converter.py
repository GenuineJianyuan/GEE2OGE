"""基于规则的 GEE ↔ OGE 代码转换引擎。

从主项目 ``case_study_pipeline.py`` 的 step4 代码生成逻辑中提取核心算法，
去除 LLM 相关代码，保留纯规则引擎的骨架生成能力。

转换策略：
- 先做静态分析提取 API 和步骤
- 再用映射库匹配 API
- 最后按步骤生成 OGE 代码骨架（含占位符和 TODO 标记）
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .analysis import analyze_gee, extract_gee_apis
from .mapping import MappingLibrary, MatchResult


def _oge_process_call(name: str, operands: str = '...') -> str:
    """生成 OGE getProcess 调用模板。

    Args:
        name: OGE 算子名称
        operands: 参数字符串

    Returns:
        str: OGE 调用代码
    """
    return f'service.getProcess("{name}").execute({operands})'


def _generate_step_code(
    gee_code: str,
    step_apis: List[str],
    api_lookup: Dict[str, Dict[str, Any]],
) -> Tuple[str, str]:
    """为单个步骤生成 OGE 代码骨架。

    根据 API 查找表中的映射信息，生成对应的 OGE 调用占位代码。
    支持 one_to_one、one_to_many、many_to_one、many_to_many、
    native_python 等多种映射类型。

    Args:
        gee_code: GEE 代码片段
        step_apis: 该步骤用到的 GEE API 列表
        api_lookup: API 查找表（GEE API → 映射信息）

    Returns:
        Tuple[str, str]: (OGE 代码, 可行性标签)
    """
    # 检查该步骤是否完全没有匹配的 API
    missing_in_step = [
        api for api in step_apis
        if api not in api_lookup or api_lookup[api].get('mapping_type') == 'missing'
    ]

    if missing_in_step and not any(api in api_lookup for api in step_apis):
        oge_code = "# [BLOCKED] 缺失 API 无法实现\n"
        oge_code += f"# 缺失的 GEE API: {', '.join(missing_in_step)}\n"
        return oge_code, 'infeasible'

    oge_lines: List[str] = []
    feasibility = 'direct_feasible'

    # 已生成的组合映射（避免重复生成）
    generated_combos: set = set()

    # 遍历 API 生成占位代码
    for gee_api in step_apis:
        if gee_api not in api_lookup:
            oge_lines.append(f"# [MISSING] {gee_api} - 未找到对应 OGE API")
            feasibility = 'partial_feasible'
            continue

        mapping = api_lookup[gee_api]
        mapping_type = mapping.get('mapping_type', 'missing')
        oge_api_names = mapping.get('oge_api_names', [])

        if mapping_type == 'native_python':
            # Python 原生实现
            native_code = mapping.get('python_implementation', '')
            if native_code:
                oge_lines.append(f"# Python 原生实现: {gee_api}")
                oge_lines.append(native_code)
            else:
                note = mapping.get('note', '') or mapping.get('remark', '')
                oge_lines.append(f"# Python 原生实现: {gee_api} ({note})")
            oge_lines.append("")

        elif mapping_type in ('many_to_one', 'many_to_many'):
            # 组合映射：只生成一次（通过组合名去重）
            combo_name = mapping.get('mapping_name', gee_api)
            if combo_name in generated_combos:
                continue
            generated_combos.add(combo_name)

            oge_api_str = ' + '.join(oge_api_names) if oge_api_names else 'unknown'
            oge_lines.append(f"# 组合映射: {combo_name}")
            oge_lines.append(f"# GEE 组合 → OGE: {oge_api_str}")
            remark = mapping.get('remark', '') or mapping.get('note', '')
            if remark:
                oge_lines.append(f"# 说明: {remark}")
            for oge_api in oge_api_names:
                oge_lines.append(f'result = {_oge_process_call(oge_api)}')
            oge_lines.append("")

        else:
            # one_to_one / one_to_many 等
            oge_api_str = ' + '.join(oge_api_names) if oge_api_names else 'unknown'
            oge_lines.append(f"# {gee_api} → {oge_api_str}")
            for oge_api in oge_api_names:
                oge_lines.append(f'result = {_oge_process_call(oge_api)}')
            oge_lines.append("")

    return '\n'.join(oge_lines), feasibility


def convert_gee_to_oge(
    gee_code: str,
    library: MappingLibrary,
) -> Dict[str, Any]:
    """将 GEE 代码转换为 OGE 代码骨架。

    执行完整流程：静态分析 → API 匹配 → 按步骤生成代码。

    Args:
        gee_code: GEE JavaScript 代码
        library: 映射库实例

    Returns:
        Dict: 包含 code, analysis, match_result, step_results 的字典
    """
    # 1. 静态分析
    analysis = analyze_gee(gee_code)

    # 2. API 匹配（使用完整匹配算法，含组合映射）
    match_result = library.match_apis(analysis['apis'])

    # 3. 生成代码骨架
    lines: List[str] = [
        '# 由 GEE-OGE 核心转换器生成',
        'import oge',
        '',
        'oge.initialize()',
        'service = oge.Service()',
        '',
    ]

    step_results: List[Dict[str, Any]] = []
    api_lookup = match_result.api_lookup

    for idx, step in enumerate(analysis['steps']):
        step_desc = step['description']
        step_code = step['code']
        step_index = idx + 1

        lines.append(f"# --- 步骤 {step_index}: {step_desc} ---")

        # 提取该步骤的 API
        step_apis = extract_gee_apis(step_code, analysis['variable_types'])

        # 生成该步骤的 OGE 代码
        oge_step_code, feasibility = _generate_step_code(
            step_code, step_apis, api_lookup
        )

        lines.append(oge_step_code)
        lines.append("")

        step_results.append({
            'step_index': step_index,
            'step_description': step_desc,
            'gee_code': step_code,
            'oge_code': oge_step_code,
            'feasibility': feasibility,
            'step_apis': step_apis,
        })

    # 判断整体可行性
    feasibility_flags = [s['feasibility'] for s in step_results]
    if any(f == 'infeasible' for f in feasibility_flags):
        overall_feasibility = 'infeasible'
    elif any(f == 'partial_feasible' for f in feasibility_flags):
        overall_feasibility = 'partial_feasible'
    else:
        overall_feasibility = 'full_feasible'

    return {
        'code': '\n'.join(lines),
        'analysis': analysis,
        'match_result': match_result.to_dict(),
        'step_results': step_results,
        'overall_feasibility': overall_feasibility,
    }


def convert_oge_to_gee(
    oge_code: str,
    library: MappingLibrary,
) -> Dict[str, Any]:
    """将 OGE 代码反向转换为 GEE 代码草稿。

    扫描 OGE 代码中的 getProcess 调用，查找对应的 GEE 映射，
    生成带注释的 GEE 转换草稿。

    Args:
        oge_code: OGE Python 代码
        library: 映射库实例

    Returns:
        Dict: 包含 code, oge_processes, missing_processes 的字典
    """
    process_names = re.findall(r'getProcess\(\s*["\']([^"\']+)["\']\s*\)', oge_code)

    lines = [
        '// 由 GEE-OGE 核心转换器生成',
        '// 运行前请补充数据源和参数。',
        '',
    ]

    missing: List[str] = []
    for process in process_names:
        reverse = library.find_oge(process)
        if not reverse:
            missing.append(process)
            lines.append(f'// TODO: 未找到 OGE 算子 {process} 对应的 GEE 映射')
            continue

        gee_names = ', '.join(item.gee_api for item in reverse)
        lines.append(f'// OGE {process} → {gee_names}')
        lines.append(f'// 替换为对应的 GEE 调用: {gee_names}')
        lines.append('')

    return {
        'code': '\n'.join(lines),
        'oge_processes': process_names,
        'missing_processes': missing,
    }


def build_mapping_context_for_llm(
    match_result: MatchResult,
) -> str:
    """构建映射上下文字符串（供 LLM 代码生成时参考）。

    从匹配结果中提取组合映射和一对一映射信息，
    格式化为易读的文本。

    Args:
        match_result: 匹配结果

    Returns:
        str: 格式化后的映射上下文文本
    """
    lines: List[str] = []
    api_lookup = match_result.api_lookup

    # 组合映射（放在最前面，强调最高优先级）
    if match_result.combo_matches:
        lines.append("## 组合映射（最高优先级！many_to_one / many_to_many）")
        lines.append("重要：如果 GEE 代码符合以下组合模式，请直接使用对应的 OGE 算子！")
        lines.append("")
        for combo in match_result.combo_matches:
            combo_dict = combo.to_dict() if hasattr(combo, 'to_dict') else combo
            gee_apis = ' + '.join(combo_dict.get('gee_apis', []))
            oge_apis = ' + '.join(combo_dict.get('oge_apis', []))
            name = combo_dict.get('mapping_name', '')
            lines.append(f"### {name}")
            lines.append(f"- GEE 组合: {gee_apis}")
            lines.append(f"- OGE 算子: {oge_apis}")
            remark = combo_dict.get('remark', '') or combo_dict.get('note', '')
            if remark:
                lines.append(f"- 说明: {remark}")
            gee_example = combo_dict.get('gee_example', '')
            oge_example = combo_dict.get('oge_example', '')
            if gee_example or oge_example:
                lines.append("- 调用示例:")
                if gee_example:
                    lines.append(f"  GEE:")
                    lines.append(f"    ```javascript")
                    lines.append(f"    {gee_example}")
                    lines.append(f"    ```")
                if oge_example:
                    lines.append(f"  OGE:")
                    lines.append(f"    ```python")
                    lines.append(f"    {oge_example}")
                    lines.append(f"    ```")
            lines.append("")
        lines.append("")

    # 一对一映射
    one_to_ones = [
        d for d in match_result.dedup_details
        if d.get('mapping_type') == 'one_to_one' and d.get('status') == 'matched'
    ]
    if one_to_ones:
        lines.append("## 一对一映射（one_to_one）")
        seen = set()
        for detail in one_to_ones:
            gee = detail.get('gee_api', '')
            if gee in seen:
                continue
            seen.add(gee)
            oge = detail.get('oge_api', '') or (
                ', '.join(detail.get('oge_api_names', []))
                if isinstance(detail.get('oge_api_names'), list) else ''
            )
            mapping_info = api_lookup.get(gee, {})
            gee_example = mapping_info.get('gee_example', '')
            oge_example = mapping_info.get('oge_example', '')
            lines.append(f"### {gee} → {oge}")
            if gee_example or oge_example:
                if gee_example:
                    lines.append(f"  GEE 示例:")
                    lines.append(f"    ```javascript")
                    lines.append(f"    {gee_example}")
                    lines.append(f"    ```")
                if oge_example:
                    lines.append(f"  OGE 示例:")
                    lines.append(f"    ```python")
                    lines.append(f"    {oge_example}")
                    lines.append(f"    ```")
        lines.append("")

    return '\n'.join(lines)
