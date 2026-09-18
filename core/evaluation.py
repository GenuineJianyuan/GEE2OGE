"""代码迁移评估算法：AST 转图、图相似度与指标计算。

从主项目 ``experiment/eva/evaluate_results.py`` 中提取核心评估算法，
去除 LLM 裁判、实验批处理、数据库依赖，保留纯算法部分。

核心指标：
- NMR (Node Match Rate): 节点匹配率（节点标签 F1）
- EMR (Edge Match Rate): 边匹配率（边标签 F1）
- TS (Topological Similarity): 拓扑相似度（节点+边的加权综合，乘以规模惩罚）
- Node_Precision/Recall/F1: 节点精确率/召回率/F1
- LAM (Logical Accuracy Metric): 逻辑准确率（边召回率）
- PA (Perfect Accuracy): 是否完全匹配
- LD (Length Difference): 节点数差异
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


# ============================================================
# 图数据结构
# ============================================================

@dataclass
class Graph:
    """有向图数据结构。

    Attributes:
        node_label: 节点 ID → 节点标签（函数名/算子名）
        edges: 有向边列表 (源节点 ID, 目标节点 ID)
    """
    node_label: Dict[str, str] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def num_nodes(self) -> int:
        """节点数量。"""
        return len(self.node_label)

    @property
    def num_edges(self) -> int:
        """边数量。"""
        return len(self.edges)


# ============================================================
# 代码 → 图（AST 解析 + 正则回退）
# ============================================================

def _strip_code_fence(code: str) -> str:
    """去除代码块的 Markdown 围栏标记。

    Args:
        code: 可能包含 ``` 围栏的代码字符串

    Returns:
        str: 清理后的代码
    """
    if not isinstance(code, str):
        return code
    code = code.strip()
    code = re.sub(r'^\s*```[a-zA-Z0-9_+-]*\s*\n', '', code)
    code = re.sub(r'\n\s*```\s*$', '', code)
    return code.strip()


def _infer_obj_type_from_label(label: Optional[str]) -> str:
    """根据节点标签推断 OGE 对象类型。

    Args:
        label: 节点标签（算子名）

    Returns:
        str: 对象类型（Coverage / CoverageCollection / Feature / Geometry / Unknown）
    """
    if not label:
        return 'Unknown'
    if label == 'Service.getCoverage':
        return 'Coverage'
    if label == 'Service.getCoverageCollection':
        return 'CoverageCollection'
    if label == 'Service.getFeature':
        return 'Feature'
    if label.startswith('CoverageCollection.'):
        return 'CoverageCollection'
    if label.startswith('Coverage.'):
        return 'Coverage'
    if label.startswith('FeatureCollection.'):
        return 'FeatureCollection'
    if label.startswith('Feature.'):
        return 'Feature'
    if label.startswith('Geometry.'):
        return 'Geometry'
    return 'Unknown'


def _inject_global_roots(
    nodes_dict: Dict[str, str],
    edges_list: List[Tuple[str, str]],
) -> Tuple[Dict[str, str], List[Tuple[str, str]]]:
    """为 DAG 注入统一的 OGE 初始化起点。

    添加 oge.initialize → oge.Service → 所有根节点 的连线，
    确保图有统一的入口点。

    Args:
        nodes_dict: 节点标签字典
        edges_list: 边列表

    Returns:
        Tuple[Dict, List]: 注入后的节点和边
    """
    init_nid = 'global_init'
    svc_nid = 'global_service'

    # 统计当前所有节点的入度，寻找根节点
    in_degrees = {nid: 0 for nid in nodes_dict}
    for src, dst in edges_list:
        if dst in in_degrees:
            in_degrees[dst] += 1

    current_roots = [nid for nid, deg in in_degrees.items() if deg == 0]

    # 加入初始化节点
    nodes_dict[init_nid] = 'oge.initialize'
    nodes_dict[svc_nid] = 'oge.Service'

    # 连线：oge.initialize → oge.Service
    edges_list.append((init_nid, svc_nid))

    # 连线：oge.Service → 原有的根节点
    for r_nid in current_roots:
        edges_list.append((svc_nid, r_nid))

    return nodes_dict, edges_list


