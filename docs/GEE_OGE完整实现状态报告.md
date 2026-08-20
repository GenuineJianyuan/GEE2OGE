# GEE → OGE 完整实现状态报告

生成时间：2026-07-31

---

## 📊 总体统计

| 指标 | 数量 |
|---|---|
| GEE API 总数 | 1425 |
| Excel 映射表中已匹配 | 202 |
| Excel 映射表中未匹配 | 189 |
| 已实现 Python 函数 | 90 |
| 识别的映射问题 | 45 |

---

## 📁 文件清单

| 文件 | 说明 |
|---|---|
| `gee_to_oge_matches.xlsx` | 映射表（202 条） |
| `gee.json` | GEE API 详情（1425 个） |
| `oge.json` | OGE API 详情 |
| `gee_to_ge_mapping.py` | 核心映射转换模块 |
| `gee_python_functions.py` | Python 实现（45 个，基础版） |
| `gee_unmatched_functions.py` | Python 实现（45 个，扩展版） |
| `mapping_review_issues.json` | 审查发现的问题 |
| `full_audit_report.json` | 完整审查数据 |

---

## ✅ 映射状态分类

### 状态图例

| 状态 | 图标 | 说明 |
|---|---|---|
| ✅ 正确映射 | 🟢 | 直接映射到 OGE API，功能一致 |
| ⚠️ 有差异 | 🟡 | 可映射但功能有差异，需注意 |
| 🔴 有问题 | 🔴 | 映射错误或功能不同，需修正 |
| 🐍 Python | 🐍 | 使用 Python 实现（OGE 无对应 API） |
| 🆕 新建 | ➕ | 新增的 Python 实现（不在原映射表中） |

---

## 一、原映射表中的 202 条映射状态

### 1.1 正确映射（约 162 条）

这些映射功能一致，可以直接使用：

#### 基础运算类

| GEE API | OGE API | 状态 | 备注 |
|---|---|---|---|
| `ee.Image.add` | `Coverage.add` | 🟢 | |
| `ee.Image.subtract` | `Coverage.subtract` | 🟢 | |
| `ee.Image.multiply` | `Coverage.multiply` | 🟢 | |
| `ee.Image.divide` | `Coverage.divide` | 🟢 | |
| `ee.Image.eq` | `Coverage.eq` | 🟢 | |
| `ee.Image.gt` | `Coverage.gt` | 🟢 | |
| `ee.Image.gte` | `Coverage.gte` | 🟢 | |
| `ee.Image.lt` | `Coverage.lt` | 🟢 | |
| `ee.Image.lte` | `Coverage.lte` | 🟢 | |
| `ee.Image.and` | `Coverage.bitwiseAnd` | � | **错误！逻辑与映射到位与** |
| `ee.Image.or` | `Coverage.or` | 🟢 | |
| `ee.Image.not` | `Coverage.not` | 🟢 | |
| `ee.Image.bitwiseAnd` | `Coverage.bitwiseAnd` | 🟢 | 正确：位与 → 位与 |
| `ee.Image.max` | `Coverage.maxi` | 🟢 | |
| `ee.Image.min` | `Coverage.mini` | 🟢 | |
| `ee.Image.rename` | `Coverage.rename` | 🟢 | |
| `ee.Image.select` | `Coverage.select` | 🟢 | |
| `ee.Image.clip` | `Coverage.clipRasterByExtentByGDAL` | 🟢 | |
| `ee.Image.mask` | `Coverage.mask` | 🟢 | |
| `ee.Image.unmask` | `Coverage.unmask` | 🟢 | |

#### 几何运算类

| GEE API | OGE API | 状态 |
|---|---|---|
| `ee.Feature.buffer` | `Feature.buffer` | 🟢 |
| `ee.Feature.distance` | `Feature.distance` | 🟢 |
| `ee.Feature.intersects` | `Feature.intersects` | 🟢 |
| `ee.Feature.intersection` | `Feature.intersection` | 🟢 |
| `ee.Feature.difference` | `Feature.difference` | 🟢 |
| `ee.Feature.symmetricDifference` | `Feature.symmetricDifference` | 🟢 |
| `ee.Feature.contains` | `Feature.contains` | 🟢 |
| `ee.Feature.contained` | `Feature.contained` | 🟢 |
| `ee.Feature.withinDistance` | `Feature.withinDistance` | 🟢 |
| `ee.Feature.bounds` | `Feature.bounds` | 🟢 |
| `ee.Feature.centroid` | `Feature.centroid` | 🟢 |
| `ee.Feature.simplify` | `Feature.simplify` | 🟢 |

#### 集合操作类

| GEE API | OGE API | 状态 |
|---|---|---|
| `ee.FeatureCollection.filter` | `FeatureCollection.filter` | 🟢 |
| `ee.FeatureCollection.sort` | `FeatureCollection.limit` | 🔴（有误） |
| `ee.FeatureCollection.geometry` | `FeatureCollection.union` | 🔴（有误） |
| `ee.FeatureCollection.first` | `FeatureCollection.first` | 🟢 |
| `ee.FeatureCollection.random` | `FeatureCollection.random` | 🟢 |
| `ee.FeatureCollection.merge` | `FeatureCollection.merge` | 🟢 |
| `ee.FeatureCollection.map` | `FeatureCollection.map` | 🟢 |
| `ee.FeatureCollection.size` | `FeatureCollection.size` | 🟢 |
| `ee.FeatureCollection.toList` | `FeatureCollection.toList` | 🟢 |

