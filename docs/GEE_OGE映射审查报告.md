# GEE → OGE 映射审查报告

生成时间：2026-07-31

---

## 📊 审查概览

| 统计项 | 数量 |
|---|---|
| 总映射条目 | 202 |
| 审查问题总数 | 45 |
| 🔴 严重错误 | 5 |
| 🟡 警告问题 | 26 |
| ℹ️ 提示信息 | 14 |

---

## 🔴 严重错误（必须修正）

### 错误 1：功能完全不同

| GEE API | OGE API | 问题 | 修正建议 |
|---|---|---|---|
| `ee.Feature.set` | `Feature.select` | set 设置属性值 ≠ select 选择字段 | Python 实现 `Feature.set(key, value)` |

**详细说明**：
- GEE: `ee.Feature.set(key, value)` 用于设置 Feature 的属性值
- OGE: `Feature.select()` 用于选择字段，返回子集
- 这两个功能完全不同，不能替换

---

### 错误 2：功能不匹配

| GEE API | OGE API | 问题 | 修正建议 |
|---|---|---|---|
| `ee.FeatureCollection.geometry` | `FeatureCollection.union` | geometry 获取几何 ≠ union 合并几何 | Python 实现 `geometry()` |

**详细说明**：
- GEE: `geometry()` 获取集合中所有要素的几何对象
- OGE: `union()` 将所有几何合并为一个
- 获取 vs 合并，语义不同

---

### 错误 3：功能不匹配

| GEE API | OGE API | 问题 | 修正建议 |
|---|---|---|---|
| `ee.FeatureCollection.sort` | `FeatureCollection.limit` | sort 排序 ≠ limit 限制数量 | Python 实现 `sort()` |

**详细说明**：
- GEE: `sort(property, ascending)` 按属性排序
- OGE: `limit(max)` 限制返回数量
- 排序 vs 限制，功能完全不同

---

### 错误 4：层级不匹配

| GEE API | OGE API | 问题 | 修正建议 |
|---|---|---|---|
| `ee.Filter.withinDistance` | `Feature.withinDistance` | Filter 是集合级过滤器 ≠ Feature 是单要素判断 | Python 实现集合级过滤器 |

**详细说明**：
- GEE: `ee.Filter.withinDistance(geom, dist)` 返回 Filter 对象，用于 `fc.filter()`
- OGE: `Feature.withinDistance(other, dist)` 返回 Boolean
- 集合级 vs 单要素级，无法直接替换

**修正代码示例**：
```python
# GEE 用法
fc.filter(ee.Filter.withinDistance(geom, dist))

# OGE 替代方案
fc.filter(lambda f: f.withinDistance(geom_feature, dist))
```

---

### 错误 5：方向相反

| GEE API | OGE API | 问题 | 修正建议 |
|---|---|---|---|
| `ee.Image.rgbToHsv` | `Coverage.hsvToRgb` | RGB→HSV ≠ HSV→RGB | 修正为 `Coverage.rgbToHsv` 或 Python 实现 |

**详细说明**：
- GEE: `rgbToHsv` 将 RGB 转换为 HSV
- OGE: `hsvToRgb` 将 HSV 转换为 RGB
- 方向完全相反！

---

## 🟡 警告问题（建议修正）

### 分类 1：分类器映射问题（9 条）

**问题**：9 个不同的 GEE 分类器全部映射到同一个 OGE SVM API

| GEE 分类器 | 当前 OGE API | 问题 |
|---|---|---|
| `ee.Classifier.libsvm` | `Coverage.svmClassificationBySAGA` | ✅ 正确（SVM → SVM） |
| `ee.Classifier.smileRandomForest` | `Coverage.svmClassificationBySAGA` | ❌ 随机森林 → SVM |
| `ee.Classifier.smileCart` | `Coverage.svmClassificationBySAGA` | ❌ CART 决策树 → SVM |
| `ee.Classifier.minimumDistance` | `Coverage.svmClassificationBySAGA` | ❌ 最小距离 → SVM |
| `ee.Classifier.naiveBayes` | `Coverage.svmClassificationBySAGA` | ❌ 朴素贝叶斯 → SVM |
| `ee.Classifier.smileGAM` | `Coverage.svmClassificationBySAGA` | ❌ GAM → SVM |
| `ee.Classifier.smileKMeans` | `Coverage.svmClassificationBySAGA` | ❌ KMeans聚类 → SVM |
| `ee.Classifier.smileLVQ` | `Coverage.svmClassificationBySAGA` | ❌ LVQ → SVM |
| `ee.Classifier.smileMLP` | `Coverage.svmClassificationBySAGA` | ❌ MLP神经网络 → SVM |

**修正方案**：使用 Python + sklearn 分别实现

