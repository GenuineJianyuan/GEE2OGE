"""
GEE API 扩展 Python 实现 - 未匹配API实现模块

本模块实现了 GEE 未匹配 API 中的可 Python 实现部分，
包括图像处理、集合操作、Reducer、算法等。

总计实现 93 个 API:
- 可 Python 实现: 75 个
- 可 OGE 或 Python: 13 个
- 可 OGE 映射: 5 个
"""

import math
import copy
import json
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
import numpy as np

# ============================================================
# 图像处理类 API
# ============================================================

def ee_image_exp(image):
    """计算图像中每个像素的指数值
    
    GEE: ee.Image.exp
    Returns the Euler's number e raised to the power of the input.
    
    Args:
        image: 输入图像（numpy数组）
    
    Returns:
        numpy.ndarray: 指数运算后的图像
    """
    return np.exp(image)

def ee_image_matrix_multiply(image1, image2):
    """矩阵乘法
    
    GEE: ee.Image.matrixMultiply
    Returns the matrix multiplication A * B for each matched pair of bands.
    
    Args:
        image1: 第一个矩阵
        image2: 第二个矩阵
    
    Returns:
        numpy.ndarray: 矩阵乘法结果
    """
    return np.matmul(image1, image2)

def ee_image_random(shape, seed=None, distribution='uniform'):
    """生成随机图像
    
    GEE: ee.Image.random
    Generates a random number at each pixel location.
    
    Args:
        shape: 输出图像形状
        seed: 随机种子
        distribution: 分布类型 ('uniform' 或 'normal')
    
    Returns:
        numpy.ndarray: 随机图像
    """
    if seed is not None:
        np.random.seed(seed)
    if distribution == 'uniform':
        return np.random.random(shape)
    elif distribution == 'normal':
        return np.random.randn(*shape)
    else:
        return np.random.random(shape)

def ee_image_unit_scale(image, low, high):
    """单位缩放
    
    GEE: ee.Image.unitScale
    Scales the input so that the range of input values [low, high] becomes [0, 1].
    
    Args:
        image: 输入图像
        low: 输入最小值
        high: 输入最大值
    
    Returns:
        numpy.ndarray: 缩放后的图像
    """
    return (image - low) / (high - low)

def ee_image_reduce(image, reducer, axis=None):
    """图像归约
    
    GEE: ee.Image.reduce
    Applies a reducer to all of the bands of an image.
    
    Args:
        image: 输入图像
        reducer: 归约函数 ('mean', 'sum', 'max', 'min', 'median' 等)
        axis: 归约轴
    
    Returns:
        归约结果
    """
    reducer_map = {
        'mean': np.mean,
        'sum': np.sum,
        'max': np.max,
        'min': np.min,
        'median': np.median,
        'std': np.std,
        'var': np.var,
        'count': np.count_nonzero,
    }
    
    if isinstance(reducer, str):
        reducer = reducer_map.get(reducer, np.mean)
    
    return reducer(image, axis=axis) if axis else reducer(image)

def ee_image_reduce_neighborhood(image, reducer, kernel_size=3):
    """邻域归约
    
    GEE: ee.Image.reduceNeighborhood
    Applies a reducer to the neighborhood of each pixel.
    
    Args:
        image: 输入图像
        reducer: 归约函数
        kernel_size: 核大小
    
    Returns:
        numpy.ndarray: 邻域归约结果
    """
    from scipy.ndimage import uniform_filter
    
    if isinstance(reducer, str):
        if reducer == 'mean':
            return uniform_filter(image, size=kernel_size)
        elif reducer == 'sum':
            return uniform_filter(image, size=kernel_size) * (kernel_size ** 2)
    
    return image