#### 导出类

| GEE API | OGE API | 状态 |
|---|---|---|
| `Export.image.toDrive` | `Coverage.export` | 🟡（同一接口不同目标） |
| `Export.image.toAsset` | `Coverage.export` | 🟡（同一接口不同目标） |
| `Export.table.toDrive` | `FeatureCollection.export` | 🟡（同一接口不同目标） |
| `Export.table.toAsset` | `FeatureCollection.export` | 🟡（同一接口不同目标） |

#### 地形分析类

| GEE API | OGE API | 状态 |
|---|---|---|
| `ee.Terrain.slope` | `Coverage.terrSlope` | 🟢 |
| `ee.Terrain.aspect` | `Coverage.terrAspect` | 🟢 |
| `ee.Terrain.hillshade` | `Coverage.terrShade` | 🟢 |

#### 其他正确映射

| GEE API | OGE API | 状态 |
|---|---|---|
| `ee.Number` → Python Int/Float | Python | 🐍 |
| `ee.String` → Python String | Python | 🐍 |
| `ee.List` → Python List | Python | 🐍 |
| `ee.Dictionary` → Python Dict | Python | 🐍 |
| `print` → Python print() | Python | 🐍 |

---

### 1.2 有差异但可接受的映射（约 25 条）

#### 对象类型不匹配（需注意）

| GEE API | OGE API | 差异说明 | 状态 |
|---|---|---|---|
| `ee.ImageCollection.limit` | `FeatureCollection.limit` | 影像集合 → 矢量集合 | 🟡 |
| `ee.ImageCollection.filterBounds` | `FeatureCollection.filterBounds` | 影像集合 → 矢量集合 | 🟡 |
| `ee.ImageCollection.filterDate` | `FeatureCollection.filterDate` | 影像集合 → 矢量集合 | 🟡 |
| `ee.ImageCollection.filterMetadata` | `FeatureCollection.filterMetadata` | 影像集合 → 矢量集合 | 🟡 |
| `ee.ImageCollection.randomColumn` | `FeatureCollection.randomColumn` | 影像集合 → 矢量集合 | 🟡 |
| `ee.Image.sample` | `FeatureCollection.sample` | 影像 → 矢量 | 🟡 |

**说明**：OGE 可能没有 Coverage/CoverageCollection 的对应方法，使用时需确认。

#### Filter → Collection 转换

| GEE API | OGE API | 转换说明 | 状态 |
|---|---|---|---|
| `ee.Filter.bounds` | `FeatureCollection.filterBounds` | 需转换调用方式 | 🟡 |
| `ee.Filter.date` | `FeatureCollection.filterDate` | 需转换调用方式 | 🟡 |
| `ee.Filter.calendarRange` | `FeatureCollection.filterDate` | 需 Python 解析 | 🟡 |
| `ee.Filter.eq` | `Coverage.eq` | 底层运算相同，场景不同 | 🟡 |
| `ee.Filter.gt` | `Coverage.gt` | 底层运算相同，场景不同 | 🟡 |
| `ee.Filter.gte` | `Coverage.gte` | 底层运算相同，场景不同 | 🟡 |
| `ee.Filter.lt` | `Coverage.lt` | 底层运算相同，场景不同 | 🟡 |
| `ee.Filter.lte` | `Coverage.lte` | 底层运算相同，场景不同 | 🟡 |
| `ee.Filter.not` | `Coverage.not` | 底层运算相同，场景不同 | 🟡 |
| `ee.Filter.or` | `Coverage.or` | 底层运算相同，场景不同 | 🟡 |

#### 功能近似

| GEE API | OGE API | 差异说明 | 状态 |
|---|---|---|---|
| `ee.Image.reduceResolution` | `Coverage.resample` | 降分辨率 vs 重采样 | 🟡 |
| `ee.Image.reduceToVectors` | `Coverage.polygonizeByGDAL` | 栅格转矢量 vs 转多边形 | 🟡 |
| `ee.Image.toInt` | `Coverage.toInt32` | 泛型 vs 指定位宽 | 🟡 |
| `ee.Reducer.max` | `Coverage.maxi` | Reducer vs 像元计算 | 🟡 |
| `ee.Reducer.min` | `Coverage.mini` | Reducer vs 像元计算 | 🟡 |
| `ee.Image.pixelArea` | `Coverage.surfAreaByGrass` | 像素面积 vs 地形表面积 | 🟡 |

#### 分类器映射（需改进）

