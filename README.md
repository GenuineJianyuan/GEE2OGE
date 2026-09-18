# GEE ↔ OGE Core Algorithms

A standalone, pure-algorithm package extracted from the GEE-to-OGE migration project.
Deliberately excludes all application-layer components: Flask routes, web pages, database connections, caching, background jobs, persistence services, and LLM HTTP clients.

## Repository Layout

```text
gitCode/
├── main.py                         # Command-line entry point
├── README.md                       # Package overview and usage
├── dependency.md                   # Dependencies and runtime boundaries
├── core/
│   ├── analysis.py                 # GEE static analysis: step segmentation, type inference, API extraction
│   ├── preprocessing.py            # Source-code preprocessing algorithms
│   ├── workflow.py                 # Data-flow graph construction, topological sort, cycle detection
│   ├── mapping.py                  # Mapping library loading, combo matching, batch lookup
│   ├── converter.py                # Rule-based GEE ↔ OGE code skeleton generation
│   ├── validation.py               # Input, mapping, and output validation rules
│   ├── native_algorithms.py        # Pure-Python remote sensing and spatial analysis algorithms
│   └── evaluation.py               # Graph similarity evaluation: NMR / EMR / TS metrics
├── docs/
│   └── ALGORITHM_CATALOG.md        # Algorithm catalogue and four-strategy descriptions
├── examples/                        # Runnable analysis and spatial algorithm examples
├── tests/                           # Unit tests
├── requirements.txt                 # Optional numerical dependencies
├── pyproject.toml                   # Install/test metadata
└── data_resources/
    ├── source_code/                # GEE source-code examples
    ├── converted_code/             # OGE converted-code examples
    └── mappings/                   # Core operator mappings (JSON format)
```

## Included Algorithms

### GEE Static Analysis (`core.analysis`)

- Comment-based workflow step segmentation, with separator-comment detection and step-coverage validation
- Global variable-type inference: Image, Collection, Geometry, Number, Date, List, Dictionary
- API recognition for constructors, static methods, Map/Export calls, and instance methods
- Chain-call extraction via bracket counting (supports nested arguments)
- Key-parameter extraction: dataset IDs, band names, index names, dates, geometry coordinates, map settings

### Data-Flow Analysis (`core.workflow`)

- Statement extraction and variable-reference analysis
- Directed dependency-graph construction
- Stable topological ordering (Kahn's algorithm with cycle fallback)
- Cycle detection (Tarjan's strongly connected components algorithm)
- Level/depth computation, root-node and leaf-node identification

### Mapping Library & Matching (`core.mapping`)

- JSON-backed GEE-to-OGE operator mapping library (125 core mappings)
- Forward lookup (GEE → OGE) and reverse lookup (OGE → GEE)
- Five mapping types: one_to_one, one_to_many, many_to_one, many_to_many, native_python
- **Combo matching algorithm**: greedy strategy sorted by combo size descending + scarcity ascending
- Match-rate calculation, missing-API statistics, feasibility classification
- API lookup-table construction (for code generation consumption)

### Rule-Based Conversion (`core.converter`)

- Mapping-driven GEE → OGE code skeleton generation
- Code generation for all five mapping types
- Code organized by workflow steps with feasibility labels
- OGE → GEE reverse conversion drafts
- Mapping context formatting utilities (for LLM-assisted code generation)

### Validation Rules (`core.validation`)

- GEE source checks: empty input, bracket/quote balance, API recognition
- Mapping-coverage checks
- OGE workflow checks: duplicate initialization, placeholders, missing APIs
- Mapping-library internal consistency checks

### Code Preprocessing (`core.preprocessing`)

- Code normalization (line endings, trailing whitespace)
- Python comment and docstring cleanup
- JavaScript comment cleanup (line comments + block comments)
- Line counting, import extraction, dedent

### Graph Similarity Evaluation (`core.evaluation`)

- **AST-to-graph**: build data-flow dependency graphs from OGE Python code
- **Regex fallback**: regex-based extraction when AST parsing fails
- **NMR** (Node Match Rate): node-level F1 score
- **EMR** (Edge Match Rate): edge-level F1 score
- **TS** (Topological Similarity): combined node+edge weighted score with size penalty
- Paper metrics: Node_Precision / Recall / F1 / LAM / PA / LD
- Multi-graph merging, metric aggregation, token-level similarity

### Native Remote-Sensing Algorithms (`core.native_algorithms`)

- Pixel-wise operations: exponential transform, matrix multiplication, random raster generation, value scaling
- Normalized indices: NDVI, GNDVI, NDMI, generic normalizedDifference
- Statistical reduction: mean / sum / max / min / median / std / var / count
- Neighborhood filtering: focal mean/sum, median filtering
- Terrain analysis: slope, aspect, hillshade, terrain products
- Image processing: connected-pixel count, Canny/Sobel edge detection
- Classification accuracy: user's accuracy, producer's accuracy, overall accuracy, Kappa coefficient
- Radiometric calibration: simplified linear Landsat TOA calibration

## Quick Start

Run from the `gitCode` directory:

```bash
# Static analysis of GEE code
python main.py analyze-gee data_resources/source_code/ndvi_calculator_gee.js

# GEE → OGE rule-based conversion
python main.py gee-to-oge data_resources/source_code/ndvi_calculator_gee.js -o output_oge.py

# OGE → GEE reverse conversion
python main.py oge-to-gee data_resources/converted_code/ndvi_calculator_oge.py -o output_gee.js

# Run unit tests
python -m unittest discover -s tests -v
```

## Extending the Mapping Library

Append records to `data_resources/mappings/core_operator_mappings.json`:

```json
{
  "gee_api": "ee.Image.normalizedDifference",
  "gee_api_names": ["ee.Image.normalizedDifference"],
  "oge_apis": ["Coverage.subtract", "Coverage.add", "Coverage.divide"],
  "mapping_type": "one_to_many",
  "mapping_name": "Normalized Difference Index",
  "note": "(band1 - band2) / (band1 + band2)",
  "gee_example": "",
  "oge_example": "",
  "python_implementation": "",
  "confidence": 0.95
}
```

Combo mapping (many_to_one) example:

```json
{
  "gee_api": "ee.Image.select",
  "gee_api_names": ["ee.Image.select", "ee.Image.subtract", "ee.Image.divide"],
  "oge_apis": ["Coverage.NDVI"],
  "mapping_type": "many_to_one",
  "mapping_name": "NDVI Combo",
  "note": "select + subtract + divide → direct NDVI operator call",
  "confidence": 0.9
}
```

The converter does not invent coverage IDs, product IDs, spatial references, resolutions, or process arguments.
Such information is retained as explicit `TODO` markers or placeholders so that generated workflows remain reviewable.

## Design Principles

1. **Pure-algorithm focus**: no Flask, database, LLM, caching, or other application-layer dependencies
2. **Zero external services**: core algorithms depend only on the Python standard library (+ NumPy, optional)
3. **Function-level documentation**: every public function has a Chinese docstring
4. **Independently runnable**: all modules can be imported and tested in isolation
5. **Data-driven**: mapping data is separated from algorithms for easy extension and audit
