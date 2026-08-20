"""GEE 未映射 API 的纯遥感/空间分析实现。

从 ``gee_unmatched_functions.py`` 提炼，保留数学和栅格计算，去除注册表、
工程元数据及非算法包装。依赖：numpy；部分函数按需导入 scipy/scikit-image。
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import numpy as np


def image_exp(image: np.ndarray) -> np.ndarray:
    """逐像元指数变换：y = exp(x)。"""
    return np.exp(image)


def matrix_multiply(image1: np.ndarray, image2: np.ndarray) -> np.ndarray:
    """逐像元矩阵乘法。"""
    return np.matmul(image1, image2)


def random_image(shape: tuple, seed: Optional[int] = None, distribution: str = 'uniform') -> np.ndarray:
    """生成可复现的均匀或正态随机栅格，不修改 NumPy 的全局随机状态。"""
    rng = np.random.default_rng(seed)
    if distribution == 'normal':
        return rng.standard_normal(shape)
    return rng.random(shape)


def unit_scale(image: np.ndarray, low: float, high: float) -> np.ndarray:
    """把输入值域 [low, high] 线性缩放到 [0, 1]。"""
    if high == low:
        raise ValueError('high 与 low 不能相等')
    return (np.asarray(image) - low) / (high - low)


def reduce_image(image: np.ndarray, reducer: str | Callable[..., Any], axis: Optional[int] = None) -> Any:
    """沿指定轴执行 mean/sum/max/min/median/std/var/count 归约。"""
    functions = {
        'mean': np.mean, 'sum': np.sum, 'max': np.max, 'min': np.min,
        'median': np.median, 'std': np.std, 'var': np.var, 'count': np.count_nonzero,
    }
    function = functions.get(reducer, np.mean) if isinstance(reducer, str) else reducer
    return function(image, axis=axis)


def reduce_neighborhood(image: np.ndarray, reducer: str = 'mean', kernel_size: int = 3) -> np.ndarray:
    """用 k×k 均匀窗口计算邻域均值或邻域总和。"""
    from scipy.ndimage import uniform_filter

    local_mean = uniform_filter(np.asarray(image, dtype=float), size=kernel_size)
    if reducer == 'mean':
        return local_mean
    if reducer == 'sum':
        return local_mean * kernel_size ** 2
    raise ValueError("reducer 仅支持 'mean' 或 'sum'")


def connected_pixel_count(image: np.ndarray, max_size: int = 100, eight_connected: bool = True) -> np.ndarray:
    """把每个非零像元赋为其所属连通域的面积，并以 max_size 截断。"""
    from scipy.ndimage import label

    binary = np.asarray(image) != 0
    structure = np.ones((3, 3), dtype=int) if eight_connected else np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    labels, count = label(binary, structure=structure)
    result = np.zeros(binary.shape, dtype=int)
    for region_id in range(1, count + 1):
        region = labels == region_id
        result[region] = min(int(region.sum()), max_size)
    return result


def canny_edge_detector(image: np.ndarray, threshold: float = 0.5, sigma: float = 1.0) -> np.ndarray:
    """Canny 边缘检测；没有 scikit-image 时退化为 Sobel 梯度阈值。"""
    try:
        from skimage.feature import canny
        return canny(image, sigma=sigma, low_threshold=threshold * 0.5, high_threshold=threshold)
    except ImportError:
        from scipy.ndimage import sobel
        gradient_x = sobel(image, axis=0)
        gradient_y = sobel(image, axis=1)
        magnitude = np.hypot(gradient_x, gradient_y)
        return (magnitude > threshold).astype(float)


def terrain_products(dem: np.ndarray) -> dict[str, np.ndarray]:
    """由 DEM 计算简化的坡度、坡向和固定 45° 光照条件下的山体阴影。"""
    from scipy.ndimage import sobel

    dem = np.asarray(dem, dtype=float)
    dx, dy = sobel(dem, axis=1), sobel(dem, axis=0)
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    aspect = np.degrees(np.arctan2(dy, -dx))
    aspect = np.where(aspect < 0, aspect + 360, aspect)
    hillshade = np.cos(np.radians(45 - slope)) * np.cos(np.radians(45 - aspect))
    return {'slope': slope, 'aspect': aspect, 'hillshade': hillshade}


def landsat_toa_simple(input_image: np.ndarray) -> np.ndarray:
    """Landsat TOA 的简化线性定标（DN × 0.0001）。"""
    return np.asarray(input_image) * 0.0001


def consumers_accuracy(matrix: np.ndarray) -> np.ndarray:
    """按混淆矩阵列计算消费者精度：对角线 / 列和。"""
    matrix = np.asarray(matrix, dtype=float)
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.divide(np.diag(matrix), matrix.sum(axis=0), out=np.zeros(matrix.shape[0]), where=matrix.sum(axis=0) != 0)