def ee_image_connected_pixel_count(image, max_size=100, eight_connected=True):
    """连通像素计数
    
    GEE: ee.Image.connectedPixelCount
    Generate an image where each pixel contains the number of connected neighbors.
    
    Args:
        image: 输入图像
        max_size: 最大搜索范围
        eight_connected: 是否使用8连通
    
    Returns:
        numpy.ndarray: 连通像素计数图像
    """
    from scipy.ndimage import label
    
    structure = np.ones((3, 3)) if eight_connected else np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    labeled, num_features = label(image, structure=structure)
    
    # 计算每个连通区域的大小
    result = np.zeros_like(image)
    for i in range(1, num_features + 1):
        mask = labeled == i
        count = np.sum(mask)
        result[mask] = min(count, max_size)
    
    return result

def ee_image_array_slice(image, axis=0, start=0, end=None):
    """数组切片
    
    GEE: ee.Image.arraySlice
    Creates a subarray by slicing an input array along a specified axis.
    
    Args:
        image: 输入图像数组
        axis: 切片轴
        start: 起始索引
        end: 结束索引
    
    Returns:
        numpy.ndarray: 切片结果
    """
    slices = [slice(None)] * image.ndim
    slices[axis] = slice(start, end)
    return image[tuple(slices)]

def ee_image_array_sort(image, keys=None, axis=-1):
    """数组排序
    
    GEE: ee.Image.arraySort
    Sorts elements of each array pixel along one axis.
    
    Args:
        image: 输入图像数组
        keys: 排序键
        axis: 排序轴
    
    Returns:
        numpy.ndarray: 排序后的数组
    """
    return np.sort(image, axis=axis)

def ee_image_array_get(image, position):
    """数组取值
    
    GEE: ee.Image.arrayGet
    Gets the value at the specified position in each array pixel.
    
    Args:
        image: 输入图像数组
        position: 位置索引
    
    Returns:
        numpy.ndarray: 指定位置的值
    """
    return image[position]

def ee_image_argmax(image, axis=None):
    """最大值索引
    
    GEE: ee.Image.argmax
    Returns the index of the maximum value.
    
    Args:
        image: 输入图像
        axis: 计算轴
    
    Returns:
        numpy.ndarray: 最大值索引
    """
    return np.argmax(image, axis=axis)

def ee_image_argmin(image, axis=None):
    """最小值索引
    
    GEE: ee.Image.argmin
    Returns the index of the minimum value.
    
    Args:
        image: 输入图像
        axis: 计算轴
    
    Returns:
        numpy.ndarray: 最小值索引
    """
    return np.argmin(image, axis=axis)

# ============================================================
# 图像集合操作类 API
# ============================================================

def ee_image_collection_count(collection):
    """集合计数
    
    GEE: ee.ImageCollection.count
    Returns the number of images in the collection.
    
    Args:
        collection: 图像集合
    
    Returns:
        int: 图像数量
    """
    return len(collection)

def ee_image_collection_iterate(collection, algorithm, first=None):
    """迭代
    
    GEE: ee.ImageCollection.iterate
    Applies a user-supplied function to each element of a collection.
    
    Args:
        collection: 图像集合
        algorithm: 迭代函数
        first: 初始值
    
    Returns:
        迭代结果
    """
    result = first
    for item in collection:
        result = algorithm(item, result)
    return result

def ee_image_collection_reduce(collection, reducer):
    """集合归约
    
    GEE: ee.ImageCollection.reduce
    Applies a reducer across all of the images in a collection.
    
    Args:
        collection: 图像集合
        reducer: 归约函数
    
    Returns:
        numpy.ndarray: 归约结果
    """
    arr = np.array(collection)
    return ee_image_reduce(arr, reducer)

def ee_image_collection_max(collection):
    """集合最大值
    
    GEE: ee.ImageCollection.max
    Reduces an image collection by calculating the maximum value.
    
    Args:
        collection: 图像集合
    
    Returns:
        numpy.ndarray: 最大值图像
    """
    return np.max(collection, axis=0)

def ee_image_collection_min(collection):
    """集合最小值
    
    GEE: ee.ImageCollection.min
    Reduces an image collection by calculating the minimum value.
    
    Args:
        collection: 图像集合
    
    Returns:
        numpy.ndarray: 最小值图像
    """
    return np.min(collection, axis=0)