| GEE API | OGE API | 差异说明 | 状态 |
|---|---|---|---|
| `ee.Classifier.libsvm` | `Coverage.svmClassificationBySAGA` | ✅ SVM → SVM | 🟢 |
| `ee.Classifier.smileRandomForest` | `Coverage.svmClassificationBySAGA` | ❌ 随机森林 → SVM | 🔴 |
| `ee.Classifier.smileCart` | `Coverage.svmClassificationBySAGA` | ❌ CART → SVM | 🔴 |
| `ee.Classifier.minimumDistance` | `Coverage.svmClassificationBySAGA` | ❌ 最小距离 → SVM | 🔴 |
| `ee.Classifier.naiveBayes` | `Coverage.svmClassificationBySAGA` | ❌ 朴素贝叶斯 → SVM | 🔴 |
| `ee.Classifier.smileGAM` | `Coverage.svmClassificationBySAGA` | ❌ GAM → SVM | 🔴 |
| `ee.Classifier.smileKMeans` | `Coverage.svmClassificationBySAGA` | ❌ KMeans → SVM | 🔴 |
| `ee.Classifier.smileLVQ` | `Coverage.svmClassificationBySAGA` | ❌ LVQ → SVM | 🔴 |
| `ee.Classifier.smileMLP` | `Coverage.svmClassificationBySAGA` | ❌ MLP → SVM | 🔴 |
| `ee.Image.classify` | `Coverage.svmClassificationBySAGA` | 仅支持 SVM | 🟡 |

---

### 1.3 有问题的映射（6 条，需修正）

| # | GEE API | OGE API | 问题类型 | 严重程度 | 修正建议 | 状态 |
|---|---|---|---|---|---|---|
| 1 | `ee.Feature.set` | `Feature.select` | 功能完全不同 | 🔴 严重 | Python 实现 `set(key, value)` | 待修正 |
| 2 | `ee.Image.rgbToHsv` | `Coverage.hsvToRgb` | 方向相反 | 🔴 严重 | 修正方向或 Python 实现 | 待修正 |
| 3 | `ee.FeatureCollection.sort` | `FeatureCollection.limit` | 功能不同 | 🔴 严重 | Python 实现 `sort()` | 待修正 |
| 4 | `ee.FeatureCollection.geometry` | `FeatureCollection.union` | 功能不同 | 🔴 严重 | Python 实现 `geometry()` | 待修正 |
| 5 | `ee.Filter.withinDistance` | `Feature.withinDistance` | 层级不匹配 | 🔴 严重 | Python 实现集合级过滤器 | 待修正 |
| 6 | `ee.Image.and` | `Coverage.bitwiseAnd` | **逻辑与映射到位与** | 🔴 严重 | Python 实现逻辑与 | 待修正 |

#### 问题详细说明

**错误 1：`ee.Feature.set` → `Feature.select`**
- GEE: 
  ```python
  fc = ee.FeatureCollection('users/example/fc')  # 加载要素集合
  feature = fc.first()                             # 获取第一个要素
  feature = feature.set('new_property', 'value')  # 设置属性值，返回新的 Feature
  ```
- OGE: 
  ```python
  fc = Service.getFeatureCollection('users/example/fc')
  feature = fc.first()
  result = feature.select(['property1', 'property2'])  # 选择字段，返回子集
  ```
- 问题：`set` 是设置属性值；`select` 是选择字段
- 修正：用 Python 实现 `set(key, value)` 方法
  ```python
  def feature_set(feature, key, value):
      """设置 Feature 的属性值"""
      result = feature.copy()
      result[key] = value
      return result
  ```

**错误 2：`ee.Image.rgbToHsv` → `Coverage.hsvToRgb`**
- GEE: 
  ```python
  # 加载 RGB 图像（3 个波段）
  rgb_image = ee.Image('users/example/rgb_image')  # 波段顺序: [R, G, B]
  hsv_image = rgb_image.rgbToHsv()  # 转换为 HSV
  ```
- OGE: 
  ```python
  # 加载 HSV 图像
  hsv_image = Service.getCoverage('users/example/hsv_image')  # 波段顺序: [H, S, V]
  rgb_image = hsv_image.hsvToRgb()  # 转换为 RGB
  ```
- 问题：方向相反！GEE 是 RGB→HSV，OGE 是 HSV→RGB
- 修正：需要用 Python 实现 `rgbToHsv`
  ```python
  import numpy as np
  
  def rgb_to_hsv(r, g, b):
      """将 RGB 值转换为 HSV"""
      r, g, b = r / 255.0, g / 255.0, b / 255.0
      max_val = max(r, g, b)
      min_val = min(r, g, b)
      diff = max_val - min_val
      
      # 色相
      if diff == 0:
          h = 0
      elif max_val == r:
          h = (60 * ((g - b) / diff) + 360) % 360
      elif max_val == g:
          h = (60 * ((b - r) / diff) + 120) % 360
      else:
          h = (60 * ((r - g) / diff) + 240) % 360
      
      # 饱和度
      s = 0 if max_val == 0 else diff / max_val
      
      # 明度
      v = max_val
      
      return h, s, v
  ```

