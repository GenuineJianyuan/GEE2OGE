"""Native Python and remote-sensing algorithms for GEE APIs without direct mappings.

Only numerical computation is included: no database registration, Web interface, or
platform calls. NumPy is required; SciPy and scikit-image are loaded on demand.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import numpy as np


def image_exp(image: np.ndarray) -> np.ndarray:
    """ee.Image.exp: compute e raised to x for every pixel."""
    return np.exp(np.asarray(image))


def matrix_multiply(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """ee.Image.matrixMultiply: perform matrix multiplication."""
    return np.matmul(left, right)


def random_image(shape: tuple[int, ...], seed: Optional[int] = None, distribution: str = 'uniform') -> np.ndarray:
    """ee.Image.random: create reproducible uniform or standard-normal rasters."""
    generator = np.random.default_rng(seed)
    return generator.standard_normal(shape) if distribution == 'normal' else generator.random(shape)


def unit_scale(image: np.ndarray, low: float, high: float) -> np.ndarray:
    """ee.Image.unitScale: linearly scale [low, high] to [0, 1]."""
    if high == low:
        raise ValueError('low and high must be different')
    return (np.asarray(image) - low) / (high - low)


def normalized_difference(first_band: np.ndarray, second_band: np.ndarray, fill_value: float = np.nan) -> np.ndarray:
    """Compute a normalized difference index: (first - second) / (first + second)."""
    first = np.asarray(first_band, dtype=float)
    second = np.asarray(second_band, dtype=float)
    denominator = first + second
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.divide(first - second, denominator, out=np.full_like(first, fill_value), where=denominator != 0)


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Normalized Difference Vegetation Index: (NIR - Red) / (NIR + Red)."""
    return normalized_difference(nir, red)


def gndvi(nir: np.ndarray, green: np.ndarray) -> np.ndarray:
    """Green Normalized Difference Vegetation Index: (NIR - Green) / (NIR + Green)."""
    return normalized_difference(nir, green)


def ndmi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Normalized Difference Moisture Index: (NIR - SWIR) / (NIR + SWIR)."""
    return normalized_difference(nir, swir)


def reduce_image(image: np.ndarray, reducer: str | Callable[..., Any], axis: Optional[int] = None) -> Any:
    """ee.Image.reduce: mean, sum, extrema, median, variance, and related reductions."""
    reducers = {
        'mean': np.mean, 'sum': np.sum, 'max': np.max, 'min': np.min,
        'median': np.median, 'std': np.std, 'var': np.var, 'count': np.count_nonzero,
    }
    function = reducers.get(reducer, np.mean) if isinstance(reducer, str) else reducer
    return function(image, axis=axis)


def reduce_neighborhood(image: np.ndarray, reducer: str = 'mean', kernel_size: int = 3) -> np.ndarray:
    """ee.Image.reduceNeighborhood: k-by-k neighborhood mean or sum."""
    from scipy.ndimage import uniform_filter
    local_mean = uniform_filter(np.asarray(image, dtype=float), size=kernel_size)
    if reducer == 'mean':
        return local_mean
    if reducer == 'sum':
        return local_mean * kernel_size ** 2
    raise ValueError("reducer must be 'mean' or 'sum'")


def focal_median(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply a median filter for salt-and-pepper noise reduction."""
    from scipy.ndimage import median_filter
    return median_filter(np.asarray(image), size=kernel_size)