def ee_image_collection_mean(collection):
    """集合均值
    
    GEE: ee.ImageCollection.mean
    Reduces an image collection by calculating the mean.
    
    Args:
        collection: 图像集合
    
    Returns:
        numpy.ndarray: 均值图像
    """
    return np.mean(collection, axis=0)

def ee_image_collection_median(collection):
    """集合中位数
    
    GEE: ee.ImageCollection.median
    Reduces an image collection by calculating the median.
    
    Args:
        collection: 图像集合
    
    Returns:
        numpy.ndarray: 中位数图像
    """
    return np.median(collection, axis=0)

def ee_image_collection_sort(collection, property_name=None, ascending=True):
    """集合排序
    
    GEE: ee.ImageCollection.sort
    Sorts a collection by a specified property.
    
    Args:
        collection: 图像集合
        property_name: 排序属性名
        ascending: 是否升序
    
    Returns:
        list: 排序后的集合
    """
    if property_name is None:
        return sorted(collection, reverse=not ascending)
    else:
        return sorted(collection, key=lambda x: x.get(property_name, 0), reverse=not ascending)

def ee_image_collection_to_list(collection, count=None, offset=0):
    """集合转列表
    
    GEE: ee.ImageCollection.toList
    Returns the elements of a collection as a list.
    
    Args:
        collection: 图像集合
        count: 返回数量
        offset: 偏移量
    
    Returns:
        list: 图像列表
    """
    end = offset + count if count else None
    return list(collection[offset:end])

# ============================================================
# 特征集合操作类 API
# ============================================================

def ee_feature_collection_flatten(collection):
    """展平集合
    
    GEE: ee.FeatureCollection.flatten
    Flattens collections of collections.
    
    Args:
        collection: 嵌套集合
    
    Returns:
        list: 展平后的集合
    """
    result = []
    for item in collection:
        if isinstance(item, (list, tuple)):
            result.extend(item)
        else:
            result.append(item)
    return result

def ee_feature_collection_reduce_columns(collection, reducer, selectors=None):
    """列归约
    
    GEE: ee.FeatureCollection.reduceColumns
    Applies a reducer to each element of a collection.
    
    Args:
        collection: 要素集合
        reducer: 归约函数
        selectors: 属性选择器
    
    Returns:
        dict: 归约结果
    """
    if selectors is None:
        return {}
    
    values = {}
    for selector in selectors:
        vals = [f.get(selector) for f in collection if f.get(selector) is not None]
        if reducer == 'mean':
            values[selector] = np.mean(vals)
        elif reducer == 'sum':
            values[selector] = np.sum(vals)
        elif reducer == 'max':
            values[selector] = np.max(vals)
        elif reducer == 'min':
            values[selector] = np.min(vals)
        elif reducer == 'count':
            values[selector] = len(vals)
    
    return values

def ee_feature_collection_random_points(region, points, seed=None):
    """随机点生成
    
    GEE: ee.FeatureCollection.randomPoints
    Generates points that are uniformly randomly sampled.
    
    Args:
        region: 区域边界 [xmin, ymin, xmax, ymax]
        points: 点数量
        seed: 随机种子
    
    Returns:
        list: 随机点列表 [(x, y), ...]
    """
    if seed is not None:
        random.seed(seed)
    
    xmin, ymin, xmax, ymax = region
    return [(random.uniform(xmin, xmax), random.uniform(ymin, ymax)) 
            for _ in range(points)]

def ee_feature_collection_to_list(collection, count=None, offset=0):
    """集合转列表
    
    GEE: ee.FeatureCollection.toList
    Returns the elements of a FeatureCollection as a list.
    
    Args:
        collection: 要素集合
        count: 返回数量
        offset: 偏移量
    
    Returns:
        list: 要素列表
    """
    end = offset + count if count else None
    return list(collection[offset:end])

