"""Pure validation rules for conversion input, mappings, and generated workflow code."""

from __future__ import annotations

import re
from typing import Dict, List

from .analysis import extract_gee_apis
from .mapping import MappingLibrary


def validate_gee_source(gee_code: str) -> List[Dict[str, str]]:
    """Detect common source issues without executing JavaScript."""
    issues: List[Dict[str, str]] = []
    if not gee_code.strip():
        return [{'severity': 'error', 'message': 'Source code is empty.'}]
    if gee_code.count('{') != gee_code.count('}'):
        issues.append({'severity': 'warning', 'message': 'Unbalanced curly braces detected.'})
    if gee_code.count('(') != gee_code.count(')'):
        issues.append({'severity': 'warning', 'message': 'Unbalanced parentheses detected.'})
    if not extract_gee_apis(gee_code):
        issues.append({'severity': 'warning', 'message': 'No recognizable GEE API calls were found.'})
    return issues


def validate_mapping_coverage(gee_code: str, library: MappingLibrary) -> Dict[str, object]:
    """Report mapped and unmapped GEE APIs referenced by a source script."""
    apis = extract_gee_apis(gee_code)
    report = library.match_report(apis)
    report['mapped_apis'] = [api for api in apis if library.find_gee(api)]
    return report


def validate_oge_workflow(oge_code: str) -> List[Dict[str, str]]:
    """Check generated OGE code for placeholders and duplicate initialization."""
    issues: List[Dict[str, str]] = []
    if len(re.findall(r'\bimport\s+oge\b', oge_code)) > 1:
        issues.append({'severity': 'warning', 'message': 'Duplicate oge import statements detected.'})
    if len(re.findall(r'\bservice\s*=\s*oge\.Service\(\)', oge_code)) > 1:
        issues.append({'severity': 'warning', 'message': 'Duplicate OGE service initialization detected.'})
    if '...' in oge_code or 'TODO' in oge_code:
        issues.append({'severity': 'warning', 'message': 'Workflow contains placeholders requiring manual completion.'})
    return issues
