"""GEE 工作流数据流分析：依赖图构建、拓扑排序与层级分析。

从主项目 ``algri/migration_algorithms.py`` 中提取数据流相关算法，
并补充了层级分析、循环检测等增强功能。
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Set, Tuple


# 标识符正则（支持 JavaScript 风格的变量名）
IDENTIFIER = re.compile(r'\b[A-Za-z_$][A-Za-z0-9_$]*\b')

# 赋值语句正则（支持 var/let/const 前缀）
ASSIGNMENT = re.compile(
    r'^\s*(?:var|let|const)?\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(.+?);?\s*$'
)

# JavaScript 关键字（排除在用户变量之外）
KEYWORDS = {
    'var', 'let', 'const', 'return', 'function', 'if', 'else',
    'true', 'false', 'null', 'undefined', 'ee', 'Map', 'Export',
    'Math', 'console', 'print', 'for', 'while', 'do', 'switch',
    'case', 'break', 'continue', 'new', 'this', 'typeof', 'in',
    'of', 'instanceof', 'void', 'delete', 'throw', 'try', 'catch',
    'finally', 'class', 'extends', 'super', 'import', 'export',
    'default', 'await', 'async', 'yield',
}


def extract_statements(code: str) -> List[str]:
    """从代码中提取可执行语句（按分号或换行分割，去除注释和空行）。

    Args:
        code: 源代码

    Returns:
        List[str]: 语句列表
    """
    # 先去除行注释
    lines: List[str] = []
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('//'):
            continue
        # 去除行内注释（简单处理，不考虑字符串中的 //）
        if '//' in stripped:
            # 粗略判断：如果 // 不在字符串中
            in_string = False
            string_char = ''
            cut_pos = -1
            for i, ch in enumerate(stripped):
                if ch in ('"', "'", '`') and (i == 0 or stripped[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = ch
                    elif ch == string_char:
                        in_string = False
                elif ch == '/' and i + 1 < len(stripped) and stripped[i+1] == '/' and not in_string:
                    cut_pos = i
                    break
            if cut_pos >= 0:
                stripped = stripped[:cut_pos].strip()

        if stripped:
            lines.append(stripped)

    # 合并成一个字符串，再按分号分割
    joined = ' '.join(lines)
    raw_statements = [s.strip() for s in joined.split(';') if s.strip()]

    # 过滤掉纯控制流语句（if/for/while 等的开头部分）
    result: List[str] = []
    for stmt in raw_statements:
        # 跳过纯控制流关键字开头的不完整语句
        if any(stmt.startswith(kw + ' ') or stmt == kw for kw in
               ('if', 'else', 'for', 'while', 'do', 'switch', 'return', 'break', 'continue')):
            continue
        result.append(stmt)

    return result


def statement_variables(statement: str) -> Tuple[Optional[str], Set[str]]:
    """提取单条语句中的赋值目标变量和引用的用户变量。

    Args:
        statement: 单条语句

    Returns:
        Tuple[Optional[str], Set[str]]: (赋值目标变量名, 引用的变量集合)
    """
    match = ASSIGNMENT.match(statement.strip())
    target = match.group(1) if match else None
    expression = match.group(2) if match else statement

    # 提取所有标识符，过滤关键字
    references = {
        token for token in IDENTIFIER.findall(expression)
        if token not in KEYWORDS
    }
    # 排除目标变量自身
    if target:
        references.discard(target)

    return target, references


def build_dataflow(statements: Iterable[str]) -> Dict[str, Any]:
    """根据赋值语句构建数据流依赖图。

    分析每条语句的赋值目标和引用变量，构建节点（语句）之间的
    有向依赖边：如果语句 B 引用了语句 A 定义的变量，则 A → B。

    Args:
        statements: 语句列表

    Returns:
        Dict: 包含 nodes 和 edges 的依赖图数据
    """
    nodes: List[Dict[str, Any]] = []
    producer: Dict[str, int] = {}  # 变量名 → 最近定义它的语句索引
    edges: Dict[int, Set[int]] = defaultdict(set)

    for index, statement in enumerate(statements):
        target, references = statement_variables(statement)

        # 查找依赖的语句
        dependencies = sorted({
            producer[name] for name in references if name in producer
        })

        # 添加依赖边
        for dependency in dependencies:
            edges[dependency].add(index)

        nodes.append({
            'id': index,
            'statement': statement,
            'target': target,
            'references': sorted(references),
            'dependencies': dependencies,
        })

        # 更新变量的生产者
        if target:
            producer[target] = index

    return {
        'nodes': nodes,
        'edges': {str(key): sorted(value) for key, value in edges.items()},
    }


def topological_order(dataflow: Dict[str, Any]) -> List[int]:
    """计算依赖图的稳定拓扑排序。

    使用 Kahn 算法进行拓扑排序。如果检测到循环，返回原始顺序
    （保证不会因循环而崩溃）。

    Args:
        dataflow: build_dataflow 返回的依赖图

    Returns:
        List[int]: 拓扑排序后的节点 ID 列表
    """
    nodes = dataflow['nodes']
    indegree = {node['id']: len(node['dependencies']) for node in nodes}
    outgoing = {int(key): values for key, values in dataflow['edges'].items()}

    queue = deque(node['id'] for node in nodes if indegree[node['id']] == 0)
    ordered: List[int] = []

    while queue:
        node = queue.popleft()
        ordered.append(node)
        for child in outgoing.get(node, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    # 如果有环，返回原始顺序
    if len(ordered) != len(nodes):
        return [node['id'] for node in nodes]

    return ordered


def detect_cycles(dataflow: Dict[str, Any]) -> List[List[int]]:
    """检测依赖图中的循环（强连通分量）。

    使用 Tarjan 算法找出所有非平凡强连通分量（大小 > 1 的 SCC）。

    Args:
        dataflow: build_dataflow 返回的依赖图

    Returns:
        List[List[int]]: 每个循环的节点 ID 列表
    """
    nodes = dataflow['nodes']
    outgoing: Dict[int, List[int]] = {
        int(key): list(values) for key, values in dataflow['edges'].items()
    }
    # 确保所有节点都在 outgoing 中
    for node in nodes:
        outgoing.setdefault(node['id'], [])

    index_counter = [0]
    stack: List[int] = []
    lowlink: Dict[int, int] = {}
    index: Dict[int, int] = {}
    on_stack: Dict[int, bool] = {}
    result: List[List[int]] = []

    def _strongconnect(v: int) -> None:
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True

        for w in outgoing.get(v, []):
            if w not in index:
                _strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack.get(w, False):
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            scc: List[int] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1:
                result.append(sorted(scc))

    for node in nodes:
        if node['id'] not in index:
            _strongconnect(node['id'])

    return result


def compute_levels(dataflow: Dict[str, Any]) -> Dict[int, int]:
    """计算每个节点的层级（拓扑深度）。

    根节点层级为 0，每增加一个依赖深度层级 +1。

    Args:
        dataflow: build_dataflow 返回的依赖图

    Returns:
        Dict[int, int]: 节点 ID → 层级
    """
    nodes = dataflow['nodes']
    outgoing = {int(key): values for key, values in dataflow['edges'].items()}
    indegree = {node['id']: len(node['dependencies']) for node in nodes}

    levels: Dict[int, int] = {}
    queue = deque()

    for node in nodes:
        if indegree[node['id']] == 0:
            levels[node['id']] = 0
            queue.append(node['id'])

    while queue:
        current = queue.popleft()
        current_level = levels[current]
        for child in outgoing.get(current, []):
            new_level = current_level + 1
            if child not in levels or new_level > levels[child]:
                levels[child] = new_level
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    # 对于循环中的节点，设为 -1
    for node in nodes:
        if node['id'] not in levels:
            levels[node['id']] = -1

    return levels


def find_leaf_nodes(dataflow: Dict[str, Any]) -> List[int]:
    """找出依赖图中的叶子节点（没有后继的节点）。

    Args:
        dataflow: build_dataflow 返回的依赖图

    Returns:
        List[int]: 叶子节点 ID 列表
    """
    nodes = dataflow['nodes']
    has_outgoing: Set[int] = set()
    for values in dataflow['edges'].values():
        has_outgoing.update(values)

    return [node['id'] for node in nodes if node['id'] not in has_outgoing]


def find_root_nodes(dataflow: Dict[str, Any]) -> List[int]:
    """找出依赖图中的根节点（没有前驱依赖的节点）。

    Args:
        dataflow: build_dataflow 返回的依赖图

    Returns:
        List[int]: 根节点 ID 列表
    """
    nodes = dataflow['nodes']
    return [node['id'] for node in nodes if not node['dependencies']]


def build_dataflow_from_code(code: str) -> Dict[str, Any]:
    """从完整代码构建数据流图（便捷入口）。

    自动提取语句并构建依赖图。

    Args:
        code: 源代码

    Returns:
        Dict: 包含 nodes、edges、topological_order、levels 的完整分析结果
    """
    statements = extract_statements(code)
    dataflow = build_dataflow(statements)
    dataflow['topological_order'] = topological_order(dataflow)
    dataflow['levels'] = compute_levels(dataflow)
    dataflow['cycles'] = detect_cycles(dataflow)
    dataflow['root_nodes'] = find_root_nodes(dataflow)
    dataflow['leaf_nodes'] = find_leaf_nodes(dataflow)
    dataflow['statement_count'] = len(statements)
    return dataflow