def _regex_extract_graph(code: str) -> Tuple[Optional[Graph], str]:
    """使用正则表达式从 OGE 代码中提取调用图（AST 解析失败时的回退方案）。

    识别 service.getCoverage / getCoverageCollection / getFeature / getProcess /
    styles / getMap / export / log 等调用，构建数据流依赖图。

    Args:
        code: OGE Python 代码

    Returns:
        Tuple[Optional[Graph], str]: (图对象, 状态说明)
    """
    lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
    node_label: Dict[str, str] = {}
    edges: List[Tuple[str, str]] = []
    env: Dict[str, str] = {}  # 变量名 → 节点 ID
    output_roots: List[Set[str]] = []
    seq = 0

    def _new_node(label: str, upstreams: Optional[List[str]] = None) -> str:
        """创建新节点并连接上游依赖。"""
        nonlocal seq
        seq += 1
        nid = f'r_{seq}'
        node_label[nid] = label
        if upstreams:
            for u in upstreams:
                if u in node_label:
                    edges.append((u, nid))
        return nid

    def _add_output_root(nid: Optional[str]) -> None:
        """记录输出根节点。"""
        if nid and nid in node_label:
            output_roots.append({nid})

    def _bind(lhs: Optional[str], nid: Optional[str]) -> None:
        """绑定变量名到节点 ID。"""
        if lhs and nid:
            env[lhs] = nid

    for ln in lines:
        # 去除行内注释
        if '#' in ln:
            ln = ln.split('#', 1)[0].strip()
        if not ln:
            continue

        lhs = None
        rhs = ln
        m_assign = re.match(r'^([A-Za-z_]\w*)\s*=\s*(.+)$', ln)
        if m_assign:
            lhs = m_assign.group(1)
            rhs = m_assign.group(2).strip()

        # 匹配 service.getProcess("xxx").execute(...)
        m_process = re.search(
            r'service\.getProcess\(\s*["\']([^"\']+)["\']\s*\)\.execute\(', rhs
        )
        if m_process:
            label = m_process.group(1)
            # 提取上游变量
            upstreams = [
                env[v] for v in re.findall(r'\b([A-Za-z_]\w*)\b', rhs)
                if v in env
            ]
            nid = _new_node(label, upstreams)
            _bind(lhs, nid)
            continue

        # service.getCoverage(...)
        if re.search(r'\bservice\.getCoverage\s*\(', rhs):
            nid = _new_node('Service.getCoverage')
            _bind(lhs, nid)
            continue

        # service.getCoverageCollection(...)
        if re.search(r'\bservice\.getCoverageCollection\s*\(', rhs):
            nid = _new_node('Service.getCoverageCollection')
            _bind(lhs, nid)
            continue

        # service.getFeature(...)
        if re.search(r'\bservice\.getFeature\s*\(', rhs):
            nid = _new_node('Service.getFeature')
            _bind(lhs, nid)
            continue

        # xxx.styles(...)
        m_styles = re.search(r'([A-Za-z_]\w*)\.styles\s*\(', rhs)
        if m_styles:
            base_var = m_styles.group(1)
            base_node = env.get(base_var)
            base_label = node_label.get(base_node) if base_node else None
            obj_type = _infer_obj_type_from_label(base_label)
            styles_label = f'{obj_type}.addStyles' if obj_type != 'Unknown' else 'Unknown.addStyles'
            nid = _new_node(styles_label, [base_node] if base_node else None)
            _bind(lhs, nid)
            # 链式调用 .getMap() / .export() / .log()
            if '.getMap(' in rhs:
                _add_output_root(nid)
            elif '.export(' in rhs:
                obj_type_export = _infer_obj_type_from_label(base_label)
                export_label = f'{obj_type_export}.export' if obj_type_export != 'Unknown' else 'Coverage.export'
                enid = _new_node(export_label, [nid])
                _add_output_root(enid)
            elif '.log(' in rhs:
                lnid = _new_node('Service.printString', [nid])
                _add_output_root(lnid)
            continue

        # xxx.getMap()
        m_getmap = re.search(r'([A-Za-z_]\w*)\.getMap\(', rhs)
        if m_getmap:
            _add_output_root(env.get(m_getmap.group(1)))
            continue

        # xxx.export()
        m_export = re.search(r'([A-Za-z_]\w*)\.export\(', rhs)
        if m_export:
            base_var = m_export.group(1)
            base_node = env.get(base_var)
            base_label = node_label.get(base_node) if base_node else None
            obj_type = _infer_obj_type_from_label(base_label)
            export_label = f'{obj_type}.export' if obj_type != 'Unknown' else 'Coverage.export'
            enid = _new_node(export_label, [base_node] if base_node else None)
            _add_output_root(enid)
            continue

        # xxx.log()
        m_log = re.search(r'([A-Za-z_]\w*)\.log\(', rhs)
        if m_log:
            base_var = m_log.group(1)
            base_node = env.get(base_var)
            lnid = _new_node('Service.printString', [base_node] if base_node else None)
            _add_output_root(lnid)
            continue

    if not node_label:
        return None, 'regex_no_nodes'

    if not output_roots:
        # 没有输出根节点，注入全局起点并返回
        nodes_fb, edges_fb = _inject_global_roots(node_label, edges)
        return Graph(node_label=nodes_fb, edges=edges_fb), 'regex_partial_no_output'

    # 从输出根节点反向剪枝，保留可达节点
    all_roots = set()
    for roots in output_roots:
        all_roots.update(roots)

    predecessors: Dict[str, Set[str]] = {}
    for src, dst in edges:
        predecessors.setdefault(dst, set()).add(src)

    keep: Set[str] = set()
    stack = list(all_roots)
    while stack:
        cur = stack.pop()
        if cur in keep:
            continue
        keep.add(cur)
        stack.extend(predecessors.get(cur, set()))

    sub_nodes = {nid: lbl for nid, lbl in node_label.items() if nid in keep}
    sub_edges = [(s, d) for s, d in edges if s in keep and d in keep]

    if not sub_nodes:
        return None, 'regex_failed'

    sub_nodes, sub_edges = _inject_global_roots(sub_nodes, sub_edges)
    return Graph(node_label=sub_nodes, edges=sub_edges), 'regex_success'