def slope_aspect(dem: np.ndarray, cell_size: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Compute slope and aspect from a DEM using central numerical gradients."""
    if cell_size <= 0:
        raise ValueError('cell_size must be positive')
    dy, dx = np.gradient(np.asarray(dem, dtype=float), cell_size, cell_size)
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    aspect = (np.degrees(np.arctan2(dy, -dx)) + 360) % 360
    return slope, aspect


def hillshade(slope: np.ndarray, aspect: np.ndarray, azimuth: float = 315.0, altitude: float = 45.0) -> np.ndarray:
    """Compute a 0-255 hillshade from slope/aspect and sun geometry in degrees."""
    zenith = np.radians(90.0 - altitude)
    azimuth_rad = np.radians(360.0 - azimuth + 90.0)
    slope_rad, aspect_rad = np.radians(slope), np.radians(aspect)
    illumination = np.cos(zenith) * np.cos(slope_rad) + np.sin(zenith) * np.sin(slope_rad) * np.cos(azimuth_rad - aspect_rad)
    return np.clip(255 * illumination, 0, 255).astype(np.uint8)


def connected_pixel_count(image: np.ndarray, max_size: int = 100, eight_connected: bool = True) -> np.ndarray:
    """ee.Image.connectedPixelCount: count the connected component of each nonzero pixel."""
    from scipy.ndimage import label
    binary = np.asarray(image) != 0
    structure = np.ones((3, 3), dtype=int) if eight_connected else np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    labels, region_count = label(binary, structure=structure)
    result = np.zeros(binary.shape, dtype=int)
    for region in range(1, region_count + 1):
        mask = labels == region
        result[mask] = min(int(mask.sum()), max_size)
    return result


def canny_edge_detector(image: np.ndarray, threshold: float = 0.5, sigma: float = 1.0) -> np.ndarray:
    """ee.Algorithms.CannyEdgeDetector with a Sobel-threshold fallback."""
    try:
        from skimage.feature import canny
        return canny(image, sigma=sigma, low_threshold=threshold * 0.5, high_threshold=threshold)
    except ImportError:
        from scipy.ndimage import sobel
        dx, dy = sobel(image, axis=0), sobel(image, axis=1)
        return (np.hypot(dx, dy) > threshold).astype(float)


def terrain_products(dem: np.ndarray) -> dict[str, np.ndarray]:
    """ee.Terrain.products: estimate slope, aspect, and simplified hillshade using Sobel gradients."""
    from scipy.ndimage import sobel
    dx, dy = sobel(dem, axis=1), sobel(dem, axis=0)
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    aspect = np.degrees(np.arctan2(dy, -dx))
    aspect = np.where(aspect < 0, aspect + 360, aspect)
    hillshade = np.cos(np.radians(45 - slope)) * np.cos(np.radians(45 - aspect))
    return {'slope': slope, 'aspect': aspect, 'hillshade': hillshade}


def consumers_accuracy(confusion_matrix: np.ndarray) -> np.ndarray:
    """ee.ConfusionMatrix.consumersAccuracy: 按混淆矩阵列计算消费者精度。

    消费者精度 = 对角线元素 / 列和

    Args:
        confusion_matrix: 混淆矩阵（方阵）

    Returns:
        np.ndarray: 每类的消费者精度
    """
    matrix = np.asarray(confusion_matrix, dtype=float)
    sums = matrix.sum(axis=0)
    return np.divide(
        np.diag(matrix), sums,
        out=np.zeros(matrix.shape[0]),
        where=sums != 0,
    )


def producers_accuracy(confusion_matrix: np.ndarray) -> np.ndarray:
    """ee.ConfusionMatrix.producersAccuracy: 按混淆矩阵行计算生产者精度。

    生产者精度 = 对角线元素 / 行和

    Args:
        confusion_matrix: 混淆矩阵（方阵）

    Returns:
        np.ndarray: 每类的生产者精度
    """
    matrix = np.asarray(confusion_matrix, dtype=float)
    sums = matrix.sum(axis=1)
    return np.divide(
        np.diag(matrix), sums,
        out=np.zeros(matrix.shape[0]),
        where=sums != 0,
    )


def overall_accuracy(confusion_matrix: np.ndarray) -> float:
    """ee.ConfusionMatrix.accuracy: 计算总体分类精度。

    总体精度 = 对角线元素之和 / 所有元素之和

    Args:
        confusion_matrix: 混淆矩阵（方阵）

    Returns:
        float: 总体精度（0~1）
    """
    matrix = np.asarray(confusion_matrix, dtype=float)
    total = matrix.sum()
    if total == 0:
        return 0.0
    return float(np.trace(matrix) / total)


def kappa_coefficient(confusion_matrix: np.ndarray) -> float:
    """计算 Cohen's Kappa 系数（分类一致性指标）。

    Kappa = (Po - Pe) / (1 - Pe)
    其中 Po 是观测一致率（总体精度），Pe 是期望一致率。

    Args:
        confusion_matrix: 混淆矩阵（方阵）

    Returns:
        float: Kappa 系数（-1~1）
    """
    matrix = np.asarray(confusion_matrix, dtype=float)
    total = matrix.sum()
    if total == 0:
        return 0.0

    po = np.trace(matrix) / total
    row_sums = matrix.sum(axis=1)
    col_sums = matrix.sum(axis=0)
    pe = (row_sums * col_sums).sum() / (total * total)

    if pe == 1.0:
        return 1.0
    return float((po - pe) / (1 - pe))


def landsat_toa_simple(input_image: np.ndarray) -> np.ndarray:
    """Landsat TOA 的简化线性定标。

    将 DN 值转换为大气顶部反射率的简化近似：
    TOA_reflectance = DN × 0.0001

    Args:
        input_image: 输入 DN 值影像

    Returns:
        np.ndarray: TOA 反射率影像
    """
    return np.asarray(input_image) * 0.0001
