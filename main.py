"""Command-line entry point for the GEE ↔ OGE core algorithm package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.analysis import analyze_gee
from core.converter import convert_gee_to_oge, convert_oge_to_gee
from core.mapping import MappingLibrary
from core.validation import validate_gee_source, validate_mapping_coverage, validate_oge_workflow
from core.workflow import build_dataflow, topological_order


ROOT = Path(__file__).resolve().parent
DEFAULT_MAPPING = ROOT / 'data_resources' / 'mappings' / 'core_operator_mappings.json'


def main() -> None:
    parser = argparse.ArgumentParser(description='GEE ↔ OGE core algorithms')
    parser.add_argument('mode', choices=['analyze-gee', 'gee-to-oge', 'oge-to-gee'])
    parser.add_argument('input', type=Path, help='input code file')
    parser.add_argument('-o', '--output', type=Path, help='output file; omitted means stdout')
    parser.add_argument('-m', '--mappings', type=Path, default=DEFAULT_MAPPING, help='operator mapping JSON')
    args = parser.parse_args()

    source = args.input.read_text(encoding='utf-8')
    if args.mode == 'analyze-gee':
        analysis = analyze_gee(source)
        statements = [line.strip() for line in source.splitlines() if line.strip() and not line.strip().startswith('//')]
        flow = build_dataflow(statements)
        analysis['dataflow'] = flow
        analysis['topological_order'] = topological_order(flow)
        analysis['validation'] = validate_gee_source(source)
        text = json.dumps(analysis, ensure_ascii=False, indent=2)
    else:
        library = MappingLibrary.from_json(args.mappings)
        result = convert_gee_to_oge(source, library) if args.mode == 'gee-to-oge' else convert_oge_to_gee(source, library)
        text = result['code']
        report = result.get('match_report')
        if report:
            report['validation'] = validate_mapping_coverage(source, library)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.mode == 'gee-to-oge':
            validation = validate_oge_workflow(text)
            if validation:
                print(json.dumps({'generated_code_validation': validation}, ensure_ascii=False, indent=2))
    if args.output:
        args.output.write_text(text, encoding='utf-8')
        print(f'written: {args.output}')
    else:
        print(text)


if __name__ == '__main__':
    main()