def infer_graph_from_code(code: Optional[str]) -> Tuple[Optional[Graph], str]:
    """从 OGE Python 代码中推断数据流图。

    优先使用 AST 解析，解析失败时回退到正则表达式提取。

    Args:
        code: OGE Python 代码

    Returns:
        Tuple[Optional[Graph], str]: (图对象, 状态说明)
    """
    if not code or not isinstance(code, str) or not code.strip():
        return None, 'no_code'

    code = _strip_code_fence(code)
    if not code:
        return None, 'empty_after_strip'

    # 尝试 AST 解析
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _regex_extract_graph(code)

    node_label: Dict[str, str] = {}
    edges: Set[Tuple[str, str]] = set()
    env: Dict[str, Set[str]] = {}  # 变量名 → 节点 ID 集合
    output_groups: List[Set[str]] = []
    node_seq = 0

    def _alloc_node(label: str) -> str:
        nonlocal node_seq
        node_seq += 1
        nid = f'n_{node_seq}'
        node_label[nid] = label
        return nid

    def _add_dependencies(target_nid: str, var_names: Iterable[str]) -> None:
        """为目标节点添加来自变量的依赖边。"""
        for v in var_names:
            if v in env:
                for src_nid in env[v]:
                    edges.add((src_nid, target_nid))

    # 遍历 AST 节点
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Assign):
            # 赋值语句：xxx = ...
            targets = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
            if not targets:
                continue

            # 分析右边的表达式
            rhs = stmt.value
            deps: Set[str] = set()
            process_label = None

            # 识别 service.getProcess("xxx").execute(...)
            if isinstance(rhs, ast.Call):
                if isinstance(rhs.func, ast.Attribute) and rhs.func.attr == 'execute':
                    if isinstance(rhs.func.value, ast.Call):
                        inner_call = rhs.func.value
                        if (isinstance(inner_call.func, ast.Attribute)
                                and inner_call.func.attr == 'getProcess'
                                and isinstance(inner_call.func.value, ast.Name)
                                and inner_call.func.value.id == 'service'
                                and inner_call.args):
                            arg0 = inner_call.args[0]
                            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                                process_label = arg0.value

                # 收集参数中的变量引用
                for node in ast.walk(rhs):
                    if isinstance(node, ast.Name) and node.id not in ('service', 'oge'):
                        deps.add(node.id)

            if process_label:
                nid = _alloc_node(process_label)
                _add_dependencies(nid, deps)
                for t in targets:
                    env.setdefault(t, set()).add(nid)
                continue

            # 识别 service.getCoverage() / getCoverageCollection() / getFeature()
            if isinstance(rhs, ast.Call):
                if (isinstance(rhs.func, ast.Attribute)
                        and isinstance(rhs.func.value, ast.Name)
                        and rhs.func.value.id == 'service'):
                    if rhs.func.attr == 'getCoverage':
                        nid = _alloc_node('Service.getCoverage')
                        for t in targets:
                            env.setdefault(t, set()).add(nid)
                        continue
                    elif rhs.func.attr == 'getCoverageCollection':
                        nid = _alloc_node('Service.getCoverageCollection')
                        for t in targets:
                            env.setdefault(t, set()).add(nid)
                        continue
                    elif rhs.func.attr == 'getFeature':
                        nid = _alloc_node('Service.getFeature')
                        for t in targets:
                            env.setdefault(t, set()).add(nid)
                        continue

            # 方法链式调用：xxx.styles().getMap() 等
            if isinstance(rhs, ast.Call) and isinstance(rhs.func, ast.Attribute):
                attr_chain: List[str] = []
                current = rhs.func
                while isinstance(current, ast.Attribute):
                    attr_chain.append(current.attr)
                    current = current.value

                # 检查是否是输出调用
                if 'getMap' in attr_chain or 'export' in attr_chain or 'log' in attr_chain:
                    base_var = None
                    if isinstance(current, ast.Name):
                        base_var = current.id
                    if base_var and base_var in env:
                        output_groups.add(frozenset(env[base_var]))

    # 如果 AST 解析没有找到节点，回退到正则
    if not node_label:
        return _regex_extract_graph(code)

    # 构建输出根节点集合
    output_roots: Set[str] = set()
    for group in output_groups:
        output_roots.update(group)

    # 如果有输出根节点，剪枝保留从根可达的节点
    if output_roots:
        predecessors: Dict[str, Set[str]] = {}
        for src, dst in edges:
            predecessors.setdefault(dst, set()).add(src)

        keep: Set[str] = set()
        stack = list(output_roots)
        while stack:
            cur = stack.pop()
            if cur in keep:
                continue
            keep.add(cur)
            stack.extend(predecessors.get(cur, set()))

        filtered_nodes = {nid: lbl for nid, lbl in node_label.items() if nid in keep}
        filtered_edges = [(s, d) for s, d in edges if s in keep and d in keep]
        if filtered_nodes:
            filtered_nodes, filtered_edges = _inject_global_roots(filtered_nodes, filtered_edges)
            return Graph(node_label=filtered_nodes, edges=filtered_edges), 'ast_success'

    # 没有输出或剪枝后为空，使用全部节点并注入全局起点
    edges_list = list(edges)
    node_label, edges_list = _inject_global_roots(node_label, edges_list)
    return Graph(node_label=node_label, edges=edges_list), 'ast_partial'