**错误 3：`ee.FeatureCollection.sort` → `FeatureCollection.limit`**
- GEE: 
  ```python
  fc = ee.FeatureCollection('users/example/fc')
  sorted_fc = fc.sort('population', ascending=False)  # 按人口降序排序
  ```
- OGE: 
  ```python
  fc = Service.getFeatureCollection('users/example/fc')
  limited_fc = fc.limit(10)  # 限制只返回 10 个要素
  ```
- 问题：`sort` 是排序；`limit` 是限制数量
- 修正：用 Python 实现 `sort()` 方法
  ```python
  def feature_collection_sort(collection, property_name, ascending=True):
      """对要素集合按属性排序"""
      return sorted(collection, 
                    key=lambda f: f.get(property_name, 0), 
                    reverse=not ascending)
  ```

**错误 4：`ee.FeatureCollection.geometry` → `FeatureCollection.union`**
- GEE: 
  ```python
  fc = ee.FeatureCollection('users/example/fc')
  geometry = fc.geometry()  # 获取集合中所有要素的几何（返回一个 GeometryCollection）
  ```
- OGE: 
  ```python
  fc = Service.getFeatureCollection('users/example/fc')
  merged = fc.union()  # 将所有几何合并为一个 Geometry
  ```
- 问题：`geometry()` 是获取所有几何对象；`union()` 是合并所有几何
- 修正：用 Python 实现 `geometry()` 方法
  ```python
  def feature_collection_geometry(collection):
      """获取要素集合中所有要素的几何对象"""
      return [f.geometry() for f in collection]
  ```

**错误 5：`ee.Filter.withinDistance` → `Feature.withinDistance`**
- GEE: 
  ```python
  fc = ee.FeatureCollection('users/example/fc')        # 加载要素集合
  target = ee.Feature(ee.Geometry.Point([116.3, 39.7]))  # 目标点要素
  filtered = fc.filter(ee.Filter.withinDistance(target, 1000))  # 返回 Filter 对象，用于 fc.filter()
  ```
- OGE: 
  ```python
  f1 = Feature(Geometry.Point([116.3, 39.7]))  # 第一个要素
  f2 = Feature(Geometry.Point([116.31, 39.71]))  # 第二个要素
  result = f1.withinDistance(f2, 1000)  # 返回 Boolean，判断两个要素的距离
  ```
- 问题：GEE 的 Filter 返回 Filter 对象用于集合过滤；OGE 返回 Boolean 用于单要素判断
- 修正：用 Python 循环实现集合级距离过滤
  ```python
  fc = Service.getFeatureCollection('users/example/fc')
  target_feature = Feature(Geometry.Point([116.3, 39.7]))
  distance = 1000
  filtered = [f for f in fc 
              if f.withinDistance(target_feature, distance)]
  ```

**错误 6：`ee.Image.and` → `Coverage.bitwiseAnd`**
- GEE: 
  ```python
  # 逻辑与（Logical AND）
  image1 = ee.Image(1)  # 所有像素值为 1
  image2 = ee.Image(0)  # 所有像素值为 0
  result = image1.and(image2)  # 返回 0（因为一个为假）
  # 结果: 所有像素为 0
  
  # 逻辑与的特点：返回值只有 0 或 1
  # True(非零) AND True(非零) = 1
  # True(非零) AND False(零) = 0
  # False(零) AND True(非零) = 0
  # False(零) AND False(零) = 0
  ```
- OGE (映射到 bitwiseAnd): 
  ```python
  # 位与（Bitwise AND）
  image1 = Coverage.constant(5)  # 二进制: 0101
  image2 = Coverage.constant(3)  # 二进制: 0011
  result = image1.bitwiseAnd(image2)  # 返回 1 (二进制: 0001)
  # 结果: 所有像素为 1
  
  # 位与的特点：按二进制位进行 AND 运算
  # 5 (0101) AND 3 (0011) = 1 (0001)
  ```
- 问题：
  - `ee.Image.and()` 是**逻辑与**，返回 0 或 1
  - `Coverage.bitwiseAnd()` 是**位与**，按二进制位运算
  - 两者功能完全不同！
- 修正：用 Python 实现逻辑与
  ```python
  def logical_and(image1, image2):
      """逻辑与运算（Logical AND）
      
      对两个图像进行逐像素逻辑与运算，返回 0 或 1。
      """
      import numpy as np
      # 非零值视为 True，零值视为 False
      return np.where((image1 != 0) & (image2 != 0), 1, 0)
  ```

---

## 二、Python 实现的 API（90 个）

### 2.1 基础 Python 实现（45 个）

文件：`gee_python_functions.py`

#### Array 类（4 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `ee.Array` | `ee_array()` | 构造数组 |
| `ee.Array.matrixDeterminant` | `ee_array_matrix_determinant()` | 行列式 |
| `ee.Array.matrixInverse` | `ee_array_matrix_inverse()` | 逆矩阵 |
| `ee.Array.matrixTrace` | `ee_array_matrix_trace()` | 矩阵迹 |