```python
# 随机森林
def ee_classifier_random_forest(features, labels, num_trees=10):
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=num_trees)
    return clf.fit(features, labels)

# CART 决策树
def ee_classifier_cart(features, labels):
    from sklearn.tree import DecisionTreeClassifier
    clf = DecisionTreeClassifier()
    return clf.fit(features, labels)

# 最小距离（K近邻）
def ee_classifier_minimum_distance(features, labels, n_neighbors=1):
    from sklearn.neighbors import KNeighborsClassifier
    clf = KNeighborsClassifier(n_neighbors=n_neighbors)
    return clf.fit(features, labels)

# 朴素贝叶斯
def ee_classifier_naive_bayes(features, labels):
    from sklearn.naive_bayes import GaussianNB
    clf = GaussianNB()
    return clf.fit(features, labels)

# KMeans 聚类
def ee_clusterer_kmeans(features, n_clusters=8):
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=n_clusters)
    return kmeans.fit(features)
```

---

### 分类 2：功能差异（4 条）

| GEE API | OGE API | 问题 | 修正建议 |
|---|---|---|---|
| `Map.addLayer` | `getMap` | 添加图层 ≠ 获取地图 | Python 实现或转换调用方式 |
| `Map.setOptions` | `Coverage.addStyles` | 设置地图选项 ≠ 添加样式 | 根据对象类型分发 |
| `ee.Image.pixelArea` | `Coverage.surfAreaByGrass` | 像素面积 ≠ 地形表面积 | 计算方式不同，标注差异 |
| `ee.Image.classify` | `Coverage.svmClassificationBySAGA` | classify 支持多种分类器 | 仅映射到 SVM，需补充其他 |

---

### 分类 3：对象类型不匹配（16 条）

#### ImageCollection → FeatureCollection（6 条）

| GEE API | OGE API | 问题 |
|---|---|---|
| `ee.ImageCollection.limit` | `FeatureCollection.limit` | 影像集合 → 矢量集合 |
| `ee.ImageCollection.randomColumn` | `FeatureCollection.randomColumn` | 影像集合 → 矢量集合 |
| `ee.ImageCollection.filterBounds` | `FeatureCollection.filterBounds` | 影像集合 → 矢量集合 |
| `ee.ImageCollection.filterDate` | `FeatureCollection.filterDate` | 影像集合 → 矢量集合 |
| `ee.ImageCollection.filterMetadata` | `FeatureCollection.filterMetadata` | 影像集合 → 矢量集合 |
| `ee.Image.sample` | `FeatureCollection.sample` | 影像 → 矢量 |

**说明**：OGE 可能没有 Coverage/CoverageCollection 的对应方法，使用时需注意对象类型转换。

#### Filter → Collection（5 条）

| GEE API | OGE API | 问题 | 修正方案 |
|---|---|---|---|
| `ee.Filter.bounds` | `FeatureCollection.filterBounds` | 过滤器 → 集合方法 | 转换调用方式 |
| `ee.Filter.date` | `FeatureCollection.filterDate` | 过滤器 → 集合方法 | 转换调用方式 |
| `ee.Filter.calendarRange` | `FeatureCollection.filterDate` | 过滤器 → 集合方法 | Python 实现日期解析 |
| `ee.Filter.withinDistance` | `Feature.withinDistance` | 过滤器 → 要素方法 | Python 实现集合过滤器 |
| `ee.Filter.contains` | `Feature.contains` | 过滤器 → 要素方法 | 转换调用方式 |

**修正方案**：

```python
# ee.Filter.bounds(geom) 转换为
FeatureCollection.filterBounds(geom)

# ee.Filter.date(start, end) 转换为
FeatureCollection.filterDate(start, end)

# ee.Filter.calendarRange(year, month, day) 转换为
# Python 实现日期范围解析后调用
FeatureCollection.filterDate(parsed_start, parsed_end)

# ee.Filter.withinDistance(geom, dist) 转换为
FeatureCollection.filter(lambda f: f.withinDistance(geom, dist))
```

#### 其他类型不匹配（5 条）

| GEE API | OGE API | 问题 |
|---|---|---|
| `ee.Geometry.area` | `FeatureCollection.area` | 几何 → 集合 |
| `ee.Geometry.union` | `FeatureCollection.union` | 几何 → 集合 |
| `Map.setOptions` | `FeatureCollection.addStyles` | 地图 → 集合 |
| `Export.table.toAsset` | `FeatureCollection.export` | 导出 → 集合 |
| `Export.table.toDrive` | `FeatureCollection.export` | 导出 → 集合 |

---

## ℹ️ 提示信息（注意即可）

### Filter vs Coverage 运算符（8 条）

| GEE API | OGE API | 说明 |
|---|---|---|
| `ee.Filter.eq` | `Coverage.eq` | 底层运算相同，使用场景不同 |
| `ee.Filter.gt` | `Coverage.gt` | 底层运算相同，使用场景不同 |
| `ee.Filter.gte` | `Coverage.gte` | 底层运算相同，使用场景不同 |
| `ee.Filter.lt` | `Coverage.lt` | 底层运算相同，使用场景不同 |
| `ee.Filter.lte` | `Coverage.lte` | 底层运算相同，使用场景不同 |
| `ee.Filter.not` | `Coverage.not` | 底层运算相同，使用场景不同 |
| `ee.Filter.or` | `Coverage.or` | 底层运算相同，使用场景不同 |

