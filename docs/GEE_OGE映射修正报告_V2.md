# GEE → OGE 映射修正报告（V2）

生成时间：2026-07-31

---

## 📢 声明

**本报告整合了朋友的审查意见，修正了我之前的检查遗漏。**

我的问题：
1. ❌ 只检查了 Excel 映射表中的映射是否合理
2. ❌ 没有在 OGE JSON 中查找更好的替代 API
3. ❌ 漏掉了 2 个重要映射问题
4. ❌ 没有验证 OGE 中是否存在更合适的 API

---

## 📊 修正后的问题统计

| 严重程度 | 数量 | 说明 |
|---|---|---|
| 🔴 **严重错误** | 8 | 映射完全错误，需立即修正 |
| 🟡 **建议改进** | 7 | 映射不理想，有更好的替代方案 |
| ℹ️ **语义差异** | 4 | 功能近似但有差异 |

---

## 🔴 严重错误（8 个）

### 错误 1：`ee.Feature.set` → `Feature.select`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | 设置 Feature 属性值 | 选择/重命名字段 | **设置属性值** |
| **正确映射** | - | ❌ `Feature.select` | ✅ `Feature.set` |

**OGE `Feature.set` 描述**：设置要素的常规属性信息。

---

### 错误 2：`ee.FeatureCollection.geometry` → `FeatureCollection.union`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | 获取集合所有几何对象 | 合并两个集合 | **需 Python 实现** |
| **问题** | - | 功能不同 | OGE 无直接对应 API |
| **修正** | - | ❌ `FeatureCollection.union` | 🐍 Python 实现 |

---

### 错误 3：`ee.FeatureCollection.sort` → `FeatureCollection.limit`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | 按属性排序 | 限制返回数量 | **需 Python 实现** |
| **问题** | - | 功能不同 | OGE 无 `sort` API |
| **修正** | - | ❌ `FeatureCollection.limit` | 🐍 Python 实现 |

---

### 错误 4：`ee.FeatureCollection.aggregate_array` → `FeatureCollection.aggregateStats`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | 返回某属性的所有值列表 | 返回数值统计指标 | **需 Python 实现** |
| **问题** | - | 返回值完全不同 | OGE 无 `aggregateArray` API |
| **修正** | - | ❌ `FeatureCollection.aggregateStats` | 🐍 Python 实现 |

**GEE 示例**：
```python
fc = ee.FeatureCollection('users/example/fc')
values = fc.aggregate_array('property_name')  # 返回 [1, 2, 3, ...] 所有值列表
```

**OGE `aggregateStats` 示例**：
```python
fc = Service.getFeatureCollection('users/example/fc')
stats = fc.aggregateStats('property_name')  # 返回 {mean: 1.5, min: 1, max: 3, ...} 统计指标
```

---

### 错误 5：`ee.Filter.withinDistance` → `Feature.withinDistance`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | 创建距离过滤器 | 判断两个 Feature 距离 | **需 Python 实现** |
| **层级** | Filter 对象（用于集合过滤） | Boolean（单要素判断） | 层级不匹配 |
| **修正** | - | ❌ `Feature.withinDistance` | 🐍 Python 实现集合级过滤器 |

---

### 错误 6：`ee.Image.addBands` → `CoverageCollection.mergeCoverages`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | 把波段追加到同一 Image | 把多 Coverage 组成 CoverageCollection | **添加波段** |
| **正确映射** | - | ❌ `CoverageCollection.mergeCoverages` | ✅ `Coverage.addBands` |

**OGE `Coverage.addBands` 描述**：将 coverage2 中感兴趣的波段添加至 coverage1 中，如果波段重名，overwrite 控制是否重写。

**GEE vs OGE 示例**：
```python
# GEE
image1 = ee.Image('band1.tif')
image2 = ee.Image('band2.tif')
result = image1.addBands(image2)  # 返回包含两个波段的 Image

# OGE (正确映射)
coverage1 = service.getCoverage('band1.tif')
coverage2 = service.getCoverage('band2.tif')
result = coverage1.addBands(coverage2)  # 返回包含两个波段的 Coverage
```