# ============================================================
# 图相似度核心算法
# ============================================================

def graph_signature(g: Graph) -> Tuple[Counter, Counter]:
    """将图转换为多重集合签名。

    - V: Counter[函数名] —— 节点标签的多重集合
    - E: Counter[(源函数名, 目标函数名)] —— 边标签的多重集合

    Args:
        g: 图对象

    Returns:
        Tuple[Counter, Counter]: (节点多重集合, 边多重集合)
    """
    V = Counter(g.node_label.values())
    E = Counter()
    for src, dst in g.edges:
        if src in g.node_label and dst in g.node_label:
            src_fn = g.node_label[src]
            dst_fn = g.node_label[dst]
            E[(src_fn, dst_fn)] += 1
    return V, E


def _multiset_intersection_size(a: Counter, b: Counter) -> int:
    """计算两个多重集合的交集大小。

    Args:
        a: 多重集合 A
        b: 多重集合 B

    Returns:
        int: 交集大小（每个元素取较小计数之和）
    """
    if not a or not b:
        return 0
    keys = set(a.keys()) & set(b.keys())
    return sum(min(a[k], b[k]) for k in keys)


def _prf1_multiset(pred: Counter, gold: Counter) -> Tuple[float, float, float]:
    """计算多重集合的精确率、召回率和 F1 值。

    Args:
        pred: 预测结果的多重集合
        gold: 标准答案的多重集合

    Returns:
        Tuple[float, float, float]: (precision, recall, f1)
    """
    inter = _multiset_intersection_size(pred, gold)
    pred_sz = sum(pred.values())
    gold_sz = sum(gold.values())

    if pred_sz == 0 and gold_sz == 0:
        return 1.0, 1.0, 1.0
    if pred_sz == 0 or gold_sz == 0:
        return 0.0, 0.0, 0.0

    p = inter / pred_sz
    r = inter / gold_sz
    f1 = (2 * p * r / (p + r)) if (p + r) else 0.0
    return p, r, f1