**说明**：Filter 用于集合过滤，Coverage 用于像元计算，但底层运算相同。

### 功能近似（6 条）

| GEE API | OGE API | 说明 |
|---|---|---|
| `ee.Image.reduceResolution` | `Coverage.resample` | 降分辨率 vs 重采样 |
| `ee.Image.reduceToVectors` | `Coverage.polygonizeByGDAL` | 栅格转矢量 vs 转多边形 |
| `ee.Image.toInt` | `Coverage.toInt32` | 泛型 vs 指定位宽 |
| `ee.Reducer.max` | `Coverage.maxi` | Reducer vs 像元计算 |
| `ee.Reducer.min` | `Coverage.mini` | Reducer vs 像元计算 |
| `ee.Filter.calendarRange` | `FeatureCollection.filterDate` | 年月日过滤 vs 日期过滤 |

---

## 🔀 一对多映射（8 条）

| GEE API | OGE API 数量 | OGE API 列表 | 修正建议 |
|---|---|---|---|
| `Map.setOptions` | 4 | Coverage/Feature/Collection 的 addStyles | Python 类型分发 |
| `ee.Geometry` | 2 | Geometry.LineString, Geometry.Polygon | 参数分发 |
| `ee.Number` | 2 | Python Int, Python Float | 保留（自动处理） |
| `ee.Number.divide` | 2 | Python Int, Python Float | 保留（自动处理） |
| `ee.Number.format` | 2 | Python Int, Python Float | 保留（自动处理） |
| `ee.Number.gte` | 2 | Python Int, Python Float | 保留（自动处理） |
| `ee.Number.lte` | 2 | Python Int, Python Float | 保留（自动处理） |
| `ee.Number.multiply` | 2 | Python Int, Python Float | 保留（自动处理） |

---

## 🔀 多对一映射（36 个 OGE API）

### 合理的多对一（无需修正）

| OGE API | GEE API 数量 | 说明 |
|---|---|---|
| `Python List` | 17 | 多个 List/Array 方法返回列表 |
| `Python Function` | 10 | 用 Python 函数实现多种功能 |
| `Python Int` | 6 | 数值运算返回整数 |
| `Python Float` | 6 | 数值运算返回浮点数 |
| `Python Dictionary` | 5 | 字典操作返回字典 |
| `Python String` | 2 | 字符串操作返回字符串 |
| `Feature.buffer` | 3 | 不同对象的缓冲区操作 |
| `Coverage.eq/gt/gte/lt/not/or` | 2 | Filter 和 Image 的相同运算符 |
| `Coverage.maxi/mini` | 2 | Reducer 和 Image 的 max/min |

### 需要注意的多对一

| OGE API | GEE API 数量 | 问题 |
|---|---|---|
| `Coverage.svmClassificationBySAGA` | 9 | 不同分类器 → 同一 SVM |
| `FeatureCollection.filterDate` | 4 | 多种日期过滤方式 |
| `FeatureCollection.filterBounds` | 3 | Filter + Collection 方法 |
| `FeatureCollection.limit` | 3 | limit + sort 映射 |
| `FeatureCollection.union` | 3 | union + geometry 映射 |

---

## ✅ 修正优先级

| 优先级 | 类别 | 数量 | 修正方式 |
|---|---|---|---|
| 🔴 最高 | 严重错误 | 5 | Python 实现 |
| 🟠 高 | 分类器映射 | 9 | Python + sklearn |
| 🟡 中 | Filter → Collection | 5 | 调用层转换 |
| 🟢 低 | 对象类型不匹配 | 16 | 标注注意事项 |
| ⚪ 无需修正 | 合理映射 | 其余 | 保留 |

---

## 📝 修正实施建议

### 1. Python 实现优先

以下 API 应优先使用 Python 实现：

```
ee.Feature.set
ee.FeatureCollection.geometry
ee.FeatureCollection.sort
ee.Filter.withinDistance
ee.Image.rgbToHsv
ee.Classifier.* (除 libsvm 外)
```

### 2. 调用层转换

以下 Filter API 需要在调用时转换为 Collection 方法：

```
ee.Filter.bounds → FeatureCollection.filterBounds
ee.Filter.date → FeatureCollection.filterDate
ee.Filter.calendarRange → Python解析 + FeatureCollection.filterDate
ee.Filter.withinDistance → FeatureCollection.filter(lambda)
```

### 3. 标注差异

以下 API 需要在文档中标注使用差异：

```
ee.ImageCollection.* → FeatureCollection.* (对象类型不同)
ee.Image.pixelArea → Coverage.surfAreaByGrass (计算方式不同)
Map.addLayer → getMap (功能不同)
```

---

## 📁 相关文件

- 映射表：`gee_to_oge_matches.xlsx`
- GEE API 详情：`gee.json`
- OGE API 详情：`oge.json`
- Python 函数实现：`gee_python_functions.py`
- 完整审查数据：`full_audit_report.json`

---

*报告生成完毕*