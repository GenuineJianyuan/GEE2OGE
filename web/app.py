"""
GEE2OGE 迁移系统 - Flask Web 后端服务器

提供 RESTful API：
1. POST /api/convert      - GEE 代码转 OGE 代码（规则引擎）
2. POST /api/convert-llm  - GEE 代码转 OGE 代码（LLM 增强版）
3. GET  /api/llm-status   - 检测 LLM 服务可用性
4. GET  /api/mappings     - 查询算子映射知识库
5. GET  /api/history      - 查询历史转换记录
6. GET  /api/stats        - 获取知识库统计信息
"""

import json
import os
import sys
import time
import threading
import traceback
import uuid
from flask import Flask, request, jsonify, render_template

# 项目根目录配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from db_dao import GeeOgeDao
from case_study_pipeline import CaseStudyPipeline
from llm_service import get_llm_service

app = Flask(__name__, template_folder='templates', static_folder='static')

# ============================================================
# 结果缓存持久化
# ============================================================

CACHE_FILE = os.path.join(PROJECT_ROOT, 'resource', 'result_cache.json')


def _load_cache():
    """从文件加载结果缓存"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f'[Cache] 加载失败: {e}')
    return {}


def _save_cache(cache_data):
    """保存结果缓存到文件"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f'[Cache] 保存失败: {e}')
        return False


@app.route('/api/result-cache', methods=['GET'])
def get_result_cache():
    """获取所有结果缓存"""
    try:
        cache = _load_cache()
        return jsonify({'success': True, 'cache': cache})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/result-cache', methods=['POST'])
def save_result_cache():
    """保存结果缓存（整体覆盖）"""
    try:
        cache_data = request.get_json(force=True) or {}
        ok = _save_cache(cache_data)
        return jsonify({'success': ok})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/result-cache', methods=['DELETE'])
def clear_result_cache():
    """清空结果缓存"""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        return jsonify({'success': True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def _get_dao():
    """创建新的 DAO 实例（每次请求使用独立连接，避免 SQLite 多线程问题）"""
    return GeeOgeDao()


# ============================================================
# 页面路由
# ============================================================

@app.route('/')
def index():
    """主页 - 单页应用，包含代码转换、知识库、历史记录"""
    return render_template('index.html')


@app.route('/test')
def interface_test_page():
    """接口测试页面 - 测试所有 Web API 接口"""
    return render_template('test.html')


@app.route('/samples')
def samples_page():
    """GEE 示例代码页面 - 展示从 gee.json 生成的纯代码示例"""
    return render_template('samples.html')


@app.route('/benchmark')
def benchmark_page():
    """Benchmark 测试集页面 - OGE→GEE 反向转换工具"""
    return render_template('benchmark.html')


@app.route('/gee-convert')
def gee_convert_page():
    """GEE→OGE 批量转换页面"""
    return render_template('gee_convert.html')


# ============================================================
# API 路由 - 转换相关
# ============================================================

@app.route('/api/llm-status', methods=['GET'])
def api_llm_status():
    """检测 LLM 服务是否可用"""
    try:
        svc = get_llm_service()
        svc.reset_availability()
        available = svc.is_available()
        return jsonify({
            'success': True,
            'available': available,
            'model': svc.model if available else None,
            'base_url': svc.base_url if available else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'available': False})


@app.route('/api/convert', methods=['POST'])
def api_convert():
    """GEE 代码转 OGE 代码（规则引擎版）"""
    data = request.get_json() or {}
    gee_code = data.get('gee_code', '').strip()
    case_name = data.get('case_name', '未命名案例')

    if not gee_code:
        return jsonify({'success': False, 'error': 'GEE 代码不能为空'}), 400

    try:
        pipeline = CaseStudyPipeline()
        result = pipeline.run(gee_code)

        record_id = None
        if result.success:
            record_id = pipeline.save_result_to_db(result, case_name, gee_code)

        pipeline.close()

        response = {
            'success': result.success,
            'result': result.to_dict(),
            'record_id': record_id,
            'engine': 'rule_based'
        }
        if result.error:
            response['error'] = result.error

        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'服务器内部错误: {str(e)}'}), 500


@app.route('/api/convert-llm', methods=['POST'])
def api_convert_llm():
    """GEE 代码转 OGE 代码（LLM 增强版）

    先使用规则引擎获取基础映射，再调用 LLM 进行智能增强：
    1. 规则引擎执行完整 6 步流水线
    2. 用 LLM 分析代码意图和变量类型
    3. 用 LLM 优化 OGE 代码生成
    4. 对缺失的 API 用 LLM 推断可能的 OGE 映射
    
    返回结果包含每步耗时信息（timing 字段）。
    """
    import time
    data = request.get_json() or {}
    gee_code = data.get('gee_code', '').strip()
    case_name = data.get('case_name', '未命名案例')

    if not gee_code:
        return jsonify({'success': False, 'error': 'GEE 代码不能为空'}), 400

    try:
        llm = get_llm_service()
        llm.reset_availability()
        if not llm.is_available():
            return jsonify({
                'success': False,
                'error': 'LLM 服务不可用，请检查本地大模型 API 连接',
                'fallback_to_rule': True
            }), 503

        # Step 1: 先用规则引擎获取基础结果（传入 LLM 用于增强步骤描述）
        _t_pipeline_start = time.time()
        pipeline = CaseStudyPipeline()
        rule_result = pipeline.run(gee_code, llm)
        pipeline_total_time = time.time() - _t_pipeline_start

        # Step 2: LLM 增强分析（复用 pipeline 中 step1 已获取的 llm_analysis，避免重复调用）
        llm_generated = None
        llm_enhancements = []
        llm_timing = {}

        # 2a. 直接复用 pipeline.step1 中保存的 LLM 分析结果
        llm_analysis = None
        if rule_result.step1 and rule_result.step1.llm_analysis:
            llm_analysis = rule_result.step1.llm_analysis
            if llm_analysis.get('task_goal'):
                llm_enhancements.append(f"LLM 任务目标: {llm_analysis['task_goal']}")
            if llm_analysis.get('suggestions'):
                llm_enhancements.extend(llm_analysis['suggestions'])

        # 2b. LLM 代码生成
        _t_llm_gen = time.time()
        try:
            mapping_context = _build_mapping_context(pipeline.dao, gee_code)
            llm_generated = llm.generate_oge_code(gee_code, mapping_context)
            if llm_generated and llm_generated.get('warnings'):
                llm_enhancements.extend(llm_generated['warnings'])
        except Exception as e:
            traceback.print_exc()
            llm_enhancements.append(f"LLM 代码生成失败: {str(e)}")
        llm_timing['llm_code_gen'] = time.time() - _t_llm_gen

        # Step 3: 合并结果
        final_result = rule_result.to_dict()

        # 用 LLM 生成的代码替换/补充规则引擎的代码
        if llm_generated and llm_generated.get('oge_code'):
            final_result['step6'] = {
                'oge_code': llm_generated['oge_code'],
                'missing_report': llm_generated.get('warnings'),
                'feasibility': llm_generated.get('feasibility', 'partial_feasible'),
                'llm_generated': True
            }
            final_result['llm_oge_code'] = llm_generated['oge_code']

        # 添加 LLM 分析结果
        if llm_analysis:
            final_result['llm_analysis'] = llm_analysis
            
            # 将 LLM 分析的 key_params 合并到 step1.key_params 中
            llm_key_params = llm_analysis.get('key_params', {})
            if llm_key_params and isinstance(llm_key_params, dict):
                # 获取现有的 key_params
                existing_params = final_result.get('step1', {}).get('key_params', {})
                if not isinstance(existing_params, dict):
                    existing_params = {}
                # 合并 LLM 提取的参数（不覆盖已有的，但可以补充）
                for key, value in llm_key_params.items():
                    if key not in existing_params:
                        existing_params[key] = value
                final_result['step1']['key_params'] = existing_params

        final_result['llm_enhancements'] = llm_enhancements
        final_result['engine'] = 'llm_enhanced'

        # 合并耗时信息
        # 基础流水线耗时 + LLM 增强耗时
        combined_timing = dict(rule_result.timing)  # step1-step6 + total
        combined_timing['pipeline_total'] = pipeline_total_time
        combined_timing['llm_code_gen'] = llm_timing.get('llm_code_gen', 0)
        # 计算接口总耗时
        combined_timing['api_total'] = combined_timing.get('total', 0) + combined_timing.get('llm_code_gen', 0)
        final_result['timing'] = combined_timing

        # Step 4: 保存到数据库
        record_id = None
        if rule_result.success:
            record_id = pipeline.save_result_to_db(rule_result, case_name, gee_code)

        pipeline.close()

        response = {
            'success': True,
            'result': final_result,
            'record_id': record_id,
            'engine': 'llm_enhanced',
            'llm_available': True,
            'timing': combined_timing  # 顶层也返回一份耗时，方便前端快速访问
        }

        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'LLM 增强转换失败: {str(e)}'}), 500