def calculate_similarity_metrics(
    pred_graph: Optional[Graph],
    gold_graph: Optional[Graph],
    edge_weight: float = 0.7,
) -> Tuple[float, float, float]:
    """计算图相似度的三个核心指标：TS、NMR、EMR。

    - NMR (Node Match Rate): 节点匹配率 = 节点标签 F1
    - EMR (Edge Match Rate): 边匹配率 = 边标签 F1
    - TS (Topological Similarity): 拓扑相似度
      = (edge_weight * EMR + (1 - edge_weight) * NMR) * 规模惩罚因子
      规模惩罚 = min(预测边数, 标准边数) / max(预测边数, 标准边数)

    Args:
        pred_graph: 预测的图
        gold_graph: 标准的图
        edge_weight: 边在综合相似度中的权重（默认 0.7）

    Returns:
        Tuple[float, float, float]: (TS, NMR, EMR)
    """
    if not pred_graph or not gold_graph:
        return 0.0, 0.0, 0.0

    pV, pE = graph_signature(pred_graph)
    gV, gE = graph_signature(gold_graph)

    _, _, f1_v = _prf1_multiset(pV, gV)  # NMR
    _, _, f1_e = _prf1_multiset(pE, gE)  # EMR

    # 综合相似度：边权重 + 节点权重
    sim = edge_weight * f1_e + (1.0 - edge_weight) * f1_v

    # 规模惩罚因子：防止边数差异很大时得分过高
    eps = 1e-9
    size_p = float(sum(pE.values()))
    size_g = float(sum(gE.values()))
    if size_p == 0.0 and size_g == 0.0:
        penalty = 1.0
    else:
        penalty = min(size_p, size_g) / (max(size_p, size_g) + eps)

    ts = sim * penalty
    return ts, f1_v, f1_e


