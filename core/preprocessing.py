"""源代码预处理算法：清理、归一化和格式化。

从主项目中提取代码预处理相关逻辑，用于迁移前的代码清洗和规范化。
所有函数均为纯函数，不修改输入参数。
"""

from __future__ import annotations

import re
from typing import List


def strip_python_prompt_noise(code: str) -> str:
    """去除 Python 代码中的三引号注释块和整行 # 注释。

    仅用于 LLM prompt 预处理，不会修改调用方保存的原始代码。

    Args:
        code: Python 源代码

    Returns:
        str: 清理后的代码
    """
    # 去除三引号块（docstring）
    without_blocks = re.sub(
        r"(?s)(?:\"\"\"|''').*?(?:\"\"\"|''')", "", code
    )
    # 去除整行注释和空行
    return "\n".join(
        line for line in without_blocks.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ).strip()


def normalize_source(code: str) -> str:
    """归一化代码的换行符和行尾空白，不改变逻辑。

    - 统一 \r\n 为 \n
    - 去除行尾空白
    - 去除首尾空行

    Args:
        code: 源代码

    Returns:
        str: 归一化后的代码
    """
    return "\n".join(
        line.rstrip() for line in code.replace("\r\n", "\n").split("\n")
    ).strip()


def remove_comments_js(code: str) -> str:
    """去除 JavaScript 代码中的注释（行注释和块注释）。

    简单实现，不考虑字符串内的注释符号。

    Args:
        code: JavaScript 代码

    Returns:
        str: 去除注释后的代码
    """
    # 去除块注释 /* ... */
    no_block = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    # 去除行注释 // ...
    lines: List[str] = []
    for line in no_block.splitlines():
        # 简单处理：如果 // 不在字符串中（粗略判断）
        in_string = False
        string_char = ''
        cut_pos = -1
        for i, ch in enumerate(line):
            if ch in ('"', "'", '`') and (i == 0 or line[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = ch
                elif ch == string_char:
                    in_string = False
            elif ch == '/' and i + 1 < len(line) and line[i+1] == '/' and not in_string:
                cut_pos = i
                break
        if cut_pos >= 0:
            line = line[:cut_pos]
        lines.append(line)
    return '\n'.join(lines)


def count_lines(code: str) -> dict:
    """统计代码的行数信息。

    Args:
        code: 源代码

    Returns:
        dict: 包含 total, non_empty, comment 等行数统计
    """
    lines = code.splitlines()
    total = len(lines)
    non_empty = sum(1 for l in lines if l.strip())
    comment_lines = sum(
        1 for l in lines
        if l.strip().startswith('//') or l.strip().startswith('#')
    )
    return {
        'total': total,
        'non_empty': non_empty,
        'comment_lines': comment_lines,
        'code_lines': non_empty - comment_lines,
    }


def extract_imports_js(code: str) -> List[str]:
    """从 JavaScript 代码中提取 require/import 导入。

    Args:
        code: JavaScript 代码

    Returns:
        List[str]: 导入的模块名列表
    """
    imports: List[str] = []

    # require 形式
    for match in re.finditer(r'require\s*\(\s*["\']([^"\']+)["\']\s*\)', code):
        imports.append(match.group(1))

    # import 形式
    for match in re.finditer(r'import\s+.+?\s+from\s+["\']([^"\']+)["\']', code):
        imports.append(match.group(1))

    return imports


def dedent_code(code: str) -> str:
    """去除代码的公共缩进（与 textwrap.dedent 类似，但更宽容）。

    Args:
        code: 源代码

    Returns:
        str: 去除公共缩进后的代码
    """
    lines = code.splitlines()
    if not lines:
        return code

    # 找出非空行的最小缩进
    min_indent = None
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if min_indent is None or indent < min_indent:
            min_indent = indent

    if min_indent is None or min_indent == 0:
        return code

    return '\n'.join(line[min_indent:] if line.strip() else line for line in lines)