def _build_mapping_context(dao, gee_code: str) -> str:
    """从 GEE 代码中提取 API 调用，构建详细的映射上下文

    提取代码中所有 GEE API，查询其对应的 OGE API 详情（签名、参数、描述、示例代码），
    组装成结构化的映射表供 LLM 使用。

    Args:
        dao: 数据访问对象
        gee_code: GEE 代码

    Returns:
        str: 详细的映射上下文文本（包含 OGE API 签名和示例）
    """
    import re

    # 提取 API 调用（ctor + 链式调用）
    apis = set()
    ctor_pattern = re.compile(r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*)\s*\(')
    for m in ctor_pattern.finditer(gee_code):
        apis.add(m.group(1))

    api_pattern = re.compile(
        r'\b(ee\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\s*\('
    )
    for m in api_pattern.finditer(gee_code):
        apis.add(m.group(1))

    map_pattern = re.compile(r'\b(Map\.[A-Za-z_][A-Za-z0-9_]*)\s*\(')
    for m in map_pattern.finditer(gee_code):
        apis.add(m.group(1))

    # 构建详细映射表
    context_parts = []
    # 跟踪是否涉及 FeatureCollection 构建场景
    has_fc_construction = False
    has_filter_date = False

    for api in sorted(apis):
        mapping = dao.get_mapping_by_gee_name(api)
        if not mapping:
            context_parts.append(f"## {api}\n- 映射状态: 未找到映射\n")
            continue

        mtype = mapping['mapping_type']
        gee_api = mapping['gee_api'] or {}
        oge_api = mapping['oge_api']

        # 检测关键场景
        if api == 'ee.FeatureCollection':
            has_fc_construction = True
        if api == 'ee.Filter.date':
            has_filter_date = True

        # GEE API 描述
        gee_desc = (gee_api.get('description') or '').strip()
        gee_args = gee_api.get('arg_types') or []

        part_lines = [f"## {api}"]
        if gee_desc:
            part_lines.append(f"- GEE 描述: {gee_desc}")
        if gee_args:
            arg_strs = []
            for arg in gee_args:
                if isinstance(arg, dict):
                    arg_strs.append(f"{arg.get('name', '?')}: {arg.get('type', '?')}")
                else:
                    arg_strs.append(str(arg))
            part_lines.append(f"- GEE 参数: {', '.join(arg_strs)}")

        if mtype == 'one_to_one' and oge_api:
            oge_name = oge_api.get('api_name', '')
            oge_desc = (oge_api.get('description') or '').strip()
            oge_inputs = oge_api.get('input_types') or []
            oge_output = oge_api.get('output_type', '')
            oge_sample = (oge_api.get('samplecode') or '').strip()

            part_lines.append(f"- 映射类型: 一对一 (one_to_one)")
            part_lines.append(f"- OGE API: {oge_name}")
            if oge_desc:
                part_lines.append(f"- OGE 描述: {oge_desc}")
            if oge_inputs:
                part_lines.append(f"- OGE 输入类型: {', '.join(oge_inputs)}")
            if oge_output:
                part_lines.append(f"- OGE 输出类型: {oge_output}")
            # 添加完整的示例代码（用代码块格式）
            if oge_sample:
                part_lines.append(f"- OGE 示例代码:\n```python\n{oge_sample}\n```")

        elif mtype == 'one_to_many':
            combo_steps = mapping.get('combo_steps') or []
            part_lines.append(f"- 映射类型: 一对多 (one_to_many)，共 {len(combo_steps)} 步")
            for i, step in enumerate(combo_steps):
                step_oge = step.get('oge_api_name', '')
                step_desc = step.get('description', '')
                part_lines.append(f"  - 步骤{i+1}: {step_oge} ({step_desc})")

        elif mtype == 'native_python':
            py_code = mapping.get('native_python_code') or ''
            part_lines.append(f"- 映射类型: Python 原生实现 (native_python)")
            if py_code:
                # 截取前 200 字符
                py_short = py_code[:300]
                part_lines.append(f"- Python 实现:\n```python\n{py_short}\n```")

        elif mtype == 'many_to_one':
            part_lines.append(f"- 映射类型: 多对一 (many_to_one)")
            if oge_api:
                part_lines.append(f"- OGE API: {oge_api.get('api_name', '')}")

        else:
            part_lines.append(f"- 映射类型: {mtype}")

        context_parts.append('\n'.join(part_lines))

    # 添加特殊场景补充说明
    special_notes = []
    if has_fc_construction:
        special_notes.append(
            "## 补充说明：FeatureCollection 构建\n"
            "- 当 GEE 代码用 `ee.FeatureCollection([feature1, feature2, ...])` "
            "从 Feature 列表构建时，应使用 `FeatureCollection.loadFromFeatureList` 算子：\n"
            "  ```python\n"
            "  fc = service.getProcess('FeatureCollection.loadFromFeatureList')"
            ".execute([feature1, feature2, ...])\n"
            "  ```\n"
            "- 当从 GeoJSON 构建时，使用 `FeatureCollection.loadFromGeojson`\n"
            "- `Service.getFeatureCollection` 仅用于加载已存在的矢量数据集"
        )
    if has_filter_date:
        special_notes.append(
            "## 补充说明：日期过滤\n"
            "- `FeatureCollection.filterDate` 需要 4 个参数："
            "(featureCollection, startDate, endDate, timeFieldName)\n"
            "- 第4个参数是时间字段名，通常为 'system:time_start'\n"
            "- 示例：`fc = service.getProcess('FeatureCollection.filterDate')"
            ".execute(fc, '2021-07-01', '2021-08-01', 'system:time_start')`\n"
            "- `ee.Date('2021-07-01')` 在 OGE 中直接使用字符串 `'2021-07-01'`\n"
            "- `ee.DateRange(start, end)` 在 OGE 中拆分为两个字符串参数"
        )

    if context_parts:
        result = '\n\n'.join(context_parts)
        if special_notes:
            result += '\n\n' + '\n\n'.join(special_notes)

        # 添加 GEE 代码变量分析，帮助 LLM 理解代码结构
        var_analysis = _extract_gee_variables(gee_code)
        if var_analysis:
            result += '\n\n## GEE 代码变量分析（重要！请使用这些变量名和值）\n' + var_analysis

        return result
    return "（未在数据库中找到该代码涉及的 GEE API 映射，需要根据 OGE 语法指南推断实现）"


def _extract_gee_variables(gee_code: str) -> str:
    """从 GEE 代码中提取变量定义和值，帮助 LLM 生成更具体的 OGE 代码

    Args:
        gee_code: GEE JavaScript 代码

    Returns:
        str: 变量分析文本
    """
    import re

    lines = gee_code.split('\n')
    var_defs = []

    # 匹配变量定义: var xxx = ...
    var_pattern = re.compile(
        r'^\s*var\s+(\w+)\s*=\s*(.+?);\s*$'
    )

    for line in lines:
        match = var_pattern.match(line)
        if match:
            var_name = match.group(1)
            var_value = match.group(2).strip()
            # 移除注释
            if '//' in var_value:
                var_value = var_value[:var_value.index('//')].strip()
            var_defs.append(f"- {var_name} = {var_value}")

    if not var_defs:
        return ""

    return "\n".join(var_defs)


# ============================================================
# API 路由 - 知识库查询
# ============================================================

@app.route('/api/mappings', methods=['GET'])
def api_mappings():
    """查询算子映射知识库（支持类型、关键词、类名过滤，分页）"""
    mapping_type = request.args.get('type', 'all')
    keyword = request.args.get('keyword', '').strip()
    gee_class = request.args.get('class', '').strip()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(int(request.args.get('per_page', 50)), 200)

    try:
        dao = _get_dao()
        if mapping_type == 'all':
            all_mappings = dao.get_all_mappings()
        else:
            all_mappings = dao.get_mappings_by_type(mapping_type)

        if keyword:
            keyword_lower = keyword.lower()
            filtered = []
            for m in all_mappings:
                gee_name = m['gee_api']['api_full_name'].lower() if m['gee_api'] else ''
                oge_name = (m['oge_api']['api_name'].lower() if m['oge_api'] else '')
                desc = ''
                if m['gee_api']:
                    desc = (m['gee_api'].get('description') or '').lower()
                if keyword_lower in gee_name or keyword_lower in oge_name or keyword_lower in desc:
                    filtered.append(m)
            all_mappings = filtered

        if gee_class:
            filtered = [m for m in all_mappings if m['gee_api'] and m['gee_api'].get('class_name') == gee_class]
            all_mappings = filtered

        total = len(all_mappings)
        start = (page - 1) * per_page
        paged = all_mappings[start:start + per_page]

        simplified = []
        for m in paged:
            item = {
                'gee_api': {
                    'full_name': m['gee_api']['api_full_name'],
                    'class_name': m['gee_api'].get('class_name', ''),
                    'description': m['gee_api'].get('description', '')[:100]
                },
                'oge_api': m['oge_api']['api_name'] if m['oge_api'] else None,
                'mapping_type': m['mapping_type'],
                'confidence': m['confidence'],
                'has_python_code': bool(m.get('native_python_code')),
                'verification_status': m['verification_status']
            }
            simplified.append(item)

        return jsonify({'success': True, 'total': total, 'page': page, 'per_page': per_page, 'data': simplified})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/mapping/<gee_name>', methods=['GET'])
def api_mapping_detail(gee_name):
    """查询单个 GEE API 的完整映射详情"""
    try:
        from urllib.parse import unquote
        gee_name = unquote(gee_name)

        dao = _get_dao()
        result = dao.get_mapping_by_gee_name(gee_name)
        if result is None:
            return jsonify({'success': False, 'error': '未找到该 API 的映射'}), 404

        if result['mapping_type'] == 'native_python' and result['native_python_code']:
            code = result['native_python_code']
            if len(code) > 2000:
                result['native_python_code_preview'] = code[:2000] + '\n... (代码已截断)'
            else:
                result['native_python_code_preview'] = code

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/mapping-library', methods=['GET'])
def api_mapping_library():
    """查询 GEE-OGE 关联映射库（用于关联库视图）

    返回所有 GEE API 及其映射状态，支持搜索、分类和筛选
    """
    keyword = request.args.get('keyword', '').strip()
    class_name = request.args.get('class', '').strip()
    mapping_filter = request.args.get('mapping', '').strip()  # mapped/unmapped/all
    mapping_type_filter = request.args.get('mapping_type', '').strip()  # one_to_one/one_to_many/many_to_one/native_python
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(int(request.args.get('per_page', 50)), 200)

    try:
        dao = _get_dao()
        conn = dao.conn

        # 先获取所有映射关系（用字典存储以便快速查找）
        all_mappings = conn.execute("""
            SELECT g.api_full_name, m.mapping_type, o.api_name as oge_api_name
            FROM operator_mapping m
            JOIN gee_api_info g ON m.gee_api_id = g.id
            LEFT JOIN oge_api_info o ON m.oge_api_id = o.id
        """).fetchall()
        mapping_map = {}
        for m in all_mappings:
            mapping_map[m['api_full_name']] = {
                'mapping_type': m['mapping_type'],
                'oge_api_name': m['oge_api_name'] or ''
            }

        # 构建 GEE API 的查询条件
        gee_conditions = []
        gee_params = []
        if keyword:
            gee_conditions.append("(api_full_name LIKE ? OR description LIKE ?)")
            kw = f'%{keyword}%'
            gee_params.extend([kw, kw])
        if class_name:
            gee_conditions.append("class_name = ?")
            gee_params.append(class_name)

        gee_where = f"WHERE {' AND '.join(gee_conditions)}" if gee_conditions else ""

        # 先获取所有符合基础条件的 GEE API（不分页，用于过滤映射状态）
        all_gee_rows = conn.execute(
            f"SELECT id, api_full_name, class_name, method_name, description, samplecode, sample_source FROM gee_api_info {gee_where} ORDER BY class_name, method_name",
            gee_params
        ).fetchall()

        # 构建带映射状态的完整数据列表
        all_data = []
        for row in all_gee_rows:
            item = dict(row)
            gee_name = item['api_full_name']
            mapping = mapping_map.get(gee_name)
            
            if mapping:
                item['mapped'] = True
                item['mapping_type'] = mapping['mapping_type']
                item['oge_api_name'] = mapping['oge_api_name'] or ''
            else:
                item['mapped'] = False
                item['mapping_type'] = None
                item['oge_api_name'] = None

            all_data.append(item)

        # 根据 mapping_filter 过滤
        if mapping_filter == 'mapped':
            filtered_data = [d for d in all_data if d['mapped']]
        elif mapping_filter == 'unmapped':
            filtered_data = [d for d in all_data if not d['mapped']]
        else:
            filtered_data = all_data

        # 根据 mapping_type_filter 过滤
        if mapping_type_filter:
            filtered_data = [d for d in filtered_data if d.get('mapping_type') == mapping_type_filter]

        # 计算统计信息
        total = len(filtered_data)
        mapped_count = sum(1 for d in filtered_data if d['mapped'])
        unmapped_count = total - mapped_count

        # 对过滤后的数据进行分页
        offset = (page - 1) * per_page
        data = filtered_data[offset:offset + per_page]

        return jsonify({
            'success': True,
            'total': total,
            'mapped_count': mapped_count,
            'unmapped_count': unmapped_count,
            'page': page,
            'per_page': per_page,
            'data': data
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/oge-api-detail', methods=['GET'])
def api_oge_detail():
    """查询单个 OGE API 详情"""
    api_name = request.args.get('api_name', '').strip()
    if not api_name:
        return jsonify({'success': False, 'error': 'api_name 参数必填'}), 400

    try:
        dao = _get_dao()
        conn = dao.conn

        row = conn.execute(
            "SELECT * FROM oge_api_info WHERE api_name = ?",
            (api_name,)
        ).fetchone()

        if row is None:
            return jsonify({'success': False, 'error': '未找到该 OGE API'}), 404

        data = dict(row)
        if data.get('input_types') and isinstance(data['input_types'], str):
            try:
                data['input_types'] = json.loads(data['input_types'])
            except (json.JSONDecodeError, TypeError):
                data['input_types'] = []
        
        # 确保字段有默认值，避免前端显示空白
        data['catalog_name'] = data.get('catalog_name') or ''
        data['description'] = data.get('description') or ''
        data['output_type'] = data.get('output_type') or ''
        data['samplecode'] = data.get('samplecode') or ''

        return jsonify({'success': True, 'data': data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/classes', methods=['GET'])
def api_history():
    """查询历史转换记录列表"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        dao = _get_dao()
        records = dao.list_pipeline_results(limit)
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/history/<int:record_id>', methods=['GET'])
def api_history_detail(record_id):
    """查询单条历史记录详情"""
    try:
        dao = _get_dao()
        result = dao.get_pipeline_result(record_id)
        if result is None:
            return jsonify({'success': False, 'error': '未找到该记录'}), 404
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """获取知识库统计信息"""
    try:
        dao = _get_dao()
        stats = dao.get_statistics()

        # 检查 LLM 状态
        llm_available = False
        try:
            llm_available = get_llm_service().is_available()
        except Exception:
            pass

        response = {
            'total_gee_apis': stats['total_gee_apis'],
            'total_oge_apis': stats['total_oge_apis'],
            'total_mappings': stats['total_mappings'],
            'by_mapping_type': stats['by_mapping_type'],
            'oge_general_purpose': stats['oge_general_purpose'],
            'oge_custom_model': stats['oge_custom_model'],
            'history_count': len(dao.list_pipeline_results(1000)),
            'llm_available': llm_available
        }
        return jsonify({'success': True, 'data': response})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/classes', methods=['GET'])
def api_classes():
    """获取所有类映射信息"""
    try:
        dao = _get_dao()
        mappings = dao.get_all_class_mappings()
        return jsonify({'success': True, 'data': mappings})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gee-apis', methods=['GET'])
def api_gee_apis():
    """查询 GEE API 列表（直接查 gee_api_info 表，支持搜索和分页）"""
    keyword = request.args.get('keyword', '').strip()
    class_name = request.args.get('class', '').strip()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(int(request.args.get('per_page', 50)), 200)

    try:
        dao = _get_dao()
        conn = dao.conn

        # 构建查询条件
        conditions = []
        params = []
        if keyword:
            conditions.append("(api_full_name LIKE ? OR description LIKE ? OR method_name LIKE ?)")
            kw = f'%{keyword}%'
            params.extend([kw, kw, kw])
        if class_name:
            conditions.append("class_name = ?")
            params.append(class_name)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 总数
        count_sql = f"SELECT COUNT(*) FROM gee_api_info {where_clause}"
        total = conn.execute(count_sql, params).fetchone()[0]

        # 分页查询
        offset = (page - 1) * per_page
        query_sql = f"""SELECT * FROM gee_api_info {where_clause} 
                       ORDER BY class_name, method_name 
                       LIMIT ? OFFSET ?"""
        rows = conn.execute(query_sql, params + [per_page, offset]).fetchall()

        data = []
        for row in rows:
            item = dict(row)
            item['arg_types'] = json.loads(item['arg_types']) if item.get('arg_types') else []
            data.append(item)

        return jsonify({'success': True, 'total': total, 'page': page, 'per_page': per_page, 'data': data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/oge-apis', methods=['GET'])
def api_oge_apis():
    """查询 OGE API 列表（直接查 oge_api_info 表，支持搜索和分页）"""
    keyword = request.args.get('keyword', '').strip()
    catalog = request.args.get('catalog', '').strip()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(int(request.args.get('per_page', 50)), 200)

    try:
        dao = _get_dao()
        conn = dao.conn

        conditions = []
        params = []
        # 过滤掉无效的占位记录（catalog_id=0 且 catalog_name 为空）
        conditions.append("(catalog_id != 0 OR catalog_name != '')")
        
        if keyword:
            conditions.append("(api_name LIKE ? OR description LIKE ? OR catalog_name LIKE ?)")
            kw = f'%{keyword}%'
            params.extend([kw, kw, kw])
        if catalog:
            conditions.append("catalog_name = ?")
            params.append(catalog)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_sql = f"SELECT COUNT(*) FROM oge_api_info {where_clause}"
        total = conn.execute(count_sql, params).fetchone()[0]

        offset = (page - 1) * per_page
        query_sql = f"""SELECT * FROM oge_api_info {where_clause}
                       ORDER BY catalog_name, api_name
                       LIMIT ? OFFSET ?"""
        rows = conn.execute(query_sql, params + [per_page, offset]).fetchall()

        data = [dict(row) for row in rows]

        return jsonify({'success': True, 'total': total, 'page': page, 'per_page': per_page, 'data': data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/native-python', methods=['GET'])
def api_native_python():
    """查询所有 Python 原生实现的映射（含完整代码）"""
    keyword = request.args.get('keyword', '').strip()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(int(request.args.get('per_page', 50)), 200)

    try:
        dao = _get_dao()
        all_items = dao.get_mappings_by_type('native_python')

        if keyword:
            kw = keyword.lower()
            all_items = [m for m in all_items
                        if kw in m['gee_api']['api_full_name'].lower()
                        or kw in (m.get('native_python_code', '') or '').lower()]

        total = len(all_items)
        start = (page - 1) * per_page
        data = all_items[start:start + per_page]

        # 精简输出，代码截断
        simplified = []
        for m in data:
            item = {
                'gee_api': {
                    'full_name': m['gee_api']['api_full_name'],
                    'class_name': m['gee_api'].get('class_name', ''),
                    'description': m['gee_api'].get('description', '')[:200]
                },
                'oge_api': m['oge_api']['api_name'] if m['oge_api'] else None,
                'python_code_length': len(m.get('native_python_code') or ''),
                'python_code_preview': (m.get('native_python_code') or '')[:500],
                'confidence': m['confidence']
            }
            simplified.append(item)

        return jsonify({'success': True, 'total': total, 'page': page, 'per_page': per_page, 'data': simplified})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# API 路由 - GEE 示例代码
# ============================================================

@app.route('/api/gee-samplecodes', methods=['GET'])
def api_gee_samplecodes():
    """查询 GEE 示例代码列表（从数据库 gee_api_info 表查询，支持搜索和分页）

    Query 参数:
        keyword: 按全名/类名/描述搜索
        class:   按 GEE 类名过滤（如 ee.Image）
        page:    页码（默认 1）
        per_page: 每页条数（默认 50，上限 200）
    """
    keyword = request.args.get('keyword', '').strip()
    class_name = request.args.get('class', '').strip()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = min(int(request.args.get('per_page', 50)), 200)

    try:
        dao = _get_dao()
        conn = dao.conn

        # 构建查询条件
        conditions = ["samplecode IS NOT NULL"]  # 只返回有示例代码的
        params = []
        if keyword:
            conditions.append("(api_full_name LIKE ? OR description LIKE ?)")
            kw = f'%{keyword}%'
            params.extend([kw, kw])
        if class_name:
            conditions.append("class_name = ?")
            params.append(class_name)

        where_clause = f"WHERE {' AND '.join(conditions)}"

        # 总数
        count_sql = f"SELECT COUNT(*) FROM gee_api_info {where_clause}"
        total = conn.execute(count_sql, params).fetchone()[0]

        # 分页查询
        offset = (page - 1) * per_page
        query_sql = f"""SELECT api_full_name, class_name, method_name, return_type, description, samplecode, sample_source
                        FROM gee_api_info {where_clause}
                        ORDER BY class_name, method_name
                        LIMIT ? OFFSET ?"""
        rows = conn.execute(query_sql, params + [per_page, offset]).fetchall()

        data = []
        for row in rows:
            data.append({
                'fullName': row['api_full_name'],
                'className': row['class_name'],
                'methodName': row['method_name'],
                'returns': row['return_type'],
                'description': row['description'] or '',
                'samplecode': row['samplecode'] or '',
                'source': row['sample_source'] or 'generated'
            })

        return jsonify({
            'success': True,
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': data
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gee-samplecode/<path:gee_name>', methods=['GET'])
def api_gee_samplecode_detail(gee_name):
    """查询单个 GEE API 的示例代码详情（从数据库查询）

    路径参数:
        gee_name: GEE API 全名（如 ee.Image.abs）
    """
    try:
        from urllib.parse import unquote
        gee_name = unquote(gee_name)

        dao = _get_dao()
        conn = dao.conn

        row = conn.execute(
            """SELECT api_full_name, class_name, method_name, return_type, description, 
                      arg_types, arg_names, samplecode, samplecodes, sample_source
               FROM gee_api_info WHERE api_full_name = ?""",
            (gee_name,)
        ).fetchone()

        if row is None:
            return jsonify({'success': False, 'error': '未找到该 API'}), 404

        # 解析参数信息：优先使用 arg_names（包含参数名），如果没有则用 arg_types
        arg_names = []
        if row['arg_names']:
            arg_names = json.loads(row['arg_names'])
        elif row['arg_types']:
            arg_types_list = json.loads(row['arg_types'])
            for i, at in enumerate(arg_types_list):
                arg_names.append({
                    'name': f'param{i+1}',
                    'type': at if isinstance(at, str) else str(at),
                    'details': ''
                })

        # 解析多个示例代码
        samplecodes = []
        if row['samplecodes']:
            samplecodes = json.loads(row['samplecodes'])
        
        # 如果没有多个示例，但有单个 samplecode，创建一个示例
        if not samplecodes and row['samplecode']:
            samplecodes = [{'order': 1, 'code': row['samplecode']}]

        return jsonify({
            'success': True,
            'data': {
                'fullName': row['api_full_name'],
                'className': row['class_name'],
                'methodName': row['method_name'],
                'returns': row['return_type'],
                'description': row['description'] or '',
                'arguments': arg_names,
                'samplecode': row['samplecode'] or '',
                'samplecodes': samplecodes,
                'source': row['sample_source'] or 'generated'
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 测试记录管理接口
# ============================================================

@app.route('/api/test-records', methods=['POST'])
def save_test_record():
    """保存测试记录

    Body JSON:
        api_id: 接口ID
        api_path: 接口路径
        method: 请求方法
        request_params: 请求参数（JSON字符串）
        request_time: 请求时间（ISO格式）
        status_code: 响应状态码
        response_time: 响应耗时（毫秒）
        response_body: 响应体（JSON字符串）
        success: 是否成功
        error_message: 错误信息
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体为空'}), 400

        dao = _get_dao()
        conn = dao.conn

        conn.execute(
            """INSERT INTO test_records
               (api_id, api_path, method, request_params, request_time, status_code, response_time, response_body, success, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get('api_id'),
                data.get('api_path'),
                data.get('method'),
                data.get('request_params'),
                data.get('request_time'),
                data.get('status_code'),
                data.get('response_time'),
                data.get('response_body'),
                data.get('success', 0),
                data.get('error_message')
            )
        )
        conn.commit()

        record_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        return jsonify({'success': True, 'id': record_id})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-records', methods=['GET'])
def list_test_records():
    """查询测试记录列表

    Query 参数:
        api_id: 按接口ID过滤（可选）
        success: 按成功状态过滤（可选，'true'/'false'）
        page: 页码（默认1）
        per_page: 每页条数（默认20，上限100）
    """
    try:
        api_id = request.args.get('api_id', '').strip()
        success_filter = request.args.get('success', '').strip()
        page = max(int(request.args.get('page', 1)), 1)
        per_page = min(int(request.args.get('per_page', 20)), 100)

        dao = _get_dao()
        conn = dao.conn

        conditions = []
        params = []

        if api_id:
            conditions.append('api_id = ?')
            params.append(api_id)

        if success_filter == 'true':
            conditions.append('success = 1')
        elif success_filter == 'false':
            conditions.append('success = 0')

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ''

        # 总数
        count_sql = f"SELECT COUNT(*) FROM test_records {where_clause}"
        total = conn.execute(count_sql, params).fetchone()[0]

        # 分页查询
        offset = (page - 1) * per_page
        query_sql = f"""SELECT id, api_id, api_path, method, request_params, request_time, status_code, response_time, success, error_message
                        FROM test_records {where_clause}
                        ORDER BY request_time DESC
                        LIMIT ? OFFSET ?"""
        rows = conn.execute(query_sql, params + [per_page, offset]).fetchall()

        data = []
        for row in rows:
            data.append({
                'id': row['id'],
                'api_id': row['api_id'],
                'api_path': row['api_path'],
                'method': row['method'],
                'request_params': row['request_params'],
                'request_time': row['request_time'],
                'status_code': row['status_code'],
                'response_time': row['response_time'],
                'success': bool(row['success']),
                'error_message': row['error_message'] or ''
            })

        return jsonify({
            'success': True,
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': data
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-records/<int:record_id>', methods=['GET'])
def get_test_record_detail(record_id):
    """查询单条测试记录详情（含响应体）"""
    try:
        dao = _get_dao()
        conn = dao.conn

        row = conn.execute(
            """SELECT id, api_id, api_path, method, request_params, request_time, status_code, response_time, response_body, success, error_message
               FROM test_records WHERE id = ?""",
            (record_id,)
        ).fetchone()

        if row is None:
            return jsonify({'success': False, 'error': '记录不存在'}), 404

        return jsonify({
            'success': True,
            'data': {
                'id': row['id'],
                'api_id': row['api_id'],
                'api_path': row['api_path'],
                'method': row['method'],
                'request_params': row['request_params'],
                'request_time': row['request_time'],
                'status_code': row['status_code'],
                'response_time': row['response_time'],
                'response_body': row['response_body'],
                'success': bool(row['success']),
                'error_message': row['error_message'] or ''
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-records/<int:record_id>', methods=['DELETE'])
def delete_test_record(record_id):
    """删除单条测试记录"""
    try:
        dao = _get_dao()
        conn = dao.conn

        conn.execute('DELETE FROM test_records WHERE id = ?', (record_id,))
        conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-records/clear', methods=['POST'])
def clear_test_records():
    """清空所有测试记录"""
    try:
        dao = _get_dao()
        conn = dao.conn

        conn.execute('DELETE FROM test_records')
        conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-records/stats', methods=['GET'])
def get_test_records_stats():
    """获取测试记录统计信息"""
    try:
        dao = _get_dao()
        conn = dao.conn

        total = conn.execute('SELECT COUNT(*) FROM test_records').fetchone()[0]
        success_count = conn.execute('SELECT COUNT(*) FROM test_records WHERE success = 1').fetchone()[0]
        fail_count = total - success_count

        # 按接口分组统计
        api_stats = conn.execute(
            """SELECT api_id, COUNT(*) as count, SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
               FROM test_records GROUP BY api_id ORDER BY count DESC LIMIT 10"""
        ).fetchall()

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'success_count': success_count,
                'fail_count': fail_count,
                'api_stats': [{'api_id': r['api_id'], 'count': r['count'], 'success_count': r['success_count']} for r in api_stats]
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 成功案例接口
# ============================================================

EXAMPLES_DIR = os.path.join(PROJECT_ROOT, 'resource', 'examples')

@app.route('/api/examples', methods=['GET'])
def get_examples():
    """获取成功案例列表"""
    try:
        examples = []
        if not os.path.exists(EXAMPLES_DIR):
            return jsonify({'success': True, 'examples': []})

        for case_dir in os.listdir(EXAMPLES_DIR):
            case_path = os.path.join(EXAMPLES_DIR, case_dir)
            if not os.path.isdir(case_path):
                continue

            meta_path = os.path.join(case_path, 'meta.json')
            if not os.path.exists(meta_path):
                continue

            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            examples.append({
                'id': meta.get('id', case_dir),
                'name': meta.get('name', case_dir),
                'description': meta.get('description', ''),
                'tags': meta.get('tags', []),
                'source': meta.get('source', ''),
                'difficulty': meta.get('difficulty', 'medium')
            })

        # 按 difficulty 排序
        difficulty_order = {'easy': 0, 'medium': 1, 'hard': 2}
        examples.sort(key=lambda x: difficulty_order.get(x['difficulty'], 1))

        return jsonify({'success': True, 'examples': examples})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/examples/<case_id>', methods=['GET'])
def get_example_detail(case_id):
    """获取案例详情（含 GEE 和 OGE 代码）"""
    try:
        case_path = os.path.join(EXAMPLES_DIR, case_id)
        if not os.path.exists(case_path):
            return jsonify({'success': False, 'error': '案例不存在'}), 404

        # 读取元数据
        meta_path = os.path.join(case_path, 'meta.json')
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

        # 读取 GEE 代码
        gee_path = os.path.join(case_path, 'gee.txt')
        gee_code = ''
        if os.path.exists(gee_path):
            with open(gee_path, 'r', encoding='utf-8') as f:
                gee_code = f.read()

        # 读取 OGE 代码
        oge_path = os.path.join(case_path, 'oge.txt')
        oge_code = ''
        if os.path.exists(oge_path):
            with open(oge_path, 'r', encoding='utf-8') as f:
                oge_code = f.read()

        return jsonify({
            'success': True,
            'example': {
                'id': meta.get('id', case_id),
                'name': meta.get('name', case_id),
                'description': meta.get('description', ''),
                'tags': meta.get('tags', []),
                'source': meta.get('source', ''),
                'difficulty': meta.get('difficulty', 'medium'),
                'gee_code': gee_code,
                'oge_code': oge_code
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/examples', methods=['POST'])
def add_example():
    """手动添加新案例

    接收案例数据（名称、GEE代码、可选的OGE代码等），
    在 resource/examples/ 下创建新目录并保存案例文件。

    请求体 JSON 格式：
        {
            "name": "案例名称",          // 必填
            "gee_code": "GEE 代码",      // 必填
            "oge_code": "OGE 代码",      // 可选
            "description": "案例描述",    // 可选
            "tags": ["标签1", "标签2"],   // 可选
            "source": "数据来源",         // 可选
            "difficulty": "easy/medium/hard"  // 可选，默认 medium
        }

    Returns:
        JSON: 包含新案例 id 和基本信息
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400

        name = (data.get('name') or '').strip()
        gee_code = (data.get('gee_code') or '').strip()

        if not name:
            return jsonify({'success': False, 'error': '案例名称不能为空'}), 400
        if not gee_code:
            return jsonify({'success': False, 'error': 'GEE 代码不能为空'}), 400

        # 生成案例 ID：基于名称的安全 slug + 时间戳避免重名
        import re as _re
        import time
        safe_name = _re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', name)
        safe_name = safe_name.strip('_')
        if not safe_name:
            safe_name = 'case'
        case_id = f"{safe_name}_{int(time.time())}"

        # 检查目录是否已存在
        case_path = os.path.join(EXAMPLES_DIR, case_id)
        if os.path.exists(case_path):
            return jsonify({'success': False, 'error': '案例目录已存在，请稍后重试'}), 409

        # 创建案例目录
        os.makedirs(case_path, exist_ok=True)

        # 保存 meta.json
        meta = {
            'id': case_id,
            'name': name,
            'description': (data.get('description') or '').strip(),
            'tags': data.get('tags') or [],
            'source': (data.get('source') or '').strip(),
            'created_at': time.strftime('%Y-%m-%d'),
            'difficulty': (data.get('difficulty') or 'medium').strip()
        }
        meta_path = os.path.join(case_path, 'meta.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 保存 gee.txt
        gee_path = os.path.join(case_path, 'gee.txt')
        with open(gee_path, 'w', encoding='utf-8') as f:
            f.write(gee_code)

        # 保存 oge.txt（可选）
        oge_code = (data.get('oge_code') or '').strip()
        if oge_code:
            oge_path = os.path.join(case_path, 'oge.txt')
            with open(oge_path, 'w', encoding='utf-8') as f:
                f.write(oge_code)

        return jsonify({
            'success': True,
            'example': {
                'id': case_id,
                'name': name,
                'description': meta['description'],
                'tags': meta['tags'],
                'source': meta['source'],
                'difficulty': meta['difficulty']
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/examples/<case_id>', methods=['PUT'])
def update_example(case_id):
    """修改已有案例

    可更新案例的名称、描述、标签、来源、难度等级、GEE代码和OGE代码。
    只需要提供要更新的字段，未提供的字段保持原值不变。

    请求体 JSON 格式：
        {
            "name": "新案例名称",        // 可选
            "gee_code": "新 GEE 代码",   // 可选
            "oge_code": "新 OGE 代码",   // 可选
            "description": "新描述",      // 可选
            "tags": ["新标签"],          // 可选
            "source": "新来源",          // 可选
            "difficulty": "easy/medium/hard"  // 可选
        }

    Returns:
        JSON: 更新后的案例信息
    """
    try:
        case_path = os.path.join(EXAMPLES_DIR, case_id)
        if not os.path.exists(case_path):
            return jsonify({'success': False, 'error': '案例不存在'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400

        # 读取现有元数据
        meta_path = os.path.join(case_path, 'meta.json')
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

        # 更新元数据字段
        if 'name' in data:
            new_name = (data.get('name') or '').strip()
            if not new_name:
                return jsonify({'success': False, 'error': '案例名称不能为空'}), 400
            meta['name'] = new_name

        if 'description' in data:
            meta['description'] = (data.get('description') or '').strip()

        if 'tags' in data:
            meta['tags'] = data.get('tags') or []

        if 'source' in data:
            meta['source'] = (data.get('source') or '').strip()

        if 'difficulty' in data:
            meta['difficulty'] = (data.get('difficulty') or 'medium').strip()

        # 保存更新后的元数据
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 更新 GEE 代码
        if 'gee_code' in data:
            gee_code = (data.get('gee_code') or '').strip()
            gee_path = os.path.join(case_path, 'gee.txt')
            with open(gee_path, 'w', encoding='utf-8') as f:
                f.write(gee_code)

        # 更新 OGE 代码
        if 'oge_code' in data:
            oge_code = (data.get('oge_code') or '').strip()
            oge_path = os.path.join(case_path, 'oge.txt')
            if oge_code:
                with open(oge_path, 'w', encoding='utf-8') as f:
                    f.write(oge_code)
            elif os.path.exists(oge_path):
                os.remove(oge_path)

        return jsonify({
            'success': True,
            'example': {
                'id': meta.get('id', case_id),
                'name': meta.get('name', case_id),
                'description': meta.get('description', ''),
                'tags': meta.get('tags', []),
                'source': meta.get('source', ''),
                'difficulty': meta.get('difficulty', 'medium')
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/examples/<case_id>', methods=['DELETE'])
def delete_example(case_id):
    """删除案例

    根据案例 ID 删除整个案例目录及其下的所有文件
    （meta.json、gee.txt、oge.txt）。

    Returns:
        JSON: 删除结果
    """
    try:
        case_path = os.path.join(EXAMPLES_DIR, case_id)
        if not os.path.exists(case_path):
            return jsonify({'success': False, 'error': '案例不存在'}), 404

        # 递归删除案例目录
        import shutil
        shutil.rmtree(case_path)

        return jsonify({
            'success': True,
            'message': f'案例 {case_id} 已删除'
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/examples/analyze', methods=['POST'])
def analyze_example_metadata():
    """使用 LLM 智能分析案例代码，自动提取元数据信息

    接收 GEE 代码（和可选的 OGE 代码），调用 LLM 分析代码意图，
    自动生成案例名称、描述、标签、来源和难度等级。

    请求体 JSON 格式：
        {
            "gee_code": "GEE JavaScript 代码",    // 必填
            "oge_code": "OGE Python 代码"         // 可选
        }

    Returns:
        JSON: 包含建议的案例元数据
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求体不能为空'}), 400

        gee_code = (data.get('gee_code') or '').strip()
        oge_code = (data.get('oge_code') or '').strip()

        if not gee_code:
            return jsonify({'success': False, 'error': 'GEE 代码不能为空'}), 400

        from llm_service import get_llm_service
        llm = get_llm_service()

        if not llm.is_available():
            return jsonify({
                'success': False,
                'error': 'LLM 服务不可用，请确保 Ollama 或其他 LLM 服务已启动'
            }), 503

        metadata = llm.analyze_case_metadata(gee_code, oge_code)

        return jsonify({
            'success': True,
            'metadata': metadata
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'分析失败: {str(e)}'}), 500


# ============================================================
# Benchmark 测试集 & OGE→GEE 反向转换
# ============================================================

@app.route('/api/benchmark-cases', methods=['GET'])
def get_benchmark_cases():
    """获取 benchmark 测试集案例列表

    返回 benchmark_with_dag_rebalanced_v4.json 中所有案例的摘要信息。
    每个案例包含 case_id、description、task_type、difficulty、code（OGE 代码）等字段。

    Returns:
        JSON: {success: bool, cases: [...], total: int}
    """
    import json
    json_path = os.path.join(os.path.dirname(__file__), 'static', 'testdata',
                             'benchmark_with_dag_rebalanced_v4.json')
    if not os.path.exists(json_path):
        return jsonify({'success': False, 'error': 'Benchmark 文件不存在'}), 404

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)

        # 只返回摘要信息（不含 dag 等大字段，减少传输量）
        summaries = []
        for c in cases:
            summaries.append({
                'case_id': c.get('case_id', ''),
                'task_type': c.get('task_type', ''),
                'description': c.get('description', ''),
                'difficulty': c.get('difficulty', ''),
                'lang': c.get('lang', ''),
                'code_length': len(c.get('code', '')),
                'notes': c.get('notes', ''),
                'data_ref': c.get('data_ref', '')
            })

        return jsonify({'success': True, 'cases': summaries, 'total': len(summaries)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'读取 benchmark 失败: {str(e)}'}), 500


@app.route('/api/benchmark-case/<case_id>', methods=['GET'])
def get_benchmark_case_detail(case_id):
    """获取单个 benchmark 案例的完整信息（含 OGE 代码）

    Args:
        case_id: 案例 ID（如 T0001）

    Returns:
        JSON: {success: bool, case: {...}}
    """
    import json
    json_path = os.path.join(os.path.dirname(__file__), 'static', 'testdata',
                             'benchmark_with_dag_rebalanced_v4.json')
    if not os.path.exists(json_path):
        return jsonify({'success': False, 'error': 'Benchmark 文件不存在'}), 404

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)

        for c in cases:
            if c.get('case_id') == case_id:
                return jsonify({'success': True, 'case': c})

        return jsonify({'success': False, 'error': f'案例 {case_id} 不存在'}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'读取失败: {str(e)}'}), 500


@app.route('/api/oge-to-gee', methods=['POST'])
def api_oge_to_gee():
    """OGE 代码反向转换为 GEE JavaScript 代码

    使用 LLM 分析 OGE Python 代码的语义和算子调用，
    映射回等效的 Google Earth Engine JavaScript 代码。

    Request Body:
        oge_code: OGE Python 代码
        description: 任务描述（可选）

    Returns:
        JSON: {success: bool, gee_code: str, explanations: [...], warnings: [...]}
    """
    data = request.get_json() or {}
    oge_code = data.get('oge_code', '').strip()
    description = data.get('description', '')

    if not oge_code:
        return jsonify({'success': False, 'error': 'OGE 代码不能为空'}), 400

    try:
        llm = get_llm_service()
        if not llm.is_available():
            return jsonify({
                'success': False,
                'error': 'LLM 服务不可用，请检查本地大模型 API 连接'
            }), 503

        import time
        _t0 = time.time()
        result = llm.oge_to_gee(oge_code, description)
        elapsed = time.time() - _t0

        return jsonify({
            'success': True,
            'gee_code': result.get('gee_code', ''),
            'explanations': result.get('explanations', []),
            'warnings': result.get('warnings', []),
            'feasible': result.get('feasible', True),
            'elapsed_ms': round(elapsed * 1000, 1)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'OGE→GEE 转换失败: {str(e)}'}), 500


# ============================================================
# Benchmark 批量转换接口
# ============================================================

BENCHMARK_RESULT_FILE = os.path.join(
    PROJECT_ROOT, 'resource', 'benchmark_convert_results.json'
)

# 全局后台任务状态：{task_id: {status, progress, ...}}
_benchmark_tasks = {}
_benchmark_tasks_lock = threading.Lock()


def _load_benchmark_cases():
    """加载 benchmark 测试集案例

    Returns:
        list: 案例列表，每个案例包含 case_id、code、gee、description 等字段
    """
    json_path = os.path.join(
        os.path.dirname(__file__), 'static', 'testdata',
        'benchmark_with_dag_rebalanced_v4.json'
    )
    if not os.path.exists(json_path):
        return None, 'Benchmark 文件不存在'

    with open(json_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    return cases, None


def _save_benchmark_results(results):
    """保存批量转换结果到 JSON 文件

    Args:
        results: 批量转换结果字典
    """
    os.makedirs(os.path.dirname(BENCHMARK_RESULT_FILE), exist_ok=True)
    with open(BENCHMARK_RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _load_benchmark_results():
    """加载已保存的批量转换结果

    Returns:
        dict or None: 已保存的结果，不存在返回 None
    """
    if os.path.exists(BENCHMARK_RESULT_FILE):
        with open(BENCHMARK_RESULT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def _run_benchmark_batch(task_id, cases, llm, force):
    """
    后台线程：逐个转换 benchmark 案例并实时保存

    Args:
        task_id: 任务 ID
        cases: 待转换的案例列表
        llm: LLM 服务实例
        force: 是否强制重新转换
    """
    # 加载已有结果（用于断点续跑）
    existing = {}
    if not force:
        saved = _load_benchmark_results()
        if saved:
            for r in saved.get('results', []):
                existing[r.get('case_id')] = r

    batch_start = time.time()
    results = list(existing.values())
    # 从已有结果中恢复计数
    converted = sum(1 for r in results if r.get('status') == 'success')
    skipped = sum(1 for r in results if r.get('status') == 'skipped')
    failed = sum(1 for r in results if r.get('status') == 'failed')
    total = len(cases)

    with _benchmark_tasks_lock:
        _benchmark_tasks[task_id]['total'] = total
        _benchmark_tasks[task_id]['status'] = 'running'

    for i, case in enumerate(cases):
        case_id = case.get('case_id', f'unknown_{i}')

        # 断点续跑：跳过已完成的案例
        if not force and case_id in existing:
            skipped += 1
            with _benchmark_tasks_lock:
                _benchmark_tasks[task_id]['skipped'] = skipped
                _benchmark_tasks[task_id]['progress'] = round((i + 1) / total * 100, 1)
            continue

        oge_code = case.get('code', '').strip()
        description = case.get('description', '')

        if not oge_code:
            failed += 1
            results.append({
                'case_id': case_id,
                'status': 'skipped',
                'error': 'OGE 代码为空',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
            })
        else:
            print(f'[Batch Convert] ({i+1}/{total}) 转换案例 {case_id} ...')
            try:
                t0 = time.time()
                result = llm.oge_to_gee(oge_code, description)
                elapsed = time.time() - t0

                ground_truth_gee = case.get('gee', '')
                results.append({
                    'case_id': case_id,
                    'task_type': case.get('task_type', ''),
                    'difficulty': case.get('difficulty', ''),
                    'description': description,
                    'oge_code': oge_code,
                    'ground_truth_gee': ground_truth_gee,
                    'llm_gee_code': result.get('gee_code', ''),
                    'explanations': result.get('explanations', []),
                    'warnings': result.get('warnings', []),
                    'feasible': result.get('feasible', True),
                    'elapsed_ms': round(elapsed * 1000, 1),
                    'status': 'success',
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                })
                converted += 1
            except Exception as e:
                traceback.print_exc()
                failed += 1
                results.append({
                    'case_id': case_id,
                    'task_type': case.get('task_type', ''),
                    'difficulty': case.get('difficulty', ''),
                    'description': description,
                    'oge_code': oge_code,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                })

        # 每处理完一个案例就保存一次
        batch_data = {
            'total': total,
            'converted': converted,
            'skipped': skipped,
            'failed': failed,
            'elapsed_ms': round((time.time() - batch_start) * 1000, 1),
            'results': results
        }
        _save_benchmark_results(batch_data)

        with _benchmark_tasks_lock:
            _benchmark_tasks[task_id]['converted'] = converted
            _benchmark_tasks[task_id]['skipped'] = skipped
            _benchmark_tasks[task_id]['failed'] = failed
            _benchmark_tasks[task_id]['progress'] = round((i + 1) / total * 100, 1)
            _benchmark_tasks[task_id]['elapsed_ms'] = round((time.time() - batch_start) * 1000, 1)

    total_elapsed = time.time() - batch_start

    # 最终保存
    batch_data = {
        'total': total,
        'converted': converted,
        'skipped': skipped,
        'failed': failed,
        'elapsed_ms': round(total_elapsed * 1000, 1),
        'results': results
    }
    _save_benchmark_results(batch_data)

    with _benchmark_tasks_lock:
        _benchmark_tasks[task_id]['status'] = 'completed'
        _benchmark_tasks[task_id]['progress'] = 100.0
        _benchmark_tasks[task_id]['elapsed_ms'] = round(total_elapsed * 1000, 1)


@app.route('/api/benchmark-batch-convert', methods=['POST'])
def api_benchmark_batch_convert():
    """批量将 benchmark 测试集的 OGE 代码转换为 GEE 代码（异步模式）

    立即返回任务 ID，后台线程逐个案例调用 LLM 的 oge_to_gee 方法。
    支持按 difficulty / task_type 过滤，支持断点续跑。
    结果实时写入 resource/benchmark_convert_results.json。
    使用 GET /api/benchmark-batch-status?task_id=... 查询进度。

    Request Body:
        difficulty: 可选，按难度过滤（如 "简单"/"中等"/"困难"）
        task_type: 可选，按任务类型过滤（如 "image_processing"）
        resume: 是否断点续跑，默认 true（跳过已有结果的案例）
        force: 是否强制重新转换所有案例，默认 false

    Returns:
        JSON: {
            success: bool,
            task_id: str,         // 任务 ID，用于查询进度
            message: str,         // 提示信息
            total: int            // 待转换案例数
        }
    """
    import uuid
    data = request.get_json() or {}
    difficulty = data.get('difficulty', '').strip()
    task_type = data.get('task_type', '').strip()
    resume = data.get('resume', True)
    force = data.get('force', False)

    # 加载 benchmark 案例
    cases, err = _load_benchmark_cases()
    if err:
        return jsonify({'success': False, 'error': err}), 404

    # 过滤案例
    if difficulty:
        cases = [c for c in cases if c.get('difficulty') == difficulty]
    if task_type:
        cases = [c for c in cases if c.get('task_type') == task_type]

    if not cases:
        return jsonify({'success': False, 'error': '没有符合条件的案例'}), 400

    # 检查 LLM 可用性
    llm = get_llm_service()
    llm.reset_availability()
    if not llm.is_available():
        return jsonify({
            'success': False,
            'error': 'LLM 服务不可用，请检查本地大模型 API 连接'
        }), 503

    # 生成任务 ID 并启动后台线程
    task_id = str(uuid.uuid4())[:8]
    with _benchmark_tasks_lock:
        _benchmark_tasks[task_id] = {
            'status': 'pending',
            'total': len(cases),
            'converted': 0,
            'skipped': 0,
            'failed': 0,
            'progress': 0.0,
            'elapsed_ms': 0,
            'start_time': time.strftime('%Y-%m-%dT%H:%M:%S')
        }

    t = threading.Thread(
        target=_run_benchmark_batch,
        args=(task_id, cases, llm, force),
        daemon=True
    )
    t.start()

    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': f'已启动后台批量转换任务，共 {len(cases)} 个案例。使用 GET /api/benchmark-batch-status?task_id={task_id} 查询进度。',
        'total': len(cases)
    })


@app.route('/api/benchmark-batch-status', methods=['GET'])
def api_benchmark_batch_status():
    """查询 benchmark 批量转换任务的进度

    Query Parameters:
        task_id: 任务 ID（由 POST /api/benchmark-batch-convert 返回）
        不传 task_id 时返回所有任务的简要状态

    Returns:
        JSON: {success: bool, data: {...}}
    """
    task_id = request.args.get('task_id', '').strip()

    if task_id:
        with _benchmark_tasks_lock:
            task = _benchmark_tasks.get(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
        return jsonify({'success': True, 'data': task})

    # 返回所有任务的简要状态
    with _benchmark_tasks_lock:
        all_tasks = [
            {'task_id': tid, **{k: v for k, v in t.items() if k != 'results'}}
            for tid, t in _benchmark_tasks.items()
        ]
    return jsonify({'success': True, 'tasks': all_tasks})


@app.route('/api/benchmark-batch-result', methods=['GET'])
def api_benchmark_batch_result():
    """获取已保存的 benchmark 批量转换结果

    Returns:
        JSON: {success: bool, data: {...}}
    """
    saved = _load_benchmark_results()
    if saved is None:
        return jsonify({
            'success': True,
            'data': {
                'total': 0,
                'converted': 0,
                'skipped': 0,
                'failed': 0,
                'elapsed_ms': 0,
                'results': [],
                'message': '暂无批量转换结果，请先调用 POST /api/benchmark-batch-convert'
            }
        })
    return jsonify({'success': True, 'data': saved})


@app.route('/api/benchmark-batch-result', methods=['DELETE'])
def api_benchmark_batch_result_clear():
    """清空已保存的 benchmark 批量转换结果

    Returns:
        JSON: {success: bool}
    """
    try:
        if os.path.exists(BENCHMARK_RESULT_FILE):
            os.remove(BENCHMARK_RESULT_FILE)
        return jsonify({'success': True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/benchmark-batch-status/<task_id>', methods=['DELETE'])
def api_benchmark_batch_status_clear(task_id):
    """清除已完成的任务状态记录

    Args:
        task_id: 任务 ID

    Returns:
        JSON: {success: bool}
    """
    with _benchmark_tasks_lock:
        if task_id in _benchmark_tasks:
            del _benchmark_tasks[task_id]
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404


# ============================================================
# GEE→OGE 批量转换接口（基于 filtered benchmark）
# ============================================================

GEE_BENCHMARK_FILE = os.path.join(
    os.path.dirname(__file__), 'static', 'testdata', 'data',
    'gee_good', 'benchmark_with_dag_rebalanced_v4_filtered.json'
)

OGE_BENCHMARK_FILE = os.path.join(
    os.path.dirname(__file__), 'static', 'testdata', 'data',
    'oge_good', 'benchmark_with_dag_rebalanced_v4_filtered.json'
)

GEE_BATCH_RESULT_FILE = os.path.join(
    PROJECT_ROOT, 'resource', 'gee_to_oge_batch_results.json'
)

_gee_batch_tasks = {}
_gee_batch_tasks_lock = threading.Lock()


def _load_gee_benchmark_cases():
    """加载 GEE filtered benchmark 案例列表

    Returns:
        tuple: (cases, error) - 案例列表和错误信息
    """
    if not os.path.exists(GEE_BENCHMARK_FILE):
        return None, f'GEE Benchmark 文件不存在: {GEE_BENCHMARK_FILE}'

    with open(GEE_BENCHMARK_FILE, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    oge_truth = {}
    if os.path.exists(OGE_BENCHMARK_FILE):
        with open(OGE_BENCHMARK_FILE, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                oge_truth[item.get('case_id')] = item.get('code', '')

    for c in cases:
        c['oge_truth'] = oge_truth.get(c.get('case_id'), '')

    return cases, None


def _save_gee_batch_results(results):
    """保存 GEE→OGE 批量转换结果"""
    os.makedirs(os.path.dirname(GEE_BATCH_RESULT_FILE), exist_ok=True)
    with open(GEE_BATCH_RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _load_gee_batch_results():
    """加载已保存的 GEE→OGE 批量转换结果"""
    if os.path.exists(GEE_BATCH_RESULT_FILE):
        with open(GEE_BATCH_RESULT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def _run_gee_batch(task_id, cases, llm, dao, force):
    """后台线程：逐个将 GEE 代码转换为 OGE 代码

    Args:
        task_id: 任务 ID
        cases: 待转换的案例列表
        llm: LLM 服务实例
        dao: 数据访问对象
        force: 是否强制重新转换
    """
    existing = {}
    if not force:
        saved = _load_gee_batch_results()
        if saved:
            for r in saved.get('results', []):
                existing[r.get('case_id')] = r

    batch_start = time.time()
    results = list(existing.values())
    converted = sum(1 for r in results if r.get('status') == 'success')
    skipped = sum(1 for r in results if r.get('status') == 'skipped')
    failed = sum(1 for r in results if r.get('status') == 'failed')
    total = len(cases)

    with _gee_batch_tasks_lock:
        _gee_batch_tasks[task_id]['total'] = total
        _gee_batch_tasks[task_id]['status'] = 'running'

    for i, case in enumerate(cases):
        case_id = case.get('case_id', f'unknown_{i}')
        gee_code = case.get('gee', '').strip()

        if not force and case_id in existing:
            skipped += 1
            with _gee_batch_tasks_lock:
                _gee_batch_tasks[task_id]['skipped'] = skipped
                _gee_batch_tasks[task_id]['progress'] = round((i + 1) / total * 100, 1)
            continue

        if not gee_code:
            failed += 1
            results.append({
                'case_id': case_id,
                'status': 'skipped',
                'error': 'GEE 代码为空',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
            })
        else:
            print(f'[GEE→OGE Batch] ({i+1}/{total}) 转换案例 {case_id} ...')
            try:
                t0 = time.time()
                mapping_context = _build_mapping_context(dao, gee_code)
                result = llm.generate_oge_code(gee_code, mapping_context)
                elapsed = time.time() - t0

                ground_truth_oge = case.get('oge_truth', '')
                results.append({
                    'case_id': case_id,
                    'gee_code': gee_code,
                    'ground_truth_oge': ground_truth_oge,
                    'llm_oge_code': result.get('oge_code', ''),
                    'explanations': result.get('explanations', []),
                    'warnings': result.get('warnings', []),
                    'feasible': result.get('feasible', 'partial_feasible'),
                    'elapsed_ms': round(elapsed * 1000, 1),
                    'status': 'success',
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                })
                converted += 1
            except Exception as e:
                traceback.print_exc()
                failed += 1
                results.append({
                    'case_id': case_id,
                    'gee_code': gee_code,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                })

        batch_data = {
            'total': total,
            'converted': converted,
            'skipped': skipped,
            'failed': failed,
            'elapsed_ms': round((time.time() - batch_start) * 1000, 1),
            'results': results
        }
        _save_gee_batch_results(batch_data)

        with _gee_batch_tasks_lock:
            _gee_batch_tasks[task_id]['converted'] = converted
            _gee_batch_tasks[task_id]['skipped'] = skipped
            _gee_batch_tasks[task_id]['failed'] = failed
            _gee_batch_tasks[task_id]['progress'] = round((i + 1) / total * 100, 1)
            _gee_batch_tasks[task_id]['elapsed_ms'] = round((time.time() - batch_start) * 1000, 1)

    total_elapsed = time.time() - batch_start

    batch_data = {
        'total': total,
        'converted': converted,
        'skipped': skipped,
        'failed': failed,
        'elapsed_ms': round(total_elapsed * 1000, 1),
        'results': results
    }
    _save_gee_batch_results(batch_data)

    with _gee_batch_tasks_lock:
        _gee_batch_tasks[task_id]['status'] = 'completed'
        _gee_batch_tasks[task_id]['progress'] = 100.0
        _gee_batch_tasks[task_id]['elapsed_ms'] = round(total_elapsed * 1000, 1)


@app.route('/api/gee-benchmark-cases', methods=['GET'])
def api_gee_benchmark_cases():
    """获取 GEE filtered benchmark 案例列表

    Returns:
        JSON: {success: bool, cases: [...], total: int}
    """
    cases, err = _load_gee_benchmark_cases()
    if err:
        return jsonify({'success': False, 'error': err}), 404

    summaries = []
    for c in cases:
        summaries.append({
            'case_id': c.get('case_id', ''),
            'gee_code_length': len(c.get('gee', '')),
            'has_oge_truth': bool(c.get('oge_truth', ''))
        })
    return jsonify({'success': True, 'cases': summaries, 'total': len(summaries)})


@app.route('/api/gee-benchmark-case/<case_id>', methods=['GET'])
def api_gee_benchmark_case_detail(case_id):
    """获取单个 GEE benchmark 案例详情

    Args:
        case_id: 案例 ID（如 T0001）

    Returns:
        JSON: {success: bool, case: {...}}
    """
    cases, err = _load_gee_benchmark_cases()
    if err:
        return jsonify({'success': False, 'error': err}), 404

    for c in cases:
        if c.get('case_id') == case_id:
            return jsonify({'success': True, 'case': c})

    return jsonify({'success': False, 'error': f'案例 {case_id} 不存在'}), 404


@app.route('/api/gee-benchmark-convert', methods=['POST'])
def api_gee_benchmark_convert():
    """异步批量将 GEE 代码转换为 OGE 代码（基于 filtered benchmark）

    立即返回任务 ID，后台线程逐个案例调用 LLM 的 generate_oge_code 方法。
    结果实时写入 resource/gee_to_oge_batch_results.json。
    使用 GET /api/gee-benchmark-status?task_id=... 查询进度。

    Request Body:
        resume: 是否断点续跑，默认 true
        force: 是否强制重新转换所有案例，默认 false

    Returns:
        JSON: {success: bool, task_id: str, message: str, total: int}
    """
    data = request.get_json() or {}
    resume = data.get('resume', True)
    force = data.get('force', False)

    cases, err = _load_gee_benchmark_cases()
    if err:
        return jsonify({'success': False, 'error': err}), 404

    if not cases:
        return jsonify({'success': False, 'error': '没有可转换的案例'}), 400

    llm = get_llm_service()
    llm.reset_availability()
    if not llm.is_available():
        return jsonify({
            'success': False,
            'error': 'LLM 服务不可用，请检查本地大模型 API 连接'
        }), 503

    dao = GeeOgeDao()

    task_id = str(uuid.uuid4())[:8]
    with _gee_batch_tasks_lock:
        _gee_batch_tasks[task_id] = {
            'status': 'pending',
            'total': len(cases),
            'converted': 0,
            'skipped': 0,
            'failed': 0,
            'progress': 0.0,
            'elapsed_ms': 0,
            'start_time': time.strftime('%Y-%m-%dT%H:%M:%S')
        }

    t = threading.Thread(
        target=_run_gee_batch,
        args=(task_id, cases, llm, dao, force),
        daemon=True
    )
    t.start()

    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': f'已启动后台 GEE→OGE 批量转换任务，共 {len(cases)} 个案例。使用 GET /api/gee-benchmark-status?task_id={task_id} 查询进度。',
        'total': len(cases)
    })


@app.route('/api/gee-benchmark-status', methods=['GET'])
def api_gee_benchmark_status():
    """查询 GEE→OGE 批量转换任务的进度

    Query Parameters:
        task_id: 可选，任务 ID。不传则返回所有任务

    Returns:
        JSON: {success: bool, data/tasks: ...}
    """
    task_id = request.args.get('task_id', '').strip()

    if task_id:
        with _gee_batch_tasks_lock:
            task = _gee_batch_tasks.get(task_id)
        if task is None:
            return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404
        return jsonify({'success': True, 'data': task})

    with _gee_batch_tasks_lock:
        all_tasks = [
            {'task_id': tid, **{k: v for k, v in t.items()}}
            for tid, t in _gee_batch_tasks.items()
        ]
    return jsonify({'success': True, 'tasks': all_tasks})


@app.route('/api/gee-benchmark-result', methods=['GET'])
def api_gee_benchmark_result():
    """获取已保存的 GEE→OGE 批量转换结果

    Returns:
        JSON: {success: bool, data: {...}}
    """
    saved = _load_gee_batch_results()
    if saved is None:
        return jsonify({
            'success': True,
            'data': {
                'total': 0,
                'converted': 0,
                'skipped': 0,
                'failed': 0,
                'elapsed_ms': 0,
                'results': [],
                'message': '暂无批量转换结果，请先调用 POST /api/gee-benchmark-convert'
            }
        })
    return jsonify({'success': True, 'data': saved})


@app.route('/api/gee-benchmark-result', methods=['DELETE'])
def api_gee_benchmark_result_clear():
    """清空已保存的 GEE→OGE 批量转换结果"""
    try:
        if os.path.exists(GEE_BATCH_RESULT_FILE):
            os.remove(GEE_BATCH_RESULT_FILE)
        return jsonify({'success': True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gee-benchmark-status/<task_id>', methods=['DELETE'])
def api_gee_benchmark_status_clear(task_id):
    """清除已完成的 GEE→OGE 任务状态记录"""
    with _gee_batch_tasks_lock:
        if task_id in _gee_batch_tasks:
            del _gee_batch_tasks[task_id]
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': f'任务 {task_id} 不存在'}), 404


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    import socket
    
    # 尝试多个端口启动服务
    ports = [5001, 5002, 5003, 5004, 8080]
    started = False
    
    for port in ports:
        try:
            # 测试端口是否可用
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_sock.bind(('127.0.0.1', port))
            test_sock.close()
            
            print("=" * 60)
            print("  GEE2OGE 迁移系统 Web 服务启动")
            print("=" * 60)
            print(f"  访问地址: http://127.0.0.1:{port}")
            print(f"  测试页面: http://127.0.0.1:{port}/test")
            print(f"  API 文档: http://127.0.0.1:{port}/api/stats")
            print("=" * 60)
            
            # 使用自定义服务器支持端口复用
            from werkzeug.serving import make_server
            server = make_server('127.0.0.1', port, app)
            print(f"  服务正在运行，按 Ctrl+C 停止...\n")
            server.serve_forever()
            started = True
            break
        except OSError as e:
            print(f"  端口 {port} 不可用 ({e})，尝试下一个端口...")
            continue
    
    if not started:
        print("错误: 所有端口都不可用，请检查网络配置或等待端口释放。")
        sys.exit(1)