---

### 错误 7：`ee.Image.and` → `Coverage.bitwiseAnd`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | 逻辑与（非零值返回 1） | 位与（二进制位运算） | **逻辑与** |
| **正确映射** | - | ❌ `Coverage.bitwiseAnd` | ✅ `Coverage.and` |

**OGE `Coverage.and` 描述**：逻辑与运算 - 如果两个值都不为零，则返回 1。

**代码对比**：
```python
# GEE: 逻辑与
image1 = ee.Image(5)  # 值: 5 (非零)
image2 = ee.Image(3)  # 值: 3 (非零)
result = image1.and(image2)  # 返回 1 (True AND True = True)

# OGE 正确映射: 逻辑与
coverage1 = Coverage.constant(5)
coverage2 = Coverage.constant(3)
result = coverage1.and(coverage2)  # 返回 1

# OGE 错误映射: 位与
result_bad = coverage1.bitwiseAnd(coverage2)  # 5 & 3 = 1 (二进制: 101 & 011 = 001)
# 虽然本例结果相同，但对于非 0/1 值会有差异
```

---

### 错误 8：`ee.Image.rgbToHsv` → `Coverage.hsvToRgb`

| 维度 | GEE | OGE 当前映射 | OGE 正确映射 |
|---|---|---|---|
| **功能** | RGB → HSV | HSV → RGB | **RGB → HSV** |
| **方向** | 正向转换 | 反方向转换 | 正向转换 |
| **正确映射** | - | ❌ `Coverage.hsvToRgb` | ✅ `Coverage.rgbToHsv` |

**OGE `Coverage.rgbToHsv` 描述**：将 coverage 从 RGB 颜色空间转换为 HSV 颜色空间。

---

## 🟡 建议改进（7 个）

### 问题 1：`Map.setOptions` → `Coverage.addStyles` 等 4 个 API

| 维度 | GEE | OGE 映射 | 问题 |
|---|---|---|---|
| **功能** | 设置地图视图选项（底图配置） | 给数据绑定渲染样式 | **功能完全不同** |
| **对象** | Map（地图视图） | Coverage/Feature（数据图层） | **作用对象不同** |

**分析**：
- GEE `Map.setOptions` 是管控背景底图，不对业务数据附加样式
- OGE `addStyles` 是给栅格/矢量数据对象绑定渲染样式，作用于业务图层
- 这两个功能**完全不对应**

**建议**：需要为 Map 底图配置找到更合适的 OGE API

---

### 问题 2：`ee.Image.get` → `Coverage.selectBands`

| 维度 | GEE | OGE 当前映射 | 问题 |
|---|---|---|---|
| **功能** | 读取影像属性（元数据） | 选择波段 | **功能完全不同** |
| **GEE 返回** | 属性值（如投影、分辨率等） | - |
| **OGE 功能** | - | 从影像中选择任意多个波段 |

**分析**：
- GEE `Image.get('property')` 返回指定属性的值
- OGE `Coverage.selectBands` 是从影像中选择波段
- 应该映射到 `Coverage.metadata`

**正确映射**：`ee.Image.get` → `Coverage.metadata`（获取单景栅格元数据）

---

### 问题 3：`ee.Filter.eq/gt/gte/lt` → `Coverage.eq/gt/gte/lt`

| 维度 | GEE | OGE 映射 | 问题 |
|---|---|---|---|
| **功能** | 属性过滤条件 | 栅格逐像元比较 | **应用场景不同** |
| **GEE 使用** | `fc.filter(ee.Filter.eq('class', 1))` | - |
| **OGE 使用** | - | `c1.eq(c2)` 逐像元比较 |

**分析**：
- GEE `Filter.eq` 是元数据等值过滤条件，用于 `fc.filter()`
- OGE `Coverage.eq` 是栅格逐像元相等比较
- 应该映射到 `FeatureCollection.filterMetadata`

