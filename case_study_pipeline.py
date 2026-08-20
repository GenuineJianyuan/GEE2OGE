"""
GEE → OGE 迁移流水线 - Case Study 6 步接口模块

根据《GEE-OGE整体框架》和《case_study_demo.html》设计，
实现完整的 6 步流水线接口，每一步都有对应的 Python 函数：

Step 1: Semantic Abstraction (语义抽象和步骤分解)
Step 2: API Requirement Elicitation (API 需求识别)
Step 3: GEE-to-OGE API Matching (GEE 到 OGE API 匹配)
Step 4: Step-Level OGE Codegen (步骤级 OGE 代码生成)
Step 5: Feasibility Completion (可行性补全)
Step 6: Workflow Reconstruction (工作流重构)

外加统一入口：run_pipeline(gee_code)

注意：本模块的"语义抽象"和"API 识别"步骤使用规则解析（AST + 正则）实现，
不依赖大模型。在实际生产环境中，可替换为调用本地大模型的实现，
接口签名保持一致即可。
"""

import ast
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# 添加项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from db_dao import GeeOgeDao, DEFAULT_DB_PATH  # noqa: E402

# ============================================================
# 数据类定义 - 流水线各步骤的输入输出
# ============================================================

@dataclass
class Step1Result:
    """步骤 1 输出：语义抽象结果

    Attributes:
        task_goal: 一句话核心任务目标
        workflow_steps: 有序的处理步骤描述列表
        key_params: 关键参数（时空范围、数据源、指数名等）
        raw_snippets: 按 step 分组的代码片段
        llm_analysis: LLM 完整分析结果（含 task_goal/steps/variable_types/
                      api_calls/dataflow/suggestions/key_params），供后续步骤复用
    """
    task_goal: str = ''
    workflow_steps: List[str] = field(default_factory=list)
    key_params: Dict[str, Any] = field(default_factory=dict)
    raw_snippets: List[Dict[str, str]] = field(default_factory=list)
    llm_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_goal': self.task_goal,
            'workflow_steps': self.workflow_steps,
            'key_params': self.key_params,
            'raw_snippets': self.raw_snippets,
            'llm_analysis': self.llm_analysis,
        }


@dataclass
class Step2Result:
    """步骤 2 输出：API 需求清单

    Attributes:
        required_apis: 每个 step 依赖的 GEE API 全名列表
        step_descriptions: 每个 step 的描述文本
        step_codes: 每个 step 的原始 GEE 代码片段
        all_apis: 去重后的全量 GEE API 列表
        api_count: API 总数
    """
    required_apis: List[List[str]] = field(default_factory=list)  # 按 step 分组
    step_descriptions: List[str] = field(default_factory=list)  # 每个 step 的描述
    step_codes: List[str] = field(default_factory=list)  # 每个 step 的原始代码
    all_apis: List[str] = field(default_factory=list)  # 去重后
    api_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'required_apis': self.required_apis,
            'step_descriptions': self.step_descriptions,
            'step_codes': self.step_codes,
            'all_apis': self.all_apis,
            'api_count': self.api_count,
        }


@dataclass
class Step3Result:
    """步骤 3 输出：GEE → OGE API 匹配结果

    Attributes:
        match_details: 每个 API 的匹配详情
        match_rate: 匹配率 (0~1)
        matched_count: 已匹配数
        missing_count: 未匹配数
        missing_apis: 未匹配的 API 列表
    """
    match_details: List[Dict[str, Any]] = field(default_factory=list)
    match_rate: float = 0.0
    matched_count: int = 0
    missing_count: int = 0
    missing_apis: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'match_details': self.match_details,
            'match_rate': self.match_rate,
            'matched_count': self.matched_count,
            'missing_count': self.missing_count,
            'missing_apis': self.missing_apis,
        }


@dataclass
class Step4Result:
    """步骤 4 输出：步骤级 OGE 代码生成结果

    Attributes:
        step_codes: 每个 workflow step 的 OGE 代码片段
        feasibility_flags: 每个 step 的可行性标记
    """
    step_codes: List[Dict[str, str]] = field(default_factory=list)
    feasibility_flags: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'step_codes': self.step_codes,
            'feasibility_flags': self.feasibility_flags,
        }


@dataclass
class Step5Result:
    """步骤 5 输出：可行性补全结果

    Attributes:
        overall_feasible: 整体是否可行
        blocking_apis: 阻断性缺失 API 列表
        non_blocking_gaps: 非阻断性缺口列表
        rescue_suggestions: 修复建议
    """
    overall_feasible: bool = True
    blocking_apis: List[str] = field(default_factory=list)
    non_blocking_gaps: List[str] = field(default_factory=list)
    rescue_suggestions: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'overall_feasible': self.overall_feasible,
            'blocking_apis': self.blocking_apis,
            'non_blocking_gaps': self.non_blocking_gaps,
            'rescue_suggestions': self.rescue_suggestions,
        }


@dataclass
class Step6Result:
    """步骤 6 输出：工作流重构结果

    Attributes:
        oge_code: 完整可执行的 OGE 工作流代码
        missing_report: API 缺失报告（如有阻断性缺失）
        feasibility: 整体可行性标签
    """
    oge_code: str = ''
    missing_report: Optional[str] = None
    feasibility: str = 'full_feasible'  # full_feasible / partial_feasible / infeasible

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'oge_code': self.oge_code,
            'missing_report': self.missing_report,
            'feasibility': self.feasibility,
        }


@dataclass
class PipelineResult:
    """流水线完整结果对象"""
    success: bool = True
    step1: Optional[Step1Result] = None
    step2: Optional[Step2Result] = None
    step3: Optional[Step3Result] = None
    step4: Optional[Step4Result] = None
    step5: Optional[Step5Result] = None
    step6: Optional[Step6Result] = None
    match_rate: float = 0.0
    error: Optional[str] = None
    timing: Dict[str, float] = field(default_factory=dict)  # 每步耗时(秒)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'step1': self.step1.to_dict() if self.step1 else None,
            'step2': self.step2.to_dict() if self.step2 else None,
            'step3': self.step3.to_dict() if self.step3 else None,
            'step4': self.step4.to_dict() if self.step4 else None,
            'step5': self.step5.to_dict() if self.step5 else None,
            'step6': self.step6.to_dict() if self.step6 else None,
            'match_rate': self.match_rate,
            'error': self.error,
            'timing': self.timing,
        }


# ============================================================
# 流水线引擎
# ============================================================