def calculate_paper_metrics(
    pred_graph: Optional[Graph],
    gold_graph: Optional[Graph],
) -> Dict[str, float]:
    """计算论文中常用的图评估指标。

    Args:
        pred_graph: 预测的图
        gold_graph: 标准的图

    Returns:
        Dict: 包含 Node_Precision, Node_Recall, Node_F1, LAM, PA, LD 的字典
    """
    if not pred_graph or not gold_graph:
        return {
            'Node_Precision': -1.0,
            'Node_Recall': -1.0,
            'Node_F1': -1.0,
            'LAM': -1.0,
            'PA': 0.0,
            'LD': -1.0,
        }

    pV = Counter(pred_graph.node_label.values())
    gV = Counter(gold_graph.node_label.values())

    # 边标签多重集合
    p_edge_labels = [
        (pred_graph.node_label.get(src, 'Unknown'), pred_graph.node_label.get(dst, 'Unknown'))
        for src, dst in pred_graph.edges
    ]
    g_edge_labels = [
        (gold_graph.node_label.get(src, 'Unknown'), gold_graph.node_label.get(dst, 'Unknown'))
        for src, dst in gold_graph.edges
    ]
    pE = Counter(p_edge_labels)
    gE = Counter(g_edge_labels)

    node_p, node_r, node_f1 = _prf1_multiset(pV, gV)
    _, edge_r, _ = _prf1_multiset(pE, gE)  # LAM = 边召回率

    # PA (Perfect Accuracy): 是否完全一致
    pa = 1.0 if (pV == gV and pE == gE) else 0.0

    # LD (Length Difference): 节点数差异
    ld = float(abs(sum(pV.values()) - sum(gV.values())))

    return {
        'Node_Precision': node_p,
        'Node_Recall': node_r,
        'Node_F1': node_f1,
        'LAM': edge_r,
        'PA': pa,
        'LD': ld,
    }


# ============================================================
# 多图合并
# ============================================================

def merge_graphs(graphs: List[Graph], prefix_fmt: str = 'd{idx}::') -> Graph:
    """将多个图合并为一个大图（节点 ID 加前缀避免冲突）。

    Args:
        graphs: 图列表
        prefix_fmt: 节点 ID 前缀格式（含 {idx} 占位符）

    Returns:
        Graph: 合并后的图
    """
    node_label: Dict[str, str] = {}
    edges: List[Tuple[str, str]] = []
    for i, g in enumerate(graphs):
        prefix = prefix_fmt.format(idx=i)
        for nid, fn in g.node_label.items():
            node_label[prefix + nid] = fn
        for src, dst in g.edges:
            edges.append((prefix + src, prefix + dst))
    return Graph(node_label=node_label, edges=edges)


# ============================================================
# Token 级别的基础指标（保留原有功能）
# ============================================================

TOKEN_PATTERN = re.compile(r'[A-Za-z_][A-Za-z0-9_.]*')


def code_tokens(code: str) -> Set[str]:
    """从代码中提取归一化的标识符/API token。

    Args:
        code: 源代码

    Returns:
        Set[str]: token 集合（全部小写）
    """
    return {token.lower() for token in TOKEN_PATTERN.findall(code)}


def overlap_metrics(reference: str, candidate: str) -> Dict[str, float]:
    """计算代码 token 级别的精确率、召回率、F1 和 Jaccard 相似度。

    Args:
        reference: 参考代码（标准）
        candidate: 候选代码（生成的）

    Returns:
        Dict: 包含 precision, recall, node_f1, token_similarity 的字典
    """
    gold, pred = code_tokens(reference), code_tokens(candidate)
    common = gold & pred
    precision = len(common) / len(pred) if pred else 0.0
    recall = len(common) / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    union = len(gold | pred)
    return {
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'node_f1': round(f1, 4),
        'token_similarity': round(len(common) / union, 4) if union else 1.0,
    }


def dependency_edges(statements: Iterable[str]) -> Set[Tuple[str, str]]:
    """近似提取赋值语句的数据流边。

    Args:
        statements: 语句列表

    Returns:
        Set[Tuple[str, str]]: (输入变量, 输出变量) 边集合
    """
    edges: Set[Tuple[str, str]] = set()
    for statement in statements:
        match = re.match(r'\s*(?:var|let|const)?\s*([A-Za-z_]\w*)\s*=\s*(.*)', statement)
        if not match:
            continue
        output, expression = match.groups()
        for token in TOKEN_PATTERN.findall(expression):
            if token != output and not token.startswith('ee.'):
                edges.add((token, output))
    return edges


