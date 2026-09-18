"""Minimal deterministic example of the native spatial fallback algorithms."""

from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.native_algorithms import normalized_difference, terrain_products

nir = np.array([[0.8, 0.4], [0.5, 0.3]])
red = np.array([[0.2, 0.2], [0.25, 0.1]])
dem = np.array([[100, 102], [98, 106]], dtype=float)
print("NDVI:\n", normalized_difference(nir, red))
try:
    print("terrain keys:", sorted(terrain_products(dem)))
except ModuleNotFoundError:
    print("terrain demo skipped: install scipy with `pip install -r requirements.txt`")
