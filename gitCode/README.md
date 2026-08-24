# GEE ↔ OGE Core Algorithms

This is a standalone, Git-ready algorithm package extracted from a GEE-to-OGE migration project. It deliberately excludes all application-layer components: Flask routes, web pages, database connections, cache handling, background jobs, persistence services, and LLM HTTP clients.

## Repository Layout

```text
gitCode/
├── main.py                         # Command-line entry point
├── README.md                       # Package overview and usage
├── dependency.md                   # Dependencies and runtime boundaries
├── core/
│   ├── analysis.py                 # GEE static analysis and API extraction
│   ├── workflow.py                 # Data-flow graph and dependency ordering
│   ├── mapping.py                  # Lightweight bidirectional mapping library
│   ├── converter.py                # Rule-based GEE ↔ OGE conversion skeletons
│   ├── validation.py               # Input, mapping, and output validation rules
│   └── native_algorithms.py        # Native numerical and remote-sensing algorithms
└── data_resources/
    ├── source_code/                # GEE source-code examples
    ├── converted_code/             # OGE converted-code examples
    └── mappings/                   # Auditable lightweight operator mappings
```

## Included Algorithms

### GEE Static Analysis

- Step segmentation based on line comments.
- Global variable-type inference for images, collections, geometry, numbers, dates, lists, and dictionaries.
- Recognition of constructors, static methods, map/export calls, and typed instance methods.
- Extraction of datasets, band names, index names, dates, geometry coordinates, and map settings.

### Data-Flow Analysis

- Assignment and identifier-reference extraction.
- Directed dependency graph construction.
- Stable topological ordering for workflow reconstruction.
- Cycle-safe fallback to original statement order.

### Mapping and Conversion

- JSON-backed GEE-to-OGE operator lookup.
- Reverse lookup from an OGE process to one or more GEE APIs.
- Mapping coverage statistics and missing-API reporting.
- One-to-one, one-to-many, and native-Python implementation categories.
- Explainable GEE-to-OGE skeleton generation with explicit placeholders.
- OGE-to-GEE reverse-conversion drafts for review.

### Validation

- Empty input and bracket-balance checks.
- API-recognition and mapping-coverage checks.
- Duplicate OGE initialization and unresolved-placeholder checks.

### Native Remote-Sensing Algorithms

- Pixel-wise exponential transform, matrix multiplication, random raster generation, and unit scaling.
- Normalized difference, NDVI, GNDVI, and NDMI.
- Statistical reduction, neighborhood mean/sum, and focal median filtering.
- Connected-pixel count and Canny/Sobel edge detection.
- DEM slope, aspect, hillshade, terrain products, and confusion-matrix consumer accuracy.

## Quick Start

Run commands from the `gitCode` directory:

```bash
python main.py analyze-gee data_resources/source_code/ndvi_calculator_gee.js
python main.py gee-to-oge data_resources/source_code/ndvi_calculator_gee.js -o output_oge.py
python main.py oge-to-gee data_resources/converted_code/ndvi_calculator_oge.py -o output_gee.js
```

## Extending the Mapping Library

Append records to `data_resources/mappings/core_operator_mappings.json`:

```json
{
  "gee_api": "ee.Image.normalizedDifference",
  "oge_apis": ["Coverage.subtract", "Coverage.add", "Coverage.divide"],
  "mapping_type": "one_to_many",
  "note": "(band1 - band2) / (band1 + band2)"
}
```

The converter does not invent coverage IDs, product IDs, spatial references, resolutions, or process arguments. It retains such information as explicit `TODO` markers or placeholders so that generated workflows remain reviewable.