def edge_f1(reference_statements: Iterable[str], candidate_statements: Iterable[str]) -> float:
    """计算近似数据流边的 F1 值。

    Args:
        reference_statements: 参考语句列表
        candidate_statements: 候选语句列表

    Returns:
        float: 边 F1 值（保留 4 位小数）
    """
    gold, pred = dependency_edges(reference_statements), dependency_edges(candidate_statements)
    if not gold and not pred:
        return 1.0
    precision = len(gold & pred) / len(pred) if pred else 0.0
    recall = len(gold & pred) / len(gold) if gold else 0.0
    return round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0


# ============================================================
# 指标聚合
# ============================================================

MISSING_METRIC = -1.0


def is_valid_metric(x: Any, missing: float = MISSING_METRIC) -> bool:
    """判断指标值是否有效（不是缺失值）。

    Args:
        x: 指标值
        missing: 缺失值标记

    Returns:
        bool: 有效返回 True
    """
    return isinstance(x, (int, float)) and x != missing


def mean_excluding_missing(values: List[Any], missing: float = MISSING_METRIC) -> Optional[float]:
    """计算排除缺失值后的均值。

    Args:
        values: 指标值列表
        missing: 缺失值标记

    Returns:
        Optional[float]: 均值，无有效值时返回 None
    """
    xs = [float(v) for v in values if is_valid_metric(v, missing=missing)]
    return (sum(xs) / len(xs)) if xs else None


def aggregate_metric_rows(rows: Iterable[dict]) -> Dict[str, float | int | None]:
    """聚合成批评估结果，排除缺失值。

    Args:
        rows: 评估结果行列表

    Returns:
        Dict: 聚合后的统计指标
    """
    rows = list(rows)
    result: Dict[str, float | int | None] = {'total': len(rows)}
    metric_names = ('NMR', 'EMR', 'TS', 'Node_F1', 'LAM', 'PA', 'LD', 'Sim_Score', 'Con_Score')
    for name in metric_names:
        values = [r.get(name) for r in rows if is_valid_metric(r.get(name))]
        result[f'{name}_mean'] = round(sum(values) / len(values), 4) if values else None
    result['success'] = sum(bool(row.get('success')) for row in rows)
    return result


# ============================================================
# 综合评估入口
# ============================================================

def evaluate_pair(
    target_code: str,
    predicted_code: str,
    edge_weight: float = 0.7,
) -> Dict[str, Any]:
    """评估一对目标代码与预测代码，返回全部图相似度指标。

    Args:
        target_code: 标准（正确）OGE Python 代码
        predicted_code: 待评估的生成代码
        edge_weight: 边在综合相似度中的权重

    Returns:
        Dict: 包含 graph_metrics, paper_metrics, graph_info 的字典
    """
    # 提取预测图与标准图
    pred_g, pred_reason = infer_graph_from_code(predicted_code)
    gold_g, gold_reason = infer_graph_from_code(target_code)

    # 图相似度核心指标
    ts, nmr, emr = calculate_similarity_metrics(pred_g, gold_g, edge_weight=edge_weight)

    # 论文指标
    paper = calculate_paper_metrics(pred_g, gold_g)

    return {
        'graph_metrics': {
            'NMR': nmr,
            'EMR': emr,
            'TS': ts,
        },
        'paper_metrics': paper,
        'graph_info': {
            'pred_nodes': pred_g.num_nodes if pred_g else 0,
            'pred_edges': pred_g.num_edges if pred_g else 0,
            'gold_nodes': gold_g.num_nodes if gold_g else 0,
            'gold_edges': gold_g.num_edges if gold_g else 0,
            'pred_reason': pred_reason,
            'gold_reason': gold_reason,
        },
    }