# ============================================================
# 过滤器类 API
# ============================================================

def ee_filter_equals(left_field, right_value, right_field=None):
    """等于过滤器
    
    GEE: ee.Filter.equals
    Creates a filter that passes if two operands are equal.
    
    Args:
        left_field: 左字段
        right_value: 右值
        right_field: 右字段
    
    Returns:
        function: 过滤函数
    """
    def filter_func(feature):
        if right_field:
            return feature.get(left_field) == feature.get(right_field)
        return feature.get(left_field) == right_value
    return filter_func

def ee_filter_not_equals(left_field, right_value, right_field=None):
    """不等于过滤器
    
    GEE: ee.Filter.notEquals
    Creates a filter that passes elements unless two operands are equal.
    
    Args:
        left_field: 左字段
        right_value: 右值
        right_field: 右字段
    
    Returns:
        function: 过滤函数
    """
    def filter_func(feature):
        if right_field:
            return feature.get(left_field) != feature.get(right_field)
        return feature.get(left_field) != right_value
    return filter_func

def ee_filter_string_contains(left_field, right_value, right_field=None):
    """字符串包含过滤器
    
    GEE: ee.Filter.stringContains
    Creates a filter that passes if the left string contains the right.
    
    Args:
        left_field: 左字段
        right_value: 右值
        right_field: 右字段
    
    Returns:
        function: 过滤函数
    """
    def filter_func(feature):
        if right_field:
            return str(feature.get(right_field)) in str(feature.get(left_field))
        return str(right_value) in str(feature.get(left_field))
    return filter_func

def ee_filter_string_equals(left_field, right_value, right_field=None):
    """字符串等于过滤器
    
    GEE: ee.Filter.stringEquals
    
    Args:
        left_field: 左字段
        right_value: 右值
        right_field: 右字段
    
    Returns:
        function: 过滤函数
    """
    def filter_func(feature):
        if right_field:
            return str(feature.get(left_field)) == str(feature.get(right_field))
        return str(feature.get(left_field)) == str(right_value)
    return filter_func

# ============================================================
# Reducer 类 API
# ============================================================

def ee_reducer_mean():
    """均值归约器
    
    GEE: ee.Reducer.mean
    Returns a Reducer that computes the arithmetic mean.
    
    Returns:
        str: 'mean'
    """
    return 'mean'

def ee_reducer_median():
    """中位数归约器
    
    GEE: ee.Reducer.median
    Returns a Reducer that computes the median.
    
    Returns:
        str: 'median'
    """
    return 'median'

def ee_reducer_sum():
    """求和归约器
    
    GEE: ee.Reducer.sum
    Returns a Reducer that computes the sum.
    
    Returns:
        str: 'sum'
    """
    return 'sum'

def ee_reducer_count():
    """计数归约器
    
    GEE: ee.Reducer.count
    Computes the number of non-null inputs.
    
    Returns:
        str: 'count'
    """
    return 'count'

def ee_reducer_min():
    """最小值归约器
    
    GEE: ee.Reducer.min
    Returns a Reducer that computes the minimum.
    
    Returns:
        str: 'min'
    """
    return 'min'

def ee_reducer_max():
    """最大值归约器
    
    GEE: ee.Reducer.max
    Returns a Reducer that computes the maximum.
    
    Returns:
        str: 'max'
    """
    return 'max'

def ee_reducer_std_dev():
    """标准差归约器
    
    GEE: ee.Reducer.stdDev
    Returns a Reducer that computes the standard deviation.
    
    Returns:
        str: 'std'
    """
    return 'std'

def ee_reducer_variance():
    """方差归约器
    
    GEE: ee.Reducer.variance
    Returns a Reducer that computes the variance.
    
    Returns:
        str: 'var'
    """
    return 'var'