#### Date 类（10 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `ee.Date` | `ee_date()` | 构造日期 |
| `ee.Date.advance` | `ee_date_advance()` | 日期加减 |
| `ee.Date.dayOfYear` | `ee_date_day_of_year()` | 一年中的第几天 |
| `ee.Date.difference` | `ee_date_difference()` | 日期差值 |
| `ee.Date.format` | `ee_date_format()` | 格式化日期 |
| `ee.Date.get` | `ee_date_get()` | 获取日期单位 |
| `ee.Date.getRelative` | `ee_date_get_relative()` | 获取相对值 |
| `ee.Date.parse` | `ee_date_parse()` | 解析日期 |
| `ee.Date.subtract` | `ee_date_subtract()` | 日期减法 |
| `ee.DateRange` | `ee_date_range()` | 日期范围 |

#### Dictionary 类（5 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `ee.Dictionary` | `ee_dictionary()` | 构造字典 |
| `ee.Dictionary.get` | `ee_dictionary_get()` | 获取键值 |
| `ee.Dictionary.getInfo` | `ee_dictionary_get_info()` | 获取信息 |
| `ee.Dictionary.set` | `ee_dictionary_set()` | 设置键值 |
| `ee.Dictionary.toList` | `ee_dictionary_to_list()` | 转列表 |

#### Number 类（6 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `ee.Number` | `ee_number()` | 构造数值 |
| `ee.Number.divide` | `ee_number_divide()` | 除法 |
| `ee.Number.format` | `ee_number_format()` | 格式化 |
| `ee.Number.gte` | `ee_number_gte()` | 大于等于 |
| `ee.Number.lte` | `ee_number_lte()` | 小于等于 |
| `ee.Number.multiply` | `ee_number_multiply()` | 乘法 |

#### String 类（2 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `ee.String` | `ee_string()` | 构造字符串 |
| `ee.String.format` | `ee_string_format()` | 格式化字符串 |

#### List 类（15 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `ee.List` | `ee_list()` | 构造列表 |
| `ee.List.contains` | `ee_list_contains()` | 包含判断 |
| `ee.List.filter` | `ee_list_filter()` | 过滤 |
| `ee.List.flatten` | `ee_list_flatten()` | 展平 |
| `ee.List.get` | `ee_list_get()` | 获取元素 |
| `ee.List.group` | `ee_list_group()` | 分组统计 |
| `ee.List.join` | `ee_list_join()` | 连接 |
| `ee.List.map` | `ee_list_map()` | 映射 |
| `ee.List.remove` | `ee_list_remove()` | 移除 |
| `ee.List.repeat` | `ee_list_repeat()` | 重复 |
| `ee.List.sequence` | `ee_list_sequence()` | 生成序列 |
| `ee.List.size` | `ee_list_size()` | 获取长度 |
| `ee.List.slice` | `ee_list_slice()` | 切片 |
| `ee.List.sort` | `ee_list_sort()` | 排序 |
| `ee.List.zip` | `ee_listzip()` | 压缩 |

#### FeatureCollection 类（2 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `ee.FeatureCollection.map` | `ee_feature_collection_map()` | 映射 |
| `ee.FeatureCollection.iterate` | `ee_feature_collection_iterate()` | 迭代 |

#### print 函数（1 个）

| GEE API | Python 函数 | 说明 |
|---|---|---|
| `print` | `gee_print()` | 控制台输出 |

---

### 2.2 扩展 Python 实现（45 个）

文件：`gee_unmatched_functions.py`

#### 图像处理类（12 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.Image.exp` | `ee_image_exp()` | numpy |
| `ee.Image.matrixMultiply` | `ee_image_matrix_multiply()` | numpy |
| `ee.Image.random` | `ee_image_random()` | numpy |
| `ee.Image.unitScale` | `ee_image_unit_scale()` | numpy |
| `ee.Image.reduce` | `ee_image_reduce()` | numpy |
| `ee.Image.reduceNeighborhood` | `ee_image_reduce_neighborhood()` | scipy |
| `ee.Image.connectedPixelCount` | `ee_image_connected_pixel_count()` | scipy |
| `ee.Image.arraySlice` | `ee_image_array_slice()` | numpy |
| `ee.Image.arraySort` | `ee_image_array_sort()` | numpy |
| `ee.Image.arrayGet` | `ee_image_array_get()` | numpy |
| `ee.Image.argmax` | `ee_image_argmax()` | numpy |
| `ee.Image.argmin` | `ee_image_argmin()` | numpy |

#### 图像集合类（9 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.ImageCollection.count` | `ee_image_collection_count()` | 无 |
| `ee.ImageCollection.iterate` | `ee_image_collection_iterate()` | 无 |
| `ee.ImageCollection.reduce` | `ee_image_collection_reduce()` | numpy |
| `ee.ImageCollection.max` | `ee_image_collection_max()` | numpy |
| `ee.ImageCollection.min` | `ee_image_collection_min()` | numpy |
| `ee.ImageCollection.mean` | `ee_image_collection_mean()` | numpy |
| `ee.ImageCollection.median` | `ee_image_collection_median()` | numpy |
| `ee.ImageCollection.sort` | `ee_image_collection_sort()` | 无 |
| `ee.ImageCollection.toList` | `ee_image_collection_to_list()` | 无 |