**正确映射**：
| GEE API | 正确 OGE API |
|---|---|
| `ee.Filter.eq` | `FeatureCollection.filterMetadata` |
| `ee.Filter.gt` | `FeatureCollection.filterMetadata` |
| `ee.Filter.gte` | `FeatureCollection.filterMetadata` |
| `ee.Filter.lt` | `FeatureCollection.filterMetadata` |

**示例**：
```python
# GEE
fc = ee.FeatureCollection('users/example/fc')
filtered = fc.filter(ee.Filter.eq('class', 1))

# OGE (正确映射)
fc = Service.getFeatureCollection('users/example/fc')
filtered = fc.filterMetadata('class', 'equals', 1)
```

---

### 问题 4：`ee.Reducer.max/min` → `Coverage.maxi/mini`

| 维度 | GEE | OGE 映射 | 问题 |
|---|---|---|---|
| **功能** | 创建 Reducer 对象 | 两幅 Coverage 逐像元取最大/最小 | **语义不同** |
| **GEE 使用** | `image.reduceRegion(ee.Reducer.max())` | - |
| **OGE 功能** | - | `c1.maxi(c2)` 逐像元取最大 |

**分析**：
- GEE `Reducer.max` 是创建归约器对象，用于 `reduceRegion` 等方法
- OGE `Coverage.maxi` 是两幅栅格逐像元取最大值
- 应该用 `Coverage.reduceRegion(reducer='max')`

**正确实现**：
```python
# GEE
image = ee.Image('example.tif')
max_val = image.reduceRegion(ee.Reducer.max(), geometry)

# OGE (正确实现)
coverage = service.getCoverage('example.tif')
max_val = coverage.reduceRegion(reducer='max', geometry=roi)
```

---

### 问题 5：`ee.Image.reduceResolution` → `Coverage.resample`

| 维度 | GEE | OGE 映射 | 问题 |
|---|---|---|---|
| **功能** | 使用 Reducer 聚合输入像元 | 按插值/尺度重采样 | **核心语义不同** |
| **GEE 特点** | 使用统计方法聚合（mean, max, min 等） | - |
| **OGE 特点** | - | 使用插值方法（nearest, bilinear 等） |

**分析**：
- GEE `reduceResolution` 使用 Reducer 聚合（如取平均值、最大值）
- OGE `resample` 使用插值方法（如最近邻、双线性插值）
- 两者核心语义不同

**建议**：根据具体场景选择 `Coverage.reduceRegion` 或 `Coverage.resample`

---

### 问题 6：`ee.Feature.set` → `Feature.select`（已在错误 1 中修正）

**正确映射**：`ee.Feature.set` → `Feature.set`（OGE 中确实存在此 API）

---

### 问题 7：`ee.Filter.withinDistance` → `Feature.withinDistance`（已在错误 5 中修正）

**建议**：Python 实现集合级距离过滤器

---

## ℹ️ 语义差异（4 个）

| # | GEE API | OGE API | 差异说明 |
|---|---|---|---|
| 1 | `ee.FeatureCollection.style` | `FeatureCollection.addStyles` | GEE 渲染为图像，OGE 添加样式 |
| 2 | `ee.Image.metadata` | `Coverage.metadata` | GEE 返回 Image，OGE 返回元数据值 |
| 3 | `ee.Image.pixelArea` | `Coverage.surfAreaByGrass` | GEE 返回面积栅格，OGE 返回统计值 |
| 4 | `ImageCollection.*` → `FeatureCollection.*` | 5 个 API | 对象类型不同，需确认 OGE 是否有 CoverageCollection 方法 |

---

## 📋 修正建议汇总

### 优先级 1：立即修正（8 个严重错误）