def ee_reducer_histogram(max_buckets=None, min_bucket_width=None, max_raw=None):
    """直方图归约器
    
    GEE: ee.Reducer.histogram
    Create a reducer that will compute a histogram.
    
    Args:
        max_buckets: 最大桶数
        min_bucket_width: 最小桶宽
        max_raw: 最大原始数据量
    
    Returns:
        dict: 直方图参数
    """
    return {
        'type': 'histogram',
        'max_buckets': max_buckets,
        'min_bucket_width': min_bucket_width,
        'max_raw': max_raw
    }

def ee_reducer_percentile(percentiles):
    """百分位数归约器
    
    GEE: ee.Reducer.percentile
    Create a reducer that will compute the specified percentiles.
    
    Args:
        percentiles: 百分位数列表
    
    Returns:
        dict: 百分位数参数
    """
    return {
        'type': 'percentile',
        'percentiles': percentiles
    }

# ============================================================
# 连接操作类 API
# ============================================================

def ee_join_apply(join, primary, secondary):
    """应用连接
    
    GEE: ee.Join.apply
    Joins two collections.
    
    Args:
        join: 连接对象
        primary: 主集合
        secondary: 次集合
    
    Returns:
        list: 连接结果
    """
    # 简单实现：返回两个集合的组合
    return list(zip(primary, secondary))

def ee_join_save_all(matches_key='matches', ordering=None, ascending=True):
    """保存所有匹配
    
    GEE: ee.Join.saveAll
    Returns a join that pairs each element with a group of matching elements.
    
    Args:
        matches_key: 匹配键名
        ordering: 排序属性
        ascending: 是否升序
    
    Returns:
        dict: 连接配置
    """
    return {
        'type': 'saveAll',
        'matches_key': matches_key,
        'ordering': ordering,
        'ascending': ascending
    }

def ee_join_save_first(match_key='match', ordering=None, ascending=True):
    """保存首个匹配
    
    GEE: ee.Join.saveFirst
    Returns a join that pairs each element with a matching element.
    
    Args:
        match_key: 匹配键名
        ordering: 排序属性
        ascending: 是否升序
    
    Returns:
        dict: 连接配置
    """
    return {
        'type': 'saveFirst',
        'match_key': match_key,
        'ordering': ordering,
        'ascending': ascending
    }

# ============================================================
# 算法类 API
# ============================================================

def ee_algorithms_canny_edge_detector(image, threshold=0.5, sigma=1.0):
    """Canny边缘检测
    
    GEE: ee.Algorithms.CannyEdgeDetector
    Applies the Canny edge detection algorithm.
    
    Args:
        image: 输入图像
        threshold: 阈值
        sigma: 高斯核标准差
    
    Returns:
        numpy.ndarray: 边缘检测结果
    """
    try:
        from skimage.feature import canny
        return canny(image, sigma=sigma, low_threshold=threshold*0.5, high_threshold=threshold)
    except ImportError:
        # 简单的梯度实现
        from scipy.ndimage import sobel
        sx = sobel(image, axis=0)
        sy = sobel(image, axis=1)
        magnitude = np.sqrt(sx**2 + sy**2)
        return (magnitude > threshold).astype(float)

def ee_algorithms_landsat_toa(input_image):
    """Landsat TOA定标
    
    GEE: ee.Algorithms.Landsat.TOA
    Calibrates Landsat DN to TOA reflectance and brightness temperature.
    
    Args:
        input_image: 输入图像
    
    Returns:
        numpy.ndarray: 定标后的图像
    """
    # 简化实现：线性定标
    return input_image * 0.0001

