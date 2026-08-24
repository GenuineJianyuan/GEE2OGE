# Dependencies

## Base Runtime

- Python 3.10 or later.
- Standard library modules: `argparse`, `collections`, `dataclasses`, `json`, `pathlib`, `re`, and `typing`.

The following modules have no dependency on a database, web server, Flask, Requests, or any LLM service:

- `core/analysis.py`
- `core/workflow.py`
- `core/mapping.py`
- `core/converter.py`
- `core/validation.py`
- `main.py`

## Native Remote-Sensing Algorithms

`core/native_algorithms.py` uses third-party packages only for numerical and image-processing operations.

| Package | Purpose | Required when |
| --- | --- | --- |
| `numpy` | Array mathematics, indices, reductions, random rasters, and accuracy metrics | Importing native algorithms |
| `scipy` | Neighborhood filters, connected components, Sobel operators, and terrain products | Calling related functions |
| `scikit-image` | Full Canny edge detector | Optional; Sobel threshold fallback is used otherwise |

Install numerical dependencies:

```bash
pip install numpy scipy scikit-image
```

## OGE Execution Boundary

The converter generates OGE Python workflow skeletons but does not execute them. Therefore, this package does not require the `oge` SDK. Install and configure the OGE SDK, service endpoint, credentials, and catalog access only in the target environment where generated workflows are executed.

## Data and Safety Boundaries

- The bundled mapping JSON is a small, auditable core mapping set rather than a complete API knowledge base.
- Example files contain no credentials, access tokens, or production data.
- `TODO` and `...` in generated code are mandatory manual-completion points and must be resolved before production execution.