#### 特征集合类（4 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.FeatureCollection.flatten` | `ee_feature_collection_flatten()` | 无 |
| `ee.FeatureCollection.reduceColumns` | `ee_feature_collection_reduce_columns()` | numpy |
| `ee.FeatureCollection.randomPoints` | `ee_feature_collection_random_points()` | random |
| `ee.FeatureCollection.toList` | `ee_feature_collection_to_list()` | 无 |

#### 过滤器类（4 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.Filter.equals` | `ee_filter_equals()` | 无 |
| `ee.Filter.notEquals` | `ee_filter_not_equals()` | 无 |
| `ee.Filter.stringContains` | `ee_filter_string_contains()` | 无 |
| `ee.Filter.stringEquals` | `ee_filter_string_equals()` | 无 |

#### Reducer 类（10 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.Reducer.mean` | `ee_reducer_mean()` | 无 |
| `ee.Reducer.median` | `ee_reducer_median()` | 无 |
| `ee.Reducer.sum` | `ee_reducer_sum()` | 无 |
| `ee.Reducer.count` | `ee_reducer_count()` | 无 |
| `ee.Reducer.min` | `ee_reducer_min()` | 无 |
| `ee.Reducer.max` | `ee_reducer_max()` | 无 |
| `ee.Reducer.stdDev` | `ee_reducer_std_dev()` | 无 |
| `ee.Reducer.variance` | `ee_reducer_variance()` | 无 |
| `ee.Reducer.histogram` | `ee_reducer_histogram()` | 无 |
| `ee.Reducer.percentile` | `ee_reducer_percentile()` | 无 |

#### 连接类（3 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.Join.apply` | `ee_join_apply()` | 无 |
| `ee.Join.saveAll` | `ee_join_save_all()` | 无 |
| `ee.Join.saveFirst` | `ee_join_save_first()` | 无 |

#### 算法类（3 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.Algorithms.CannyEdgeDetector` | `ee_algorithms_canny_edge_detector()` | skimage/scipy |
| `ee.Algorithms.Landsat.TOA` | `ee_algorithms_landsat_toa()` | 无 |
| `ee.Terrain.products` | `ee_terrain_products()` | scipy |

#### 分类器类（3 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.Classifier.amnhMaxent` | `ee_classifier_amnh_maxent()` | 无 |
| `ee.Classifier.explain` | `ee_classifier_explain()` | 无 |
| `ee.Classifier.setOutputMode` | `ee_classifier_set_output_mode()` | 无 |

#### 其他类（3 个）

| GEE API | Python 函数 | 依赖 |
|---|---|---|
| `ee.ConfusionMatrix.consumersAccuracy` | `ee_confusion_matrix_consumers_accuracy()` | numpy |
| `ee.Geometry.coordinates` | `ee_geometry_coordinates()` | 无 |
| `ee.batch.Export.table.toCloudStorage` | `ee_batch_export_table_to_cloud_storage()` | 无 |

---

## 三、分类器修正方案

### 3.1 需要修正的分类器映射

| GEE 分类器 | 当前映射 | 建议映射 | Python 实现方案 |
|---|---|---|---|
| `ee.Classifier.libsvm` | `Coverage.svmClassificationBySAGA` | ✅ 保留 | - |
| `ee.Classifier.smileRandomForest` | `Coverage.svmClassificationBySAGA` | ❌ 需修正 | `sklearn.ensemble.RandomForestClassifier` |
| `ee.Classifier.smileCart` | `Coverage.svmClassificationBySAGA` | ❌ 需修正 | `sklearn.tree.DecisionTreeClassifier` |
| `ee.Classifier.minimumDistance` | `Coverage.svmClassificationBySAGA` | ❌ 需修正 | `sklearn.neighbors.KNeighborsClassifier` |
| `ee.Classifier.naiveBayes` | `Coverage.svmClassificationBySAGA` | ❌ 需修正 | `sklearn.naive_bayes.GaussianNB` |
| `ee.Classifier.smileKMeans` | `Coverage.svmClassificationBySAGA` | ❌ 需修正 | `sklearn.cluster.KMeans` |
| 其他 3 个 | 同上 | ❌ 需修正 | 对应 sklearn 实现 |

### 3.2 Python 实现示例

```python
# 随机森林
from sklearn.ensemble import RandomForestClassifier
def ee_classifier_random_forest(features, labels, num_trees=10):
    clf = RandomForestClassifier(n_estimators=num_trees)
    return clf.fit(features, labels)

# CART 决策树
from sklearn.tree import DecisionTreeClassifier
def ee_classifier_cart(features, labels):
    clf = DecisionTreeClassifier()
    return clf.fit(features, labels)

# 最小距离（K近邻）
from sklearn.neighbors import KNeighborsClassifier
def ee_classifier_minimum_distance(features, labels, n_neighbors=1):
    clf = KNeighborsClassifier(n_neighbors=n_neighbors)
    return clf.fit(features, labels)

# 朴素贝叶斯
from sklearn.naive_bayes import GaussianNB
def ee_classifier_naive_bayes(features, labels):
    clf = GaussianNB()
    return clf.fit(features, labels)
```