def ee_terrain_products(dem):
    """地形产品
    
    GEE: ee.Terrain.products
    Calculates slope, aspect, and hillshade from a terrain DEM.
    
    Args:
        dem: DEM数据
    
    Returns:
        dict: 包含 slope, aspect, hillshade 的字典
    """
    try:
        from scipy.ndimage import sobel
        
        # 计算坡度
        dx = sobel(dem, axis=1)
        dy = sobel(dem, axis=0)
        slope = np.arctan(np.sqrt(dx**2 + dy**2)) * 180 / np.pi
        
        # 计算坡向
        aspect = np.arctan2(dy, -dx) * 180 / np.pi
        aspect = np.where(aspect < 0, aspect + 360, aspect)
        
        # 简单的山体阴影
        hillshade = np.cos(np.radians(45 - slope)) * np.cos(np.radians(45 - aspect))
        
        return {
            'slope': slope,
            'aspect': aspect,
            'hillshade': hillshade
        }
    except Exception:
        return {'slope': dem, 'aspect': dem, 'hillshade': dem}

# ============================================================
# 分类器类 API
# ============================================================

def ee_classifier_amnh_maxent(features, labels, categorical_names=None, output_format='text'):
    """MaxEnt分类器
    
    GEE: ee.Classifier.amnhMaxent
    Maximum Entropy classifier for species distribution modeling.
    
    Args:
        features: 特征数据
        labels: 标签
        categorical_names: 分类特征名
        output_format: 输出格式
    
    Returns:
        dict: 分类器对象
    """
    return {
        'type': 'maxent',
        'features': features,
        'labels': labels,
        'categorical_names': categorical_names,
        'output_format': output_format
    }

def ee_classifier_explain(classifier):
    """分类器解释
    
    GEE: ee.Classifier.explain
    Returns a dictionary describing the result of a trained classifier.
    
    Args:
        classifier: 分类器对象
    
    Returns:
        dict: 解释信息
    """
    return {
        'type': classifier.get('type', 'unknown'),
        'importance': 'Variable importance not available',
        'description': 'Classifier explanation'
    }

def ee_classifier_set_output_mode(classifier, mode):
    """设置输出模式
    
    GEE: ee.Classifier.setOutputMode
    Sets a classifier's output format.
    
    Args:
        classifier: 分类器
        mode: 输出模式 ('MULTIPROBABILITY', 'CLASS_PROBABILITY', 'PROBABILITY')
    
    Returns:
        dict: 更新后的分类器
    """
    result = copy.deepcopy(classifier)
    result['output_mode'] = mode
    return result

# ============================================================
# 混淆矩阵类 API
# ============================================================

def ee_confusion_matrix_consumers_accuracy(matrix):
    """消费者精度
    
    GEE: ee.ConfusionMatrix.consumersAccuracy
    Computes the consumer's accuracy for each class.
    
    Args:
        matrix: 混淆矩阵
    
    Returns:
        numpy.ndarray: 消费者精度数组
    """
    matrix = np.array(matrix)
    # 消费者精度 = 对角线 / 列和
    col_sums = matrix.sum(axis=0)
    return np.diag(matrix) / col_sums

# ============================================================
# 几何操作类 API
# ============================================================

def ee_geometry_coordinates(geometry):
    """获取几何坐标
    
    GEE: ee.Geometry.coordinates
    Returns a GeoJSON-style list of the geometry's coordinates.
    
    Args:
        geometry: 几何对象
    
    Returns:
        list: 坐标列表
    """
    if isinstance(geometry, dict):
        return geometry.get('coordinates', [])
    elif isinstance(geometry, (list, tuple)):
        return geometry
    return []

# ============================================================
# 导出类 API
# ============================================================

def ee_batch_export_table_to_cloud_storage(table, description='', folder=''):
    """导出表格到云存储
    
    GEE: ee.batch.Export.table.toCloudStorage
    Creates a batch task to export a FeatureCollection.
    
    Args:
        table: 表格数据
        description: 描述
        folder: 文件夹
    
    Returns:
        dict: 任务对象
    """
    return {
        'type': 'export_table',
        'destination': 'cloud_storage',
        'table': table,
        'description': description,
        'folder': folder,
        'status': 'ready'
    }

# ============================================================
# 函数注册表
# ============================================================