class CaseStudyPipeline:
    """Case Study 6 步流水线引擎

    将 GEE 代码通过 6 步处理转换为 OGE 代码（或缺失报告）

    Attributes:
        dao: 数据访问对象
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """初始化流水线

        Args:
            db_path: SQLite 数据库路径
        """
        self.dao = GeeOgeDao(db_path)

    def close(self) -> None:
        """关闭资源"""
        self.dao.close()

    # ============================================================
    # Step 1: 语义抽象和步骤分解
    # ============================================================

    def step1_semantic_abstraction(self, gee_code: str, llm_service=None) -> Step1Result:
        """步骤 1：语义抽象和步骤分解

        将 GEE 代码拆解为有序的处理步骤，提取任务目标和关键参数。
        优先使用 LLM 进行语义拆分（在 analyze_gee_code 中完成），
        当 LLM 不可用或拆分结果覆盖率不足时回退到注释解析。

        拆分策略：
        1. 优先使用 LLM 返回的 steps 字段（按语义功能划分，已删除注释）
        2. 对 LLM 结果做行覆盖率校验：原始代码所有非注释行必须被覆盖
        3. 漏掉的行会追加到最后一个步骤，保证不遗漏任何代码
        4. 回退：以注释行（如 // Winter NDVI）为步骤分隔

        Args:
            gee_code: 原始 GEE 代码（JavaScript）
            llm_service: LLM 服务实例（可选，用于增强分析）

        Returns:
            Step1Result: 语义抽象结果
        """
        result = Step1Result()
        llm_analysis = None

        # ========== 优先使用 LLM 进行语义拆分 ==========
        if llm_service and llm_service.is_available():
            try:
                llm_analysis = llm_service.analyze_gee_code(gee_code)
                if llm_analysis:
                    # 保存完整 LLM 分析结果，供 app.py 及后续步骤复用，避免重复调用
                    result.llm_analysis = llm_analysis

                    llm_task_goal = llm_analysis.get('task_goal', '')
                    llm_steps = llm_analysis.get('steps', []) or []

                    if llm_task_goal:
                        result.task_goal = llm_task_goal

                    if llm_steps:
                        # 构建 raw_snippets
                        for step in llm_steps:
                            desc = (step.get('description') or '').strip() or '未命名步骤'
                            code = (step.get('code') or '').strip()
                            if code:
                                result.workflow_steps.append(desc)
                                result.raw_snippets.append({
                                    'step_description': desc,
                                    'code_snippet': code
                                })

                        # 行覆盖率校验：检查是否有遗漏的代码行
                        self._verify_and_fix_step_coverage(gee_code, result)

                        # 如果校验后仍有步骤，使用 LLM 结果
                        if result.raw_snippets:
                            # 提取关键参数（传入 LLM 分析结果以增强提取）
                            result.key_params = self._extract_key_params(gee_code, llm_analysis)
                            return result

            except Exception as e:
                # LLM 分析失败时静默回退到注释解析
                print(f'[Step1] LLM 拆分失败，回退到注释解析: {e}')

        # ========== 回退：按注释行拆分 ==========
        return self._fallback_split_by_comments(gee_code, result, llm_analysis)

    @staticmethod
    def _verify_and_fix_step_coverage(gee_code: str, result: 'Step1Result') -> None:
        """校验 LLM 拆分结果的代码覆盖率，补回遗漏的代码行

        比较原始代码（去注释去空行）与 LLM 步骤中的代码行，
        将遗漏的行追加到最后一个步骤，保证不遗漏任何代码。

        Args:
            gee_code: 原始 GEE 代码
            result: Step1Result，会就地修改
        """
        if not result.raw_snippets:
            return

        # 1. 提取原始代码的所有非注释、非空行（归一化后用于比较）
        original_lines = []
        for line in gee_code.splitlines():
            stripped = line.strip()
            # 跳过空行
            if not stripped:
                continue
            # 跳过纯注释行
            if stripped.startswith('//'):
                continue
            # 跳过块注释的行（简单处理）
            if stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('*/'):
                continue
            original_lines.append(stripped)

        # 2. 提取 LLM 步骤中的所有代码行（归一化后）
        llm_lines_set = set()
        for snippet in result.raw_snippets:
            code = snippet.get('code_snippet', '')
            for line in code.splitlines():
                stripped = line.strip()
                if stripped:
                    llm_lines_set.add(stripped)

        # 3. 找出遗漏的行（原始代码中有，但 LLM 步骤中没有的）
        missing_lines = []
        for line in original_lines:
            if line not in llm_lines_set:
                missing_lines.append(line)

        # 4. 如果有遗漏，追加到最后一个步骤
        if missing_lines:
            last_snippet = result.raw_snippets[-1]
            existing_code = last_snippet.get('code_snippet', '')
            supplement_code = '\n'.join(missing_lines)
            if existing_code:
                last_snippet['code_snippet'] = existing_code + '\n' + supplement_code
            else:
                last_snippet['code_snippet'] = supplement_code
            print(f'[Step1] 发现 {len(missing_lines)} 行遗漏代码，已补到最后一个步骤')

    def _fallback_split_by_comments(
        self, gee_code: str, result: 'Step1Result', llm_analysis: Optional[Dict[str, Any]]
    ) -> 'Step1Result':
        """回退方案：按注释行拆分步骤

        当 LLM 不可用或拆分失败时使用此方法。
        以分隔符式注释或单独注释行作为步骤边界。

        Args:
            gee_code: 原始 GEE 代码
            result: 已部分填充的 Step1Result
            llm_analysis: LLM 分析结果（可选，用于提取 task_goal）

        Returns:
            Step1Result: 拆分结果
        """
        lines = gee_code.splitlines()
        single_comment_pattern = re.compile(r'^\s*//\s*(.+?)\s*$')

        # 如果 LLM 提供了 task_goal，用作默认步骤描述
        llm_step_desc = None
        if llm_analysis:
            llm_task_goal = llm_analysis.get('task_goal', '')
            api_calls = llm_analysis.get('api_calls', [])
            if llm_task_goal:
                llm_step_desc = llm_task_goal
            if api_calls:
                llm_step_desc = f"{llm_task_goal or '代码执行'} ({len(api_calls)} 个 API 调用)"

        current_step_desc: Optional[str] = None
        current_step_lines: List[str] = []
        step_groups: List[Tuple[str, List[str]]] = []

        def _flush_current():
            """保存当前步骤"""
            nonlocal current_step_desc, current_step_lines
            if current_step_desc is not None and current_step_lines:
                non_empty = [l for l in current_step_lines if l.strip()]
                if non_empty:
                    step_groups.append((current_step_desc, current_step_lines))
            current_step_desc = None
            current_step_lines = []

        for line in lines:
            if not line.strip():
                if current_step_lines:
                    current_step_lines.append(line)
                continue

            comment_match = single_comment_pattern.match(line)
            if comment_match:
                comment_text = comment_match.group(1).strip()
                if self._is_pure_separator(comment_text):
                    _flush_current()
                    continue
                cleaned = re.sub(r'[-=#!]{2,}', '', comment_text).strip()
                if cleaned:
                    _flush_current()
                    current_step_desc = cleaned
                    current_step_lines = []
                else:
                    _flush_current()
                continue

            if current_step_desc is None:
                current_step_desc = llm_step_desc or 'Code Execution'
            current_step_lines.append(line)

        _flush_current()

        if not step_groups:
            step_groups.append(('Whole script', lines))

        for desc, code_lines in step_groups:
            snippet = '\n'.join(code_lines).strip()
            if snippet:
                result.workflow_steps.append(desc)
                result.raw_snippets.append({
                    'step_description': desc,
                    'code_snippet': snippet
                })

        if not result.task_goal and result.workflow_steps:
            result.task_goal = f"Task decomposed into {len(result.workflow_steps)} steps: " + \
                               "; ".join(result.workflow_steps[:3])
            if len(result.workflow_steps) > 3:
                result.task_goal += "; ..."

        result.key_params = self._extract_key_params(gee_code, llm_analysis)
        return result

    @staticmethod
    def _is_pure_separator(text: str) -> bool:
        """判断注释文本是否为纯装饰分隔线

        纯分隔线特征：去掉所有 -、=、#、!、空格后为空字符串
        例如 "-----"、"====="、"#####"、"--- --- ---" 都是纯分隔线
        "Winter bands" 不是分隔线，"Winter bands -----" 也不是（有实际内容）

        Args:
            text: 注释内容（已去掉 // 前缀）

        Returns:
            bool: 是纯分隔线返回 True
        """
        # 去掉所有装饰符和空格
        cleaned = re.sub(r'[-=#!\s]', '', text)
        return len(cleaned) == 0

    @staticmethod
    def _extract_key_params(gee_code: str, llm_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从 GEE 代码中提取关键参数

        提取内容：
        - 数据源 ID（如 'LANDSAT/LC08/C02/T1_TOA/...'）
        - 波段名（如 'B4', 'B5'）
        - 指数名（如 NDVI, GNDVI, NDMI）
        - 坐标（如 setCenter、Geometry.Point 的参数）
        - 日期范围
        - 属性名和值
        - 过滤条件
        - 变量定义

        Args:
            gee_code: GEE 代码
            llm_analysis: LLM 分析结果（可选，用于增强参数提取）

        Returns:
            Dict: 关键参数字典
        """
        params: Dict[str, Any] = {}

        # 提取数据源 ID
        dataset_pattern = re.compile(r"ee\.Image(?:Collection)?\(['\"]([^'\"]+)['\"]\)")
        datasets = dataset_pattern.findall(gee_code)
        if datasets:
            params['datasets'] = list(set(datasets))

        # 提取波段名
        band_pattern = re.compile(r"\.select\(['\"]([^'\"]+)['\"]\)")
        bands = band_pattern.findall(gee_code)
        if bands:
            params['bands'] = list(set(bands))

        # 提取指数名（从 rename 或变量名推断）
        rename_pattern = re.compile(r"\.rename\(['\"]([^'\"]+)['\"]\)")
        indices = rename_pattern.findall(gee_code)
        if indices:
            params['indices'] = list(set(indices))

        # 提取 setCenter 坐标
        center_pattern = re.compile(r"Map\.setCenter\(([\d.\-]+),\s*([\d.\-]+),\s*(\d+)\)")
        center_match = center_pattern.search(gee_code)
        if center_match:
            params['map_center'] = {
                'lng': float(center_match.group(1)),
                'lat': float(center_match.group(2)),
                'zoom': int(center_match.group(3))
            }

        # 提取 Geometry.Point 坐标
        point_pattern = re.compile(r"ee\.Geometry\.Point\(\[([\d.\-]+),\s*([\d.\-]+)\]\)")
        points = point_pattern.findall(gee_code)
        if points:
            params['geometry_points'] = [
                {'lng': float(lng), 'lat': float(lat)}
                for lng, lat in points
            ]

        # 提取日期字符串
        date_pattern = re.compile(r"['\"](\d{4}-\d{2}-\d{2})['\"]")
        dates = date_pattern.findall(gee_code)
        if dates:
            params['dates'] = sorted(set(dates))

        # 提取日期范围过滤
        date_filter_pattern = re.compile(r"ee\.Filter\.date\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]\)")
        date_filters = date_filter_pattern.findall(gee_code)
        if date_filters:
            params['date_filters'] = [
                {'start': start, 'end': end}
                for start, end in date_filters
            ]

        # 提取属性键值对（从 Feature 构造）
        prop_pattern = re.compile(r"\{\s*['\"]([^'\"]+)['\"]\s*:\s*([^,}]+)\}")
        properties = prop_pattern.findall(gee_code)
        if properties:
            params['properties'] = [
                {'key': key.strip('"').strip("'"), 'value': value.strip()}
                for key, value in properties
            ]

        # 提取方法调用（主要操作）
        method_pattern = re.compile(r"\.(\w+)\(")
        methods = method_pattern.findall(gee_code)
        # 过滤掉常见的链式方法
        common_methods = {'get', 'set', 'toDictionary', 'toList', 'toString'}
        significant_methods = [m for m in set(methods) if m not in common_methods]
        if significant_methods:
            params['operations'] = sorted(significant_methods)

        # 提取变量定义
        var_def_pattern = re.compile(r"(\w+)\s*=\s*ee\.(\w+(?:\.\w+)*)\(")
        var_defs = var_def_pattern.findall(gee_code)
        if var_defs:
            params['variable_definitions'] = [
                {'variable': var, 'type': f'ee.{type_path}'}
                for var, type_path in var_defs
            ]

        # 如果 LLM 分析结果中有更多参数，合并进去
        if llm_analysis:
            llm_params = llm_analysis.get('key_params', {})
            if llm_params and isinstance(llm_params, dict):
                for key, value in llm_params.items():
                    if key not in params:
                        params[key] = value

        # 如果没有提取到任何参数，添加说明
        if not params:
            params['note'] = '代码不包含典型参数（数据源、波段、坐标等），可能为纯逻辑操作代码'

        return params

    # ============================================================
    # Step 2: API 需求识别
    # ============================================================

    def step2_api_requirement(self, step1_result: Step1Result) -> Step2Result:
        """步骤 2：API 需求识别

        从每个步骤的代码片段中提取调用的 GEE API，
        并保存步骤描述和原始代码片段

        注意：变量类型推断基于全局代码（所有步骤合并），
        以支持跨步骤的变量类型追踪

        Args:
            step1_result: 步骤 1 的结果

        Returns:
            Step2Result: API 需求清单
        """
        result = Step2Result()
        all_apis_set = set()

        # 先对全部代码做全局变量类型推断
        # 合并所有步骤的代码片段，保证跨步骤变量类型可见
        full_code = '\n'.join(
            snippet['code_snippet'] for snippet in step1_result.raw_snippets
        )
        global_var_types = self._infer_variable_types(full_code)

        # 对每个步骤的代码片段提取 API（使用全局变量类型）
        for snippet_info in step1_result.raw_snippets:
            step_desc = snippet_info['step_description']
            code = snippet_info['code_snippet']
            apis = self._extract_gee_apis_with_types(code, global_var_types)

            # 保存 API 列表、步骤描述和原始代码
            result.required_apis.append(apis)
            result.step_descriptions.append(step_desc)
            result.step_codes.append(code)
            all_apis_set.update(apis)

        result.all_apis = sorted(all_apis_set)
        result.api_count = len(result.all_apis)
        return result

    @staticmethod
    def _extract_gee_apis_with_types(code: str, variable_types: Dict[str, str]) -> List[str]:
        """从代码片段中提取所有 GEE API 调用（使用外部传入的变量类型表）

        与 _extract_gee_apis 类似，但使用预先推断的全局变量类型，
        支持跨步骤的变量类型追踪

        Args:
            code: 代码片段
            variable_types: 变量类型字典（{变量名: GEE 类全名}）

        Returns:
            List[str]: GEE API 全名列表（去重）
        """
        apis = set()

        # 1. 匹配 ee.XXX( 形式的构造函数调用（如 ee.Image(...)、ee.FeatureCollection(...)）
        ctor_pattern = re.compile(r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*)\s*\(')
        for match in ctor_pattern.finditer(code):
            apis.add(match.group(1))

        # 2. 匹配 ee.XXX.yyy( 形式的直接调用（多级，如 ee.Algorithms.CannyEdgeDetector）
        api_pattern = re.compile(
            r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\s*\('
        )
        for match in api_pattern.finditer(code):
            apis.add(match.group(1))

        # 3. 匹配 Map.xxx( 形式
        map_pattern = re.compile(r'\b(Map\.[A-Za-z_][A-Za-z0-9_]*)\s*\(')
        for match in map_pattern.finditer(code):
            apis.add(match.group(1))

        # 4. 匹配 Export.xxx( 形式
        export_pattern = re.compile(r'\b(Export\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\(')
        for match in export_pattern.finditer(code):
            apis.add(match.group(1))

        # 5. 匹配 print( 形式
        if re.search(r'\bprint\s*\(', code):
            apis.add('print')

        # 6. 使用传入的变量类型表，识别变量.方法( 形式
        # 常见 Image/Feature/Collection 方法集合
        common_image_methods = {
            'select', 'subtract', 'add', 'multiply', 'divide', 'rename',
            'clip', 'mask', 'unmask', 'updateMask', 'where', 'and', 'or',
            'not', 'eq', 'gt', 'gte', 'lt', 'lte', 'abs', 'sqrt', 'pow',
            'log', 'exp', 'cos', 'sin', 'tan', 'min', 'max', 'sum',
            'mean', 'median', 'count', 'reduce', 'reduceRegion', 'reduceRegions',
            'sample', 'sampleRegions', 'classify', 'visualize', 'unitScale',
            'normalizedDifference', 'expression', 'bandNames', 'bandTypes',
            'set', 'get', 'toArray', 'toDouble', 'toFloat', 'toInt', 'toInt32',
            'addBands', 'selectBands', 'resample', 'reduceResolution',
            'reproject', 'cast', 'unmix', 'trim', 'convolve', 'focal_mean',
            'focal_max', 'focal_min', 'gradient', 'kernel',
        }
        common_feature_methods = {
            'set', 'get', 'geometry', 'area', 'length', 'perimeter',
            'buffer', 'bounds', 'centroid', 'contains', 'intersects',
            'withinDistance', 'distance', 'intersection', 'union',
            'difference', 'symmetricDifference', 'simplify', 'transform'
        }
        common_collection_methods = {
            'filter', 'filterDate', 'filterBounds', 'filterMetadata',
            'map', 'select', 'first', 'limit', 'sort', 'size', 'getInfo',
            'geometry', 'union', 'aggregate_array', 'aggregate_stats',
            'aggregate_count', 'aggregate_max', 'aggregate_min', 'aggregate_mean',
            'aggregate_sum', 'aggregate_product', 'reduceToImage', 'reduceToVectors',
            'randomColumn', 'style', 'merge', 'flatten', 'distinct', 'toList'
        }
        common_geometry_methods = {
            'buffer', 'bounds', 'centroid', 'contains', 'intersects',
            'withinDistance', 'distance', 'intersection', 'union',
            'difference', 'symmetricDifference', 'simplify', 'transform',
            'area', 'length', 'perimeter', 'coordinates', 'geodesic',
            'srid', 'type', 'geometry'
        }
        common_number_methods = {
            'add', 'subtract', 'multiply', 'divide', 'abs', 'sqrt', 'pow',
            'round', 'floor', 'ceil', 'toInt', 'toFloat', 'format',
            'lt', 'lte', 'gt', 'gte', 'eq', 'neq', 'and', 'or', 'not',
            'min', 'max', 'log', 'exp', 'sin', 'cos', 'tan'
        }
        common_string_methods = {
            'cat', 'slice', 'indexOf', 'toUpperCase', 'toLowerCase',
            'replace', 'split', 'length', 'regexpExtract'
        }
        common_date_methods = {
            'advance', 'difference', 'get', 'format', 'millis',
            'getRange', 'getRelative', 'unitDifference'
        }
        common_list_methods = {
            'get', 'map', 'iterate', 'slice', 'reverse', 'sort',
            'size', 'contains', 'indexOf', 'add', 'remove', 'set',
            'repeat', 'flatten', 'cat', 'reduce', 'sort_combined'
        }
        common_dictionary_methods = {
            'get', 'set', 'keys', 'values', 'size', 'contains',
            'rename', 'select'
        }

        # 遍历已知变量，匹配变量.方法( 和链式调用
        for var_name, gee_class in variable_types.items():
            # 单次调用：var.method(
            var_call_pattern = re.compile(
                rf'\b{re.escape(var_name)}\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            )
            for match in var_call_pattern.finditer(code):
                method = match.group(1)
                if gee_class == 'ee.Image' and method in common_image_methods:
                    apis.add(f'ee.Image.{method}')
                elif gee_class == 'ee.Feature' and method in common_feature_methods:
                    apis.add(f'ee.Feature.{method}')
                elif gee_class in ('ee.FeatureCollection', 'ee.ImageCollection') \
                        and method in common_collection_methods:
                    apis.add(f'{gee_class}.{method}')
                elif gee_class == 'ee.Geometry' and method in common_geometry_methods:
                    apis.add(f'ee.Geometry.{method}')
                elif gee_class == 'ee.Number' and method in common_number_methods:
                    apis.add(f'ee.Number.{method}')
                elif gee_class == 'ee.String' and method in common_string_methods:
                    apis.add(f'ee.String.{method}')
                elif gee_class == 'ee.Date' and method in common_date_methods:
                    apis.add(f'ee.Date.{method}')
                elif gee_class == 'ee.List' and method in common_list_methods:
                    apis.add(f'ee.List.{method}')
                elif gee_class == 'ee.Dictionary' and method in common_dictionary_methods:
                    apis.add(f'ee.Dictionary.{method}')

            # 链式调用：var.method1(...).method2(...)
            var_chain_pattern = re.compile(
                rf'\b{re.escape(var_name)}(?:\.[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))+'
            )
            for chain_match in var_chain_pattern.finditer(code):
                chain_text = chain_match.group(0)
                method_pattern = re.compile(r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
                for method_match in method_pattern.finditer(chain_text):
                    method = method_match.group(1)
                    if gee_class == 'ee.Image' and method in common_image_methods:
                        apis.add(f'ee.Image.{method}')
                    elif gee_class == 'ee.Feature' and method in common_feature_methods:
                        apis.add(f'ee.Feature.{method}')
                    elif gee_class in ('ee.FeatureCollection', 'ee.ImageCollection') \
                            and method in common_collection_methods:
                        apis.add(f'{gee_class}.{method}')
                    elif gee_class == 'ee.Geometry' and method in common_geometry_methods:
                        apis.add(f'ee.Geometry.{method}')
                    elif gee_class == 'ee.Number' and method in common_number_methods:
                        apis.add(f'ee.Number.{method}')
                    elif gee_class == 'ee.String' and method in common_string_methods:
                        apis.add(f'ee.String.{method}')
                    elif gee_class == 'ee.Date' and method in common_date_methods:
                        apis.add(f'ee.Date.{method}')
                    elif gee_class == 'ee.List' and method in common_list_methods:
                        apis.add(f'ee.List.{method}')
                    elif gee_class == 'ee.Dictionary' and method in common_dictionary_methods:
                        apis.add(f'ee.Dictionary.{method}')

        return sorted(apis)

    @staticmethod
    def _extract_gee_apis(code: str) -> List[str]:
        """从代码片段中提取所有 GEE API 调用（内部推断变量类型）

        兼容旧接口，内部调用 _extract_gee_apis_with_types

        Args:
            code: 代码片段

        Returns:
            List[str]: GEE API 全名列表（去重）
        """
        variable_types = CaseStudyPipeline._infer_variable_types(code)
        return CaseStudyPipeline._extract_gee_apis_with_types(code, variable_types)

    @staticmethod
    def _infer_variable_types(code: str) -> Dict[str, str]:
        """从代码中推断变量类型

        通过分析 var/let/const xxx = ee.Image(...) 等赋值语句，
        推断变量的 GEE 类类型。支持多级类名（如 ee.Geometry.LineString）。

        Args:
            code: 代码片段

        Returns:
            Dict[str, str]: {变量名: GEE 类全名}，如 {'winterImage': 'ee.Image'}
        """
        variable_types: Dict[str, str] = {}

        # 匹配 var/let/const xxx = ee.ImageClass(...) —— 支持多级类名
        # 例如：var winterImage = ee.Image('...')
        #       var fc = ee.FeatureCollection('...')
        #       var lineString = ee.Geometry.LineString([...])
        #       var polygon = ee.Geometry.Polygon([...])
        var_decl_pattern = re.compile(
            r'(?:var|let|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*'
            r'(ee\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*\('
        )
        for match in var_decl_pattern.finditer(code):
            var_name = match.group(1)
            gee_class = match.group(2)
            # 提取基础类名（前两级），如 ee.Geometry.LineString -> ee.Geometry
            # 这样在方法匹配时能正确归类
            parts = gee_class.split('.')
            if len(parts) >= 2:
                base_class = f'{parts[0]}.{parts[1]}'
            else:
                base_class = gee_class
            variable_types[var_name] = base_class

        # 处理赋值链：var x = ee.Image(...).select(...)
        # 此时 x 仍然是 ee.Image 类型（因为 select 返回 Image）
        # 这种情况通过保留第一个类名已经处理

        # 处理变量间赋值：var y = x（继承 x 的类型）
        var_assign_pattern = re.compile(
            r'(?:var|let|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[;\n]'
        )
        for match in var_assign_pattern.finditer(code):
            target_var = match.group(1)
            source_var = match.group(2)
            if source_var in variable_types and target_var not in variable_types:
                variable_types[target_var] = variable_types[source_var]

        # 处理变量运算结果：var z = x.subtract(y)（z 也是 ee.Image）
        # 通过识别 .method() 调用，推断返回值类型
        var_op_pattern = re.compile(
            r'(?:var|let|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*'
            r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        )
        # 方法返回值类型映射：{方法名: 返回的 GEE 类型}
        method_return_types = {
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
            # ee.Geometry 方法返回 ee.Geometry
            'buffer': 'ee.Geometry', 'bounds': 'ee.Geometry',
            'centroid': 'ee.Geometry', 'simplify': 'ee.Geometry',
            'transform': 'ee.Geometry', 'intersection': 'ee.Geometry',
            'union': 'ee.Geometry', 'difference': 'ee.Geometry',
            'symmetricDifference': 'ee.Geometry',
            # ee.Feature 方法返回 ee.Feature
            'geometry': 'ee.Geometry',
        }
        for match in var_op_pattern.finditer(code):
            target_var = match.group(1)
            source_var = match.group(2)
            method_name = match.group(3)
            if source_var in variable_types and target_var not in variable_types:
                source_class = variable_types[source_var]
                # 根据方法名推断返回类型
                if method_name in method_return_types:
                    return_type = method_return_types[method_name]
                    # 如果返回类型与源类型匹配，或返回类型是 ee.Geometry（通用类型）
                    if return_type == source_class or return_type == 'ee.Geometry':
                        variable_types[target_var] = return_type

        return variable_types

    # ============================================================
    # Step 3: GEE → OGE API 匹配
    # ============================================================

    def step3_api_matching(self, step2_result: Step2Result,
                            llm_service=None) -> Step3Result:
        """步骤 3：GEE → OGE API 匹配

        基于 DAO 查询本地知识库，为每个 GEE API 找到对应的 OGE 实现。
        当 LLM 可用时，对知识库未匹配的 API 调用 LLM 做语义匹配增强，
        将高置信度的 LLM 匹配结果补充进匹配列表，降低缺失率。

        Args:
            step2_result: 步骤 2 的结果
            llm_service: LLM 服务实例（可选，用于语义匹配增强）

        Returns:
            Step3Result: 匹配结果
        """
        result = Step3Result()

        match_info = self.dao.calculate_match_rate(step2_result.all_apis)
        result.match_details = match_info['details']

        # LLM 语义匹配增强：对知识库未匹配的 API，调用 LLM 推断对应 OGE API
        if llm_service and llm_service.is_available() and result.match_details:
            llm_rescued = 0
            for detail in result.match_details:
                if detail.get('status') != 'missing':
                    continue
                gee_api = detail.get('gee_api', '')
                if not gee_api:
                    continue
                try:
                    match_result = llm_service.match_gee_to_oge(gee_api)
                    if (match_result and match_result.get('matched')
                            and match_result.get('confidence', 0) >= 0.6):
                        # LLM 匹配成功，更新详情
                        detail['status'] = 'matched'
                        detail['mapping_type'] = 'llm_semantic'
                        detail['oge_api'] = match_result.get('oge_api')
                        detail['confidence'] = match_result.get('confidence')
                        detail['reasoning'] = match_result.get('reasoning')
                        llm_rescued += 1
                except Exception as e:
                    print(f'[Step3] LLM 语义匹配 {gee_api} 失败: {e}')
            if llm_rescued > 0:
                print(f'[Step3] LLM 语义匹配救回 {llm_rescued} 个 API')

        # 重新统计（LLM 增强后可能变化）
        total = len(result.match_details)
        matched = sum(1 for d in result.match_details if d.get('status') == 'matched')
        missing = total - matched
        result.matched_count = matched
        result.missing_count = missing
        result.match_rate = matched / total if total > 0 else 0.0
        result.missing_apis = [d['gee_api'] for d in result.match_details
                               if d.get('status') == 'missing']

        return result

    # ============================================================
    # Step 4: 步骤级 OGE 代码生成
    # ============================================================

    def step4_ocode_codegen(self, step1_result: Step1Result,
                            step2_result: Step2Result,
                            step3_result: Step3Result) -> Step4Result:
        """步骤 4：步骤级 OGE 代码生成

        根据匹配结果，为每个 workflow step 生成对应的 OGE 代码片段
        本实现使用规则模板生成，不依赖大模型

        Args:
            step1_result: 步骤 1 的结果
            step2_result: 步骤 2 的结果
            step3_result: 步骤 3 的结果

        Returns:
            Step4Result: 代码生成结果
        """
        result = Step4Result()

        # 构建 GEE API -> OGE API 的快速查找表
        api_lookup: Dict[str, Dict[str, Any]] = {}
        for detail in step3_result.match_details:
            gee_name = detail['gee_api']
            if detail['status'] == 'matched':
                mapping = self.dao.get_mapping_by_gee_name(gee_name)
                if mapping:
                    api_lookup[gee_name] = mapping

        # 为每个 step 生成代码
        for idx, (snippet_info, step_apis) in enumerate(
            zip(step1_result.raw_snippets, step2_result.required_apis)
        ):
            step_desc = snippet_info['step_description']
            code_snippet = snippet_info['code_snippet']

            # 生成 OGE 代码
            oge_code, feasibility = self._generate_oge_code_for_step(
                code_snippet, step_apis, api_lookup
            )

            result.step_codes.append({
                'step_index': idx + 1,
                'step_description': step_desc,
                'gee_code': code_snippet,
                'oge_code': oge_code,
                'feasibility': feasibility
            })
            result.feasibility_flags.append({
                'step_index': idx + 1,
                'step_description': step_desc,
                'feasibility': feasibility
            })

        return result

    def _generate_oge_code_for_step(
        self, gee_code: str, step_apis: List[str],
        api_lookup: Dict[str, Dict[str, Any]]
    ) -> Tuple[str, str]:
        """为单个步骤生成 OGE 代码（符合 oge_step_codegen.txt 规则）

        生成的代码遵循以下规范：
        1. 初始化骨架：oge.initialize() + service = oge.Service()
        2. 使用 service.getProcess("算子名").execute(位置参数) 调用算子
        3. 生成尽量完整具体的可执行代码，而非仅注释

        Args:
            gee_code: GEE 代码片段
            step_apis: 该步骤用到的 GEE API
            api_lookup: API 查找表

        Returns:
            Tuple[str, str]: (OGE 代码, 可行性标签)
        """
        # 检查该步骤是否有未匹配的 API
        missing_in_step = [
            api for api in step_apis
            if api not in api_lookup or api_lookup[api]['mapping_type'] == 'missing'
        ]

        if missing_in_step and not any(api in api_lookup for api in step_apis):
            # 所有 API 都未匹配
            oge_code = "# [BLOCKED] 缺失 API 无法实现\n"
            oge_code += "# 缺失的 GEE API: {}\n".format(', '.join(missing_in_step))
            return oge_code, 'infeasible'

        # 基于 API 类型生成代码
        oge_lines = []
        feasibility = 'direct_feasible'

        # 生成初始化骨架
        has_matched = any(api in api_lookup for api in step_apis)
        if has_matched:
            oge_lines.append("import oge")
            oge_lines.append("oge.initialize()")
            oge_lines.append("service = oge.Service()")
            oge_lines.append("")

        # 提取变量赋值信息用于生成更具体的代码
        var_assignments = self._extract_var_assignments(gee_code)

        for gee_api in step_apis:
            if gee_api not in api_lookup:
                oge_lines.append(f"# [MISSING] {gee_api} - 未找到对应 OGE API")
                feasibility = 'partial_feasible'
                continue

            mapping = api_lookup[gee_api]
            mapping_type = mapping.get('mapping_type', 'missing')

            if mapping_type == 'native_python':
                # Python 原生实现
                native_code = mapping.get('native_python_code', '')
                if native_code:
                    oge_lines.append(native_code)
                else:
                    oge_lines.append(f"# Python 原生实现: {gee_api}")
                    oge_lines.append("# 请根据具体需求补充实现代码")
                oge_lines.append("")

            elif mapping_type == 'one_to_one':
                oge_api = mapping.get('oge_api', {})
                if oge_api:
                    oge_api_name = oge_api.get('api_name', '')
                    # 根据算子类型生成更具体的调用代码
                    oge_lines.append(self._generate_api_call_code(
                        gee_api, oge_api_name, var_assignments, gee_code
                    ))
                else:
                    oge_lines.append(f"# 映射到 OGE API: {gee_api}")

            elif mapping_type == 'one_to_many':
                combo_steps = mapping.get('combo_steps') or []
                oge_lines.append(f"# 组合实现: {gee_api}")
                for step in combo_steps:
                    oge_api = step.get('oge_api', 'unknown')
                    oge_lines.append(f'step_result = service.getProcess("{oge_api}").execute(...)')
                oge_lines.append("")

            elif mapping_type == 'many_to_one':
                oge_api = mapping.get('oge_api', {})
                if oge_api:
                    oge_api_name = oge_api.get('api_name', '')
                    oge_lines.append(f'# 多对一映射: {gee_api} -> {oge_api_name}')
                    oge_lines.append(f'result = service.getProcess("{oge_api_name}").execute(...)')
                    oge_lines.append("")

        # 添加 print 输出或可视化代码
        if any('print' in api for api in step_apis):
            oge_lines.append("# 输出结果")
            oge_lines.append("print(result)")
            oge_lines.append("")

        if any('Map' in api for api in step_apis):
            oge_lines.append("# 可视化输出")
            oge_lines.append('oge.mapclient.centerMap(lon, lat, zoom)')
            oge_lines.append("")

        return '\n'.join(oge_lines), feasibility

    @staticmethod
    def _extract_var_assignments(code: str) -> Dict[str, str]:
        """从 GEE 代码中提取变量赋值信息

        Args:
            code: GEE 代码片段

        Returns:
            Dict[str, str]: {变量名: 赋值表达式}
        """
        assignments = {}
        var_pattern = re.compile(
            r'(?:var|let|const)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?);',
            re.DOTALL
        )
        for match in var_pattern.finditer(code):
            var_name = match.group(1)
            value = match.group(2).strip()
            assignments[var_name] = value
        return assignments

    @staticmethod
    def _generate_api_call_code(
        gee_api: str, oge_api_name: str,
        var_assignments: Dict[str, str], gee_code: str
    ) -> str:
        """根据 GEE API 和映射关系生成具体的 OGE 调用代码

        Args:
            gee_api: GEE API 名
            oge_api_name: 映射的 OGE API 名
            var_assignments: 变量赋值信息
            gee_code: GEE 原始代码

        Returns:
            str: OGE 调用代码字符串
        """
        lines = []

        # 根据 OGE API 类型生成不同的调用模板
        if 'Geometry' in oge_api_name:
            if 'buffer' in oge_api_name:
                lines.append('# 几何缓冲分析')
                lines.append('geometry = service.getProcess("Geometry.Polygon").execute(...)')
                lines.append(f'result = service.getProcess("{oge_api_name}").execute(geometry, distance)')
            elif 'Point' in oge_api_name:
                lines.append(f'geometry = service.getProcess("{oge_api_name}").execute([lng, lat], "EPSG:4326")')
            elif 'LineString' in oge_api_name:
                lines.append(f'geometry = service.getProcess("{oge_api_name}").execute([[lng1, lat1], [lng2, lat2]], "EPSG:4326")')
            elif 'Polygon' in oge_api_name:
                lines.append(f'geometry = service.getProcess("{oge_api_name}").execute([[[lng, lat], ...]], "EPSG:4326")')
            else:
                lines.append(f'result = service.getProcess("{oge_api_name}").execute(...)')

        elif 'Feature' in oge_api_name and 'Collection' not in oge_api_name:
            lines.append(f'feature = service.getProcess("{oge_api_name}").execute(geometry, properties)')

        elif 'FeatureCollection' in oge_api_name:
            if 'filter' in oge_api_name.lower():
                lines.append(f'result = service.getProcess("{oge_api_name}").execute(feature_collection, start, end, "system:time_start")')
            elif 'loadFromFeatureList' in oge_api_name:
                lines.append(f'feature_collection = service.getProcess("{oge_api_name}").execute([feature1, feature2])')
            else:
                lines.append(f'result = service.getProcess("{oge_api_name}").execute(...)')

        elif 'Coverage' in oge_api_name:
            if 'filter' in oge_api_name.lower():
                lines.append(f'result = service.getProcess("{oge_api_name}").execute(coverage, ...)')
            else:
                lines.append(f'result = service.getProcess("{oge_api_name}").execute(coverage, ...)')

        elif 'filterDate' in oge_api_name:
            lines.append(f'result = service.getProcess("{oge_api_name}").execute(fc, "start_date", "end_date", "system:time_start")')

        else:
            lines.append(f'result = service.getProcess("{oge_api_name}").execute(...)')

        return '\n'.join(lines)

    # ============================================================
    # Step 5: 可行性补全
    # ============================================================

    def step5_feasibility_completion(self, step3_result: Step3Result,
                                     step4_result: Step4Result,
                                     llm_service=None) -> Step5Result:
        """步骤 5：可行性补全

        分析缺失的 API，判断是否阻断整体工作流，并给出修复建议。
        当 LLM 可用时，对缺失 API 调用 LLM 生成 Python 原生实现建议，
        丰富补救方案，提升非阻断性缺失的可恢复性。

        Args:
            step3_result: 步骤 3 的结果
            step4_result: 步骤 4 的结果
            llm_service: LLM 服务实例（可选，用于生成 Python 实现建议）

        Returns:
            Step5Result: 可行性补全结果
        """
        result = Step5Result()

        # 1. 判断阻断性 API
        # 阻断性 API：核心分析算子（非 UI/可视化类）
        blocking_keywords = ['Image', 'ImageCollection', 'Feature', 'FeatureCollection',
                             'Reducer', 'Classifier', 'Filter']
        ui_keywords = ['Map.addLayer', 'Map.setCenter', 'Map.setOptions', 'print', 'Export']

        for missing_api in step3_result.missing_apis:
            # 判断是否为 UI 类
            is_ui = any(kw in missing_api for kw in ui_keywords)
            if is_ui:
                result.non_blocking_gaps.append(missing_api)
                result.rescue_suggestions.append({
                    'api': missing_api,
                    'suggestion': 'UI/可视化类算子缺失，不影响核心分析流程，可用 print 或注释替代'
                })
            else:
                # 判断是否为核心分析算子
                is_core = any(kw in missing_api for kw in blocking_keywords)
                if is_core:
                    result.blocking_apis.append(missing_api)
                    result.rescue_suggestions.append({
                        'api': missing_api,
                        'suggestion': '核心分析算子缺失，需用 Python 实现或寻找替代 OGE 算子'
                    })
                else:
                    result.non_blocking_gaps.append(missing_api)
                    result.rescue_suggestions.append({
                        'api': missing_api,
                        'suggestion': '辅助类算子缺失，可用 Python 原生实现替代'
                    })

        # 2. LLM 增强：为缺失 API 生成 Python 原生实现建议
        if llm_service and llm_service.is_available() and step3_result.missing_apis:
            for suggestion in result.rescue_suggestions:
                api = suggestion.get('api', '')
                if not api:
                    continue
                try:
                    impl = llm_service.suggest_python_implementation(api)
                    if impl and impl.get('python_code'):
                        suggestion['python_code'] = impl.get('python_code')
                        suggestion['dependencies'] = impl.get('dependencies', [])
                        suggestion['example'] = impl.get('example', '')
                except Exception as e:
                    print(f'[Step5] LLM 生成 Python 实现 {api} 失败: {e}')

        # 3. 整体可行性
        if result.blocking_apis:
            result.overall_feasible = False
        else:
            result.overall_feasible = True

        return result

    # ============================================================
    # Step 6: 工作流重构
    # ============================================================

    def step6_workflow_reconstruction(self, step4_result: Step4Result,
                                      step5_result: Step5Result,
                                      step1_result: Step1Result) -> Step6Result:
        """步骤 6：工作流重构

        将步骤级代码整合为完整可执行的 OGE 工作流；
        若存在阻断性缺失 API，则生成 API 缺失报告

        Args:
            step4_result: 步骤 4 的结果
            step5_result: 步骤 5 的结果
            step1_result: 步骤 1 的结果

        Returns:
            Step6Result: 工作流重构结果
        """
        result = Step6Result()

        # 1. 判断整体可行性
        if step5_result.blocking_apis:
            result.feasibility = 'infeasible'
            result.missing_report = self._generate_missing_report(
                step1_result, step5_result
            )
            result.oge_code = self._assemble_partial_workflow(step4_result, step5_result)
        elif step5_result.non_blocking_gaps:
            result.feasibility = 'partial_feasible'
            result.oge_code = self._assemble_full_workflow(step4_result, step1_result)
        else:
            result.feasibility = 'full_feasible'
            result.oge_code = self._assemble_full_workflow(step4_result, step1_result)

        return result

    def _assemble_full_workflow(self, step4_result: Step4Result,
                                 step1_result: Step1Result) -> str:
        """组装完整 OGE 工作流代码

        Args:
            step4_result: 步骤 4 的结果
            step1_result: 步骤 1 的结果

        Returns:
            str: 完整 OGE 代码
        """
        lines = [
            "# ============================================================",
            "# GEE → OGE 自动迁移生成的工作流",
            f"# 任务目标: {step1_result.task_goal}",
            "# ============================================================",
            "",
            "import oge",
            "",
            "# 初始化",
            "oge.initialize()",
            "service = oge.Service()",
            "",
        ]

        for step_code in step4_result.step_codes:
            lines.append(f"# ----- Step {step_code['step_index']}: {step_code['step_description']} -----")
            lines.append(step_code['oge_code'])
            lines.append("")

        return '\n'.join(lines)

    def _assemble_partial_workflow(self, step4_result: Step4Result,
                                    step5_result: Step5Result) -> str:
        """组装部分可执行的工作流（含阻断性缺失）

        Args:
            step4_result: 步骤 4 的结果
            step5_result: 步骤 5 的结果

        Returns:
            str: 部分可执行的 OGE 代码
        """
        lines = [
            "# ============================================================",
            "# GEE → OGE 自动迁移生成的工作流（部分可执行）",
            f"# 警告: 存在 {len(step5_result.blocking_apis)} 个阻断性缺失 API",
            "# ============================================================",
            "",
            "import oge",
            "",
            "oge.initialize()",
            "service = oge.Service()",
            "",
        ]

        for step_code in step4_result.step_codes:
            lines.append(f"# ----- Step {step_code['step_index']}: {step_code['step_description']} -----")
            lines.append(step_code['oge_code'])
            lines.append("")

        lines.append("# ============================================================")
        lines.append("# 阻断性缺失 API 列表（需手动实现或寻找替代方案）")
        for api in step5_result.blocking_apis:
            lines.append(f"# - {api}")
        lines.append("# ============================================================")

        return '\n'.join(lines)

    def _generate_missing_report(self, step1_result: Step1Result,
                                  step5_result: Step5Result) -> str:
        """生成 API 缺失报告

        Args:
            step1_result: 步骤 1 的结果
            step5_result: 步骤 5 的结果

        Returns:
            str: 缺失报告文本
        """
        lines = [
            "============================================================",
            "         OGE API 缺失报告",
            "============================================================",
            "",
            f"任务目标: {step1_result.task_goal}",
            f"整体状态: {'不可执行' if step5_result.blocking_apis else '部分可执行'}",
            "",
            "----- 缺失 API 明细 -----",
        ]

        for api in step5_result.blocking_apis:
            lines.append(f"  [阻断] {api}")
        for api in step5_result.non_blocking_gaps:
            lines.append(f"  [非阻断] {api}")

        lines.append("")
        lines.append("----- 修复路线建议 -----")
        for sugg in step5_result.rescue_suggestions:
            lines.append(f"  {sugg['api']}: {sugg['suggestion']}")

        lines.append("")
        lines.append("============================================================")

        return '\n'.join(lines)

    # ============================================================
    # 统一入口
    # ============================================================

    def run(self, gee_code: str, llm_service=None) -> PipelineResult:
        """流水线统一入口

        输入 GEE 代码，一键执行完整的 6 步迁移流程，
        并记录每一步的耗时信息。

        Args:
            gee_code: 原始 GEE 代码
            llm_service: LLM 服务实例（可选，用于增强语义分析）

        Returns:
            PipelineResult: 完整结果对象（包含 timing 字段）
        """
        import time
        result = PipelineResult()

        try:
            # Step 1: 语义抽象（使用 LLM 增强步骤描述）
            _t0 = time.time()
            result.step1 = self.step1_semantic_abstraction(gee_code, llm_service)
            result.timing['step1'] = time.time() - _t0

            # Step 2: API 需求识别
            _t0 = time.time()
            result.step2 = self.step2_api_requirement(result.step1)
            result.timing['step2'] = time.time() - _t0

            # Step 3: API 匹配（LLM 可用时对未匹配 API 做语义匹配增强）
            _t0 = time.time()
            result.step3 = self.step3_api_matching(result.step2, llm_service)
            result.timing['step3'] = time.time() - _t0
            result.match_rate = result.step3.match_rate

            # Step 4: 代码生成
            _t0 = time.time()
            result.step4 = self.step4_ocode_codegen(
                result.step1, result.step2, result.step3
            )
            result.timing['step4'] = time.time() - _t0

            # Step 5: 可行性补全（LLM 可用时为缺失 API 生成 Python 实现建议）
            _t0 = time.time()
            result.step5 = self.step5_feasibility_completion(
                result.step3, result.step4, llm_service
            )
            result.timing['step5'] = time.time() - _t0

            # Step 6: 工作流重构
            _t0 = time.time()
            result.step6 = self.step6_workflow_reconstruction(
                result.step4, result.step5, result.step1
            )
            result.timing['step6'] = time.time() - _t0

            # 计算总耗时
            result.timing['total'] = sum(result.timing.get(f'step{i}', 0) for i in range(1, 7))
            result.success = True

        except Exception as e:
            result.success = False
            result.error = str(e)

        return result

    # ============================================================
    # 结果持久化接口
    # ============================================================

    def save_result_to_db(self, result: PipelineResult,
                          case_name: str = '未命名案例',
                          gee_code: str = '') -> int:
        """将流水线执行结果保存到 case_study_pipeline 表

        每一步的中间产物（语义摘要、API 清单、匹配详情、步骤级代码、
        可行性补全、最终工作流）均以 JSON 形式持久化，便于历史追溯与对比

        Args:
            result: 流水线执行结果对象
            case_name: 案例名称（如 "华东小麦长势监测"）
            gee_code: 原始 GEE 代码

        Returns:
            int: 新插入记录的 id
        """
        conn = self.dao.conn
        cursor = conn.execute(
            """INSERT INTO case_study_pipeline
               (case_name, gee_code, step1_summary, step2_apis, step3_match,
                step4_codegen, step5_feasible, step6_workflow, match_rate, feasibility)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (case_name,
             gee_code,
             json.dumps(result.step1.to_dict(), ensure_ascii=False) if result.step1 else None,
             json.dumps(result.step2.to_dict(), ensure_ascii=False) if result.step2 else None,
             json.dumps(result.step3.to_dict(), ensure_ascii=False) if result.step3 else None,
             json.dumps(result.step4.to_dict(), ensure_ascii=False) if result.step4 else None,
             json.dumps(result.step5.to_dict(), ensure_ascii=False) if result.step5 else None,
             result.step6.oge_code if result.step6 else None,
             result.match_rate,
             result.step6.feasibility if result.step6 else None)
        )
        conn.commit()
        return cursor.lastrowid


# ============================================================
# 便捷函数
# ============================================================

def run_pipeline(gee_code: str, db_path: str = DEFAULT_DB_PATH) -> PipelineResult:
    """流水线便捷入口函数

    Args:
        gee_code: 原始 GEE 代码
        db_path: 数据库路径

    Returns:
        PipelineResult: 完整结果对象
    """
    pipeline = CaseStudyPipeline(db_path)
    try:
        return pipeline.run(gee_code)
    finally:
        pipeline.close()


# ============================================================
# 主入口：使用 case_study_demo.html 中的示例进行演示
# ============================================================

if __name__ == '__main__':
    # case_study_demo.html 中的示例 GEE 代码
    sample_gee_code = """// Winter-season image
var winterImage = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_119038_20230104');

// Summer-season image
var summerImage = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_119038_20220728');

// -----------------------
// Winter bands
// -----------------------
var winterRed = winterImage.select('B4');
var winterGreen = winterImage.select('B3');
var winterNir = winterImage.select('B5');
var winterSwir1 = winterImage.select('B6');

// Winter NDVI
var winterNdviNumerator = winterNir.subtract(winterRed);
var winterNdviDenominator = winterNir.add(winterRed);
var winterNdvi = winterNdviNumerator.divide(winterNdviDenominator).rename('Winter_NDVI');

// Visualization parameters
var vis = {
  min: -1,
  max: 1,
  palette: ['blue', 'lightblue', 'green', 'yellow', 'red']
};

// Add layers to the map
Map.addLayer(winterNdvi, vis, 'Winter NDVI');

// Set the map center
Map.setCenter(120.5, 32.0, 9);"""

    print("=" * 70)
    print("Case Study 流水线演示")
    print("=" * 70)

    result = run_pipeline(sample_gee_code)

    print(f"\n[流水线状态] {'成功' if result.success else '失败'}")
    if result.error:
        print(f"[错误信息] {result.error}")

    if result.step1:
        print(f"\n----- Step 1: 语义抽象 -----")
        print(f"任务目标: {result.step1.task_goal}")
        print(f"步骤数量: {len(result.step1.workflow_steps)}")
        for i, step in enumerate(result.step1.workflow_steps, 1):
            print(f"  {i}. {step}")
        if result.step1.key_params:
            print(f"关键参数: {json.dumps(result.step1.key_params, ensure_ascii=False, indent=2)}")

    if result.step2:
        print(f"\n----- Step 2: API 需求识别 -----")
        print(f"API 总数: {result.step2.api_count}")
        print(f"API 列表:")
        for api in result.step2.all_apis:
            print(f"  - {api}")

    if result.step3:
        print(f"\n----- Step 3: GEE→OGE API 匹配 -----")
        print(f"匹配率: {result.step3.match_rate:.2%}")
        print(f"已匹配: {result.step3.matched_count}")
        print(f"未匹配: {result.step3.missing_count}")
        if result.step3.missing_apis:
            print(f"缺失 API: {result.step3.missing_apis}")

    if result.step5:
        print(f"\n----- Step 5: 可行性补全 -----")
        print(f"整体可行: {'是' if result.step5.overall_feasible else '否'}")
        if result.step5.blocking_apis:
            print(f"阻断性 API: {result.step5.blocking_apis}")

    if result.step6:
        print(f"\n----- Step 6: 工作流重构 -----")
        print(f"可行性: {result.step6.feasibility}")
        print(f"\n生成的 OGE 代码（前 50 行）:")
        print('\n'.join(result.step6.oge_code.splitlines()[:50]))

    # 将结果保存到数据库
    print(f"\n----- 保存结果到数据库 -----")
    pipeline2 = CaseStudyPipeline()
    try:
        record_id = pipeline2.save_result_to_db(
            result, case_name='华东小麦长势监测案例', gee_code=sample_gee_code
        )
        print(f"[OK] 结果已保存到 case_study_pipeline 表，记录 id: {record_id}")
    finally:
        pipeline2.close()

    # 导出完整结果到 JSON（报告类产物统一输出到 docs/ 目录）
    docs_dir = os.path.join(PROJECT_ROOT, 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, 'case_study_result.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"[OK] 完整结果已导出到: {output_path}")
