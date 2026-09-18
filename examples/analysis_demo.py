"""Run GEE static analysis and mapping coverage on the included NDVI example."""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.analysis import analyze_gee
from core.mapping import MappingLibrary
from core.validation import validate_mapping_coverage

source = (ROOT / "data_resources/source_code/ndvi_calculator_gee.js").read_text(encoding="utf-8")
library = MappingLibrary.from_json(ROOT / "data_resources/mappings/core_operator_mappings.json")
report = analyze_gee(source)
report["mapping_validation"] = validate_mapping_coverage(source, library)
print(json.dumps(report, ensure_ascii=False, indent=2))