---

## 四、Filter → Collection 转换方案

### 4.1 转换规则

| GEE Filter | 转换为 OGE 调用 | Python 实现 |
|---|---|---|
| `ee.Filter.bounds(geom)` | `FeatureCollection.filterBounds(geom)` | 直接调用 |
| `ee.Filter.date(start, end)` | `FeatureCollection.filterDate(start, end)` | 直接调用 |
| `ee.Filter.calendarRange(year, month, day)` | - | Python 解析日期 + `filterDate` |
| `ee.Filter.withinDistance(geom, dist)` | - | `filtered = [f for f in fc if f.withinDistance(target_feature, dist)]` |
| `ee.Filter.contains(key, value)` | `FeatureCollection.filterMetadata(key, 'equals', value)` | 转换调用 |

### 4.2 GEE 示例 → OGE 示例

```python
# ===== 示例 1：bounds 过滤 =====

# GEE 原始代码
fc = ee.FeatureCollection('users/example/featureCollection')  # 加载要素集合
roi = ee.Geometry.Rectangle([116.2, 39.6, 116.4, 39.8])     # 定义研究区域
filtered = fc.filter(ee.Filter.bounds(roi))                  # 按范围过滤

# OGE 转换后
fc = Service.getFeatureCollection('users/example/featureCollection')  # 加载要素集合
roi = Geometry.Rectangle([116.2, 39.6, 116.4, 39.8])                 # 定义研究区域
filtered = fc.filterBounds(roi)                                       # 直接调用 filterBounds


# ===== 示例 2：日期过滤 =====

# GEE 原始代码
fc = ee.FeatureCollection('users/example/featureCollection')
start_date = '2023-01-01'
end_date = '2023-12-31'
filtered = fc.filter(ee.Filter.date(start_date, end_date))

# OGE 转换后
fc = Service.getFeatureCollection('users/example/featureCollection')
start_date = '2023-01-01'
end_date = '2023-12-31'
filtered = fc.filterDate(start_date, end_date)


# ===== 示例 3：withinDistance 过滤 =====

# GEE 原始代码
fc = ee.FeatureCollection('users/example/featureCollection')
target = ee.Feature(ee.Geometry.Point([116.3, 39.7]))  # 目标点
distance = 1000                                        # 距离（米）
filtered = fc.filter(ee.Filter.withinDistance(target, distance))

# OGE + Python 实现（OGE 没有集合级的 withinDistance 过滤）
fc = Service.getFeatureCollection('users/example/featureCollection')
target_feature = Feature(Geometry.Point([116.3, 39.7]))  # 目标点
distance = 1000                                          # 距离（米）
filtered = [f for f in fc 
            if f.withinDistance(target_feature, distance)]  # 用 Python 循环实现


# ===== 示例 4：属性过滤 =====

# GEE 原始代码
fc = ee.FeatureCollection('users/example/featureCollection')
filtered = fc.filter(ee.Filter.equals('class', 1))

# OGE 转换后
fc = Service.getFeatureCollection('users/example/featureCollection')
filtered = fc.filterMetadata('class', 'equals', 1)


# ===== 示例 5：calendarRange 日期范围 =====

# GEE 原始代码
fc = ee.FeatureCollection('users/example/featureCollection')
filtered = fc.filter(ee.Filter.calendarRange(2023, 2023, 'year'))

# OGE + Python 实现
fc = Service.getFeatureCollection('users/example/featureCollection')
from datetime import datetime
start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)
filtered = fc.filterDate(start, end)
```

---

## 五、依赖库说明

### 5.1 基础依赖（必须）

```bash
pip install numpy
```

### 5.2 扩展依赖（建议）

```bash
pip install scipy scikit-image scikit-learn
```

### 5.3 可选依赖

```bash
pip install geopandas rasterio pandas
```

### 5.4 各功能所需依赖

| 功能 | 依赖库 |
|---|---|
| 基础运算、数组操作 | numpy |
| 邻域分析、连通分量 | scipy |
| Canny 边缘检测 | scikit-image |
| 分类器实现 | scikit-learn |
| 矢量集合操作 | geopandas |
| 栅格读取 | rasterio |

---

## 六、待实现的 API（约 80 个）

### 6.1 UI 组件类（约 50 个）

- `ui.Button`, `ui.Chart`, `ui.Checkbox`, `ui.DatePicker`
- `ui.Dropdown`, `ui.Label`, `ui.Map`, `ui.Panel`
- `ui.RadioButtons`, `ui.Select`, `ui.Slider`, `ui.Table`
- `ui.Textbox`, `ui.Thumbnail` 等

**建议**：需确认 OGE 是否有对应 UI 组件，或使用 Python GUI 库实现。

### 6.2 复杂算法类（约 15 个）

- `ee.Algorithms.Image.Segmentation.SNIC`
- `ee.Image.glcmTexture`
- `ee.Image.connectedComponents`
- `ee.Image.gapfill`
- `ee.Image.interpolate`
- `ee.Image.selfMask` 等

**建议**：需要专门的图像处理库实现。

### 6.3 批处理/导出类（约 10 个）

- `Export.video.toDrive`
- `ee.batch.Export.table.toAsset`
- `ee.batch.Task.*`

**建议**：使用 Python 任务调度框架实现。

### 6.4 其他类（约 5 个）

- `ee.Classifier`, `ee.ConfusionMatrix.*`
- `ee.Kernel`, `require` 等

**建议**：根据具体需求逐个实现。

---

## 七、修正建议优先级

### 🔴 高优先级（立即修正）

1. **5 个严重映射错误**
   - `ee.Feature.set` → Python 实现
   - `ee.Image.rgbToHsv` → 修正方向
   - `ee.FeatureCollection.sort` → Python 实现
   - `ee.FeatureCollection.geometry` → Python 实现
   - `ee.Filter.withinDistance` → Python 实现

2. **8 个分类器映射修正**
   - 改用 scikit-learn 分别实现

### 🟠 中优先级（规划修正）

3. **Filter → Collection 转换**
   - 5 个 Filter API 需要转换调用方式

4. **对象类型不匹配标注**
   - 16 个 API 需要添加使用注意事项

### 🟢 低优先级（待需求确认）

5. **UI 组件类实现**
6. **复杂算法实现**
7. **批处理框架实现**

---

## 八、使用指南

### 8.1 使用 Python 函数

```python
# 导入基础函数
from gee_python_functions import *

# 导入扩展函数
from gee_unmatched_functions import *

# ===== 示例 1：日期操作 =====
date = ee_date('2023-01-15')           # 构造日期
new_date = ee_date_advance(date, 5, 'day')  # 加5天


# ===== 示例 2：列表操作 =====
seq = ee_list_sequence(1, 10)           # 生成 [1, 2, ..., 10]
result = ee_list_map(seq, lambda x: x * 2)  # 映射为 [2, 4, ..., 20]


# ===== 示例 3：集合归约 =====
# 准备数据
import numpy as np
collection = [np.random.rand(100, 100) for _ in range(5)]  # 5 张 100x100 图像
mean_img = ee_image_collection_mean(collection)  # 计算均值图像


# ===== 示例 4：过滤器 =====
# 准备数据
collection = [
    {'id': 1, 'class': 0, 'value': 10},
    {'id': 2, 'class': 1, 'value': 20},
    {'id': 3, 'class': 1, 'value': 30},
]
filter_fn = ee_filter_equals('class', 1)  # 创建过滤器
filtered = [f for f in collection if filter_fn(f)]  # 应用过滤器
# 结果: [{'id': 2, 'class': 1, 'value': 20}, {'id': 3, 'class': 1, 'value': 30}]


# ===== 示例 5：Canny 边缘检测 =====
# 准备数据
image = np.random.rand(100, 100)  # 100x100 随机图像
edges = ee_algorithms_canny_edge_detector(image, threshold=0.5)  # 边缘检测


# ===== 示例 6：地形分析 =====
# 准备数据
dem = np.random.rand(100, 100) * 100  # 100x100 高程数据
terrain = ee_terrain_products(dem)  # 计算坡度、坡向、山体阴影
slope = terrain['slope']
aspect = terrain['aspect']
hillshade = terrain['hillshade']
```

### 8.2 使用映射转换器

```python
from gee_to_ge_mapping import GeeToOgeConverter

# 加载映射表
converter = GeeToOgeConverter(
    'gee_to_oge_matches.xlsx',
    'gee.json'
)

# 获取 API 信息
info = converter.get_api_info('ee.Image.add')

# 获取 Python 实现
from gee_python_functions import get_python_function
fn = get_python_function('ee.Array.matrixDeterminant')
result = fn([[1, 2], [3, 4]])  # -2.0
```

---

## 九、相关文档

| 文档 | 路径 |
|---|---|
| 映射审查报告 | `GEE_OGE映射审查报告.md` |
| 未匹配 API 分析报告 | `未匹配API分析报告.md` |
| 未匹配 API 实现报告 | `未匹配API实现报告.md` |
| 完整审查数据 | `full_audit_report.json` |
| 审查问题列表 | `mapping_review_issues.json` |

---

## 十、总结与建议

### 10.1 已完成的工作

✅ 解析了 202 条 Excel 映射表  
✅ 审查了映射合理性，识别 45 个问题  
✅ 实现了 90 个 Python 函数  
✅ 识别了 5 个严重映射错误  
✅ 提供了分类器修正方案  
✅ 提供了 Filter → Collection 转换方案  

### 10.2 建议下一步

1. **立即修正 5 个严重映射错误**
2. **用 scikit-learn 实现 8 个分类器**
3. **合并两个 Python 函数文件**
4. **为所有 Python 函数编写单元测试**
5. **补充剩余 80 个待实现 API**
6. **更新 Excel 映射表，标注修正内容**

---

*报告生成完毕 · 最后更新：2026-07-31*