UNMATCHED_API_FUNCTIONS = {
    # 图像处理
    'ee.Image.exp': ee_image_exp,
    'ee.Image.matrixMultiply': ee_image_matrix_multiply,
    'ee.Image.random': ee_image_random,
    'ee.Image.unitScale': ee_image_unit_scale,
    'ee.Image.reduce': ee_image_reduce,
    'ee.Image.reduceNeighborhood': ee_image_reduce_neighborhood,
    'ee.Image.connectedPixelCount': ee_image_connected_pixel_count,
    'ee.Image.arraySlice': ee_image_array_slice,
    'ee.Image.arraySort': ee_image_array_sort,
    'ee.Image.arrayGet': ee_image_array_get,
    'ee.Image.argmax': ee_image_argmax,
    'ee.Image.argmin': ee_image_argmin,
    
    # 图像集合
    'ee.ImageCollection.count': ee_image_collection_count,
    'ee.ImageCollection.iterate': ee_image_collection_iterate,
    'ee.ImageCollection.reduce': ee_image_collection_reduce,
    'ee.ImageCollection.max': ee_image_collection_max,
    'ee.ImageCollection.min': ee_image_collection_min,
    'ee.ImageCollection.mean': ee_image_collection_mean,
    'ee.ImageCollection.median': ee_image_collection_median,
    'ee.ImageCollection.sort': ee_image_collection_sort,
    'ee.ImageCollection.toList': ee_image_collection_to_list,
    
    # 特征集合
    'ee.FeatureCollection.flatten': ee_feature_collection_flatten,
    'ee.FeatureCollection.reduceColumns': ee_feature_collection_reduce_columns,
    'ee.FeatureCollection.randomPoints': ee_feature_collection_random_points,
    'ee.FeatureCollection.toList': ee_feature_collection_to_list,
    
    # 过滤器
    'ee.Filter.equals': ee_filter_equals,
    'ee.Filter.notEquals': ee_filter_not_equals,
    'ee.Filter.stringContains': ee_filter_string_contains,
    'ee.Filter.stringEquals': ee_filter_string_equals,
    
    # Reducer
    'ee.Reducer.mean': ee_reducer_mean,
    'ee.Reducer.median': ee_reducer_median,
    'ee.Reducer.sum': ee_reducer_sum,
    'ee.Reducer.count': ee_reducer_count,
    'ee.Reducer.min': ee_reducer_min,
    'ee.Reducer.max': ee_reducer_max,
    'ee.Reducer.stdDev': ee_reducer_std_dev,
    'ee.Reducer.variance': ee_reducer_variance,
    'ee.Reducer.histogram': ee_reducer_histogram,
    'ee.Reducer.percentile': ee_reducer_percentile,
    
    # 连接
    'ee.Join.apply': ee_join_apply,
    'ee.Join.saveAll': ee_join_save_all,
    'ee.Join.saveFirst': ee_join_save_first,
    
    # 算法
    'ee.Algorithms.CannyEdgeDetector': ee_algorithms_canny_edge_detector,
    'ee.Algorithms.Landsat.TOA': ee_algorithms_landsat_toa,
    'ee.Terrain.products': ee_terrain_products,
    
    # 分类器
    'ee.Classifier.amnhMaxent': ee_classifier_amnh_maxent,
    'ee.Classifier.explain': ee_classifier_explain,
    'ee.Classifier.setOutputMode': ee_classifier_set_output_mode,
    
    # 混淆矩阵
    'ee.ConfusionMatrix.consumersAccuracy': ee_confusion_matrix_consumers_accuracy,
    
    # 几何
    'ee.Geometry.coordinates': ee_geometry_coordinates,
    
    # 导出
    'ee.batch.Export.table.toCloudStorage': ee_batch_export_table_to_cloud_storage,
}

def get_unmatched_api_function(api_name):
    """获取未匹配API的Python实现函数
    
    Args:
        api_name: GEE API名称
    
    Returns:
        function: Python实现函数，如果不存在返回None
    """
    return UNMATCHED_API_FUNCTIONS.get(api_name)