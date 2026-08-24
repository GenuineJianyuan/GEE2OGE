"""Data-flow graph construction and dependency ordering for GEE workflow statements."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Set


IDENTIFIER = re.compile(r'\b[A-Za-z_$][A-Za-z0-9_$]*\b')
ASSIGNMENT = re.compile(r'^\s*(?:var|let|const)?\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(.+?);?\s*$')
KEYWORDS = {'var', 'let', 'const', 'return', 'function', 'if', 'else', 'true', 'false', 'null', 'undefined', 'ee', 'Map', 'Export', 'Math', 'console', 'print'}


def statement_variables(statement: str) -> tuple[str | None, Set[str]]:
    """Return the assigned variable and referenced user variables in one statement."""
    match = ASSIGNMENT.match(statement.strip())
    target = match.group(1) if match else None
    expression = match.group(2) if match else statement
    references = {token for token in IDENTIFIER.findall(expression) if token not in KEYWORDS}
    if target:
        references.discard(target)
    return target, references


def build_dataflow(statements: Iterable[str]) -> Dict[str, object]:
    """Build a dependency graph using assignment and identifier references."""
    nodes = []
    producer: Dict[str, int] = {}
    edges: Dict[int, Set[int]] = defaultdict(set)
    for index, statement in enumerate(statements):
        target, references = statement_variables(statement)
        dependencies = sorted({producer[name] for name in references if name in producer})
        for dependency in dependencies:
            edges[dependency].add(index)
        nodes.append({'id': index, 'statement': statement, 'target': target, 'references': sorted(references), 'dependencies': dependencies})
        if target:
            producer[target] = index
    return {'nodes': nodes, 'edges': {str(key): sorted(value) for key, value in edges.items()}}


def topological_order(dataflow: Dict[str, object]) -> List[int]:
    """Return a stable topological order; preserve original order if a cycle is found."""
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
    return ordered if len(ordered) == len(nodes) else [node['id'] for node in nodes]