| # | GEE API | 当前 OGE | 正确映射 | 修正方式 |
|---|---|---|---|---|
| 1 | `ee.Feature.set` | `Feature.select` | `Feature.set` | ✅ 直接映射（OGE 已存在） |
| 2 | `ee.FeatureCollection.geometry` | `FeatureCollection.union` | 无直接对应 | 🐍 Python 实现 |
| 3 | `ee.FeatureCollection.sort` | `FeatureCollection.limit` | 无直接对应 | 🐍 Python 实现 |
| 4 | `ee.FeatureCollection.aggregate_array` | `FeatureCollection.aggregateStats` | 无直接对应 | 🐍 Python 实现 |
| 5 | `ee.Filter.withinDistance` | `Feature.withinDistance` | 无直接对应 | 🐍 Python 实现 |
| 6 | `ee.Image.addBands` | `CoverageCollection.mergeCoverages` | `Coverage.addBands` | ✅ 直接映射（OGE 已存在） |
| 7 | `ee.Image.and` | `Coverage.bitwiseAnd` | `Coverage.and` | ✅ 直接映射（OGE 已存在） |
| 8 | `ee.Image.rgbToHsv` | `Coverage.hsvToRgb` | `Coverage.rgbToHsv` | ✅ 直接映射（OGE 已存在） |

### 优先级 2：建议改进（7 个警告）

| # | GEE API | 当前 OGE | 建议映射 | 说明 |
|---|---|---|---|---|
| 1 | `Map.setOptions` | `Coverage.addStyles` 等 | 待查找 | 功能完全不同 |
| 2 | `ee.Image.get` | `Coverage.selectBands` | `Coverage.metadata` | 语义更匹配 |
| 3 | `ee.Filter.eq/gt/gte/lt` | `Coverage.eq/gt/gte/lt` | `FeatureCollection.filterMetadata` | 场景更匹配 |
| 4 | `ee.Reducer.max/min` | `Coverage.maxi/mini` | `Coverage.reduceRegion` | 语义更匹配 |
| 5 | `ee.Image.reduceResolution` | `Coverage.resample` | `Coverage.reduceRegion` 或 `Coverage.resample` | 视场景而定 |
| 6 | 同错误 1 | - | - | - |
| 7 | 同错误 5 | - | - | - |

---

## 🛠️ Python 实现代码

### 1. `ee.FeatureCollection.geometry()`
```python
def feature_collection_geometry(collection):
    """获取要素集合中所有要素的几何对象"""
    return [f.geometry() for f in collection]
```

### 2. `ee.FeatureCollection.sort()`
```python
def feature_collection_sort(collection, property_name, ascending=True):
    """对要素集合按属性排序"""
    return sorted(collection, 
                  key=lambda f: f.get(property_name, 0), 
                  reverse=not ascending)
```

### 3. `ee.FeatureCollection.aggregate_array()`
```python
def feature_collection_aggregate_array(collection, property_name):
    """返回某属性的所有值列表"""
    return [f.get(property_name) for f in collection]
```

### 4. `ee.Filter.withinDistance()` 集合级
```python
def filter_within_distance(collection, target, distance):
    """集合级距离过滤器"""
    return [f for f in collection 
            if f.withinDistance(target, distance)]
```

---

## ✅ 确认的 OGE API 存在性

| OGE API | 是否存在 | 描述 |
|---|---|---|
| `Feature.set` | ✅ 存在 | 设置要素的常规属性信息 |
| `Coverage.addBands` | ✅ 存在 | 将 coverage2 中感兴趣的波段添加至 coverage1 |
| `Coverage.and` | ✅ 存在 | 逻辑与运算 - 两个值都不为零返回 1 |
| `Coverage.rgbToHsv` | ✅ 存在 | RGB 转 HSV 色彩空间 |
| `Coverage.hsvToRgb` | ✅ 存在 | HSV 转 RGB 色彩空间 |
| `FeatureCollection.filterMetadata` | ✅ 存在 | 按元数据过滤 |
| `Coverage.reduceRegion` | ✅ 存在 | 按区域栅格统计运算 |
| `Coverage.metadata` | ✅ 存在 | 获取单景栅格元数据 |

---

## 📝 后续工作

1. **立即修正 Excel 映射表**：将 4 个可以直接修正的映射（错误 1, 6, 7, 8）改为正确的 OGE API
2. **实现 Python 函数**：为 4 个 OGE 无直接对应的 API（错误 2, 3, 4, 5）实现 Python 函数
3. **更新映射表文档**：标注所有修正内容
4. **验证修正后的映射**：确保修正后的映射功能正确

---

*报告生成完毕 · 最后更新：2026-07-31*