# GEE 未匹配 API 分析报告

生成时间：2026-07-31

---

## 📊 分析概览

| 统计项 | 数量 |
|---|---|
| GEE API 总数 | 1425 |
| 已匹配 | 202 |
| **未匹配总数** | **189** |

### 未匹配 API 分析结果

| 可实现方式 | 数量 | 占比 |
|---|---|---|
| 🟢 可 Python 实现 | 75 | 39.7% |
| 🔵 可 OGE 或 Python | 13 | 6.9% |
| 🟡 可 OGE 映射 | 5 | 2.6% |
| 🔴 待分析 | 96 | 50.8% |

---

## 🟢 可 Python 实现的 API（75 个）

这些 API 可以通过 Python 原生功能或第三方库（如 numpy, scipy, scikit-learn）实现：

### 日期/时间处理
| GEE API | Python 实现方式 |
|---|---|
| `ui.Chart.array.values` | 数组值提取 |
| `ui.Chart.image.histogram` | numpy 直方图 |
| `ui.Map.addLayer` | 添加图层 |
| `ui.Map.clear` | 清空地图 |
| `ui.Panel.removeAll` | 移除所有 |
| `ui.SplitPanel` | 分割面板 |

### 算法处理
| GEE API | Python 实现方式 |
|---|---|
| `ee.Algorithms.CannyEdgeDetector` | scikit-image `canny` |
| `ee.Algorithms.Landsat.TOA` | 辐射定标公式 |
| `ee.Classifier.amnhMaxent` | MaxEnt 模型 |
| `ee.Classifier.explain` | 模型解释 |
| `ee.Classifier.setOutputMode` | 设置输出模式 |
| `ee.ConfusionMatrix.consumersAccuracy` | 消费者精度 |

### 集合操作
| GEE API | Python 实现方式 |
|---|---|
| `ee.FeatureCollection.flatten` | 展平嵌套集合 |
| `ee.FeatureCollection.randomPoints` | 随机点生成 |
| `ee.FeatureCollection.reduceColumns` | 列归约 |
| `ee.FeatureCollection.toList` | 集合转列表 |
| `ee.Image.reduceRegions` | 区域归约 |

### 过滤器
| GEE API | Python 实现方式 |
|---|---|
| `ee.Filter.equals` | 等于过滤 |
| `ee.Filter.notEquals` | 不等于过滤 |
| `ee.Filter.stringContains` | 字符串包含过滤 |
| `ee.Filter.stringEquals` | 字符串等于过滤 |

### 几何处理
| GEE API | Python 实现方式 |
|---|---|
| `ee.Geometry.Rectangle.coordinates` | 获取坐标 |
| `ee.Geometry.coordinates` | 获取坐标 |

### 图像处理
| GEE API | Python 实现方式 |
|---|---|
| `ee.Image.argmax` | 最大值索引 |
| `ee.Image.argmin` | 最小值索引 |
| `ee.Image.arrayGet` | 数组取值 |
| `ee.Image.arraySlice` | 数组切片 |
| `ee.Image.arraySort` | 数组排序 |
| `ee.Image.connectedPixelCount` | 连通像素计数 |
| `ee.Image.exp` | 指数运算 |
| `ee.Image.expression` | 表达式计算 |
| `ee.Image.getRegion` | 获取区域 |
| `ee.Image.matrixMultiply` | 矩阵乘法 |
| `ee.Image.qualityMosaic` | 质量镶嵌 |
| `ee.Image.random` | 随机数生成 |
| `ee.Image.reduce` | 图像归约 |
| `ee.Image.reduceConnectedComponents` | 连通分量归约 |
| `ee.Image.reduceNeighborhood` | 邻域归约 |
| `ee.Image.rgbToGrayscale` | RGB 转灰度 |
| `ee.Image.setMulti` | 多值设置 |
| `ee.Image.toBands` | 转为波段 |
| `ee.Image.unitScale` | 单位缩放 |

### 集合归约
| GEE API | Python 实现方式 |
|---|---|
| `ee.ImageCollection.count` | 计数 |
| `ee.ImageCollection.iterate` | 迭代 |
| `ee.ImageCollection.max` | 最大值 |
| `ee.ImageCollection.mean` | 均值 |
| `ee.ImageCollection.median` | 中位数 |
| `ee.ImageCollection.min` | 最小值 |
| `ee.ImageCollection.qualityMosaic` | 质量镶嵌 |
| `ee.ImageCollection.reduce` | 归约 |
| `ee.ImageCollection.sort` | 排序 |
| `ee.ImageCollection.toBands` | 转波段 |
| `ee.ImageCollection.toList` | 转列表 |

### 连接操作
| GEE API | Python 实现方式 |
|---|---|
| `ee.Join` | 创建连接 |
| `ee.Join.apply` | 应用连接 |
| `ee.Join.saveAll` | 保存所有匹配 |
| `ee.Join.saveFirst` | 保存首个匹配 |

### Reducer 操作
| GEE API | Python 实现方式 |
|---|---|
| `ee.Reducer` | 创建归约器 |
| `ee.Reducer.centeredVariance` | 中心方差 |
| `ee.Reducer.composite` | 合成 |
| `ee.Reducer.count` | 计数 |
| `ee.Reducer.covariance` | 协方差 |
| `ee.Reducer.frequencyHistogram` | 频率直方图 |
| `ee.Reducer.histogram` | 直方图 |
| `ee.Reducer.mean` | 均值 |
| `ee.Reducer.median` | 中位数 |
| `ee.Reducer.minMax` | 最小最大值 |
| `ee.Reducer.mode` | 众数 |
| `ee.Reducer.percentile` | 百分位数 |
| `ee.Reducer.range` | 极差 |
| `ee.Reducer.stdDev` | 标准差 |
| `ee.Reducer.toList` | 转列表 |
| `ee.Reducer.variance` | 方差 |

### 地形分析
| GEE API | Python 实现方式 |
|---|---|
| `ee.Terrain.products` | 坡度/坡向/山体阴影 |

### 导出
| GEE API | Python 实现方式 |
|---|---|
| `ee.batch.Export.table.toCloudStorage` | 导出到云存储 |

---

## 🔵 可 OGE 或 Python 实现的 API（13 个）

这些 API 既有可能找到 OGE 对应实现，也可以用 Python 实现：

| GEE API | OGE 候选 | Python 实现方式 |
|---|---|---|
| `ui.Map` | `FeatureCollection.map` | 创建地图 |
| `ui.Map.add` | `Coverage.add` | 添加元素 |
| `ui.Panel.add` | `Coverage.add` | 添加元素 |
| `ui.Select` | `Feature.select` | 选择 |
| `ee.FeatureCollection.filter` | `FeatureCollection.filter` | 过滤集合 |
| `ee.Image.cat` | `Coverage.cat` | 拼接图像 |
| `ee.Image.reduceRegion` | `Coverage.reduceRegion` | 区域归约 |
| `ee.ImageCollection.filter` | `FeatureCollection.filter` | 过滤影像集合 |
| `ee.ImageCollection.map` | `FeatureCollection.map` | 映射 |
| `ee.ImageCollection.merge` | `FeatureCollection.merge` | 合并 |
| `ee.ImageCollection.select` | `Feature.select` | 选择波段 |
| `ee.ImageCollection.size` | `FeatureCollection.size` | 获取大小 |
| `ee.Reducer.sum` | `CoverageCollection.sum` | 求和 |

---

## 🟡 可 OGE 映射的 API（5 个）

这些 API 可以直接映射到现有的 OGE API：

| GEE API | OGE API | 说明 |
|---|---|---|
| `ui.Date` | `Coverage.date` | 日期对象 |
| `ee.Image.geometry` | `Feature.geometry` | 获取几何 |
| `ee.Image.sampleRegions` | `Coverage.sampleRegions` | 区域采样 |
| `ee.Image.set` | `Feature.set` | 设置属性 |
| `ee.ImageCollection.toArray` | `Feature.toArray` | 转数组 |

---

## 🔴 待人工分析的 API（96 个）

这些 API 需要人工判断是否可以映射或实现：

### UI 组件类（约 40 个）
这些是 GEE 前端 UI 组件，OGE 可能没有对应实现：

- `Map.onClick`, `Map.setControlVisibility`
- `ui.Button`, `ui.Chart`, `ui.Chart.feature.*`, `ui.Chart.image.*`
- `ui.Chart.setChartType`, `ui.Chart.setOptions`, `ui.Chart.setSeriesColumns`
- `ui.Chart.setSeriesOptions`, `ui.Checkbox`, `ui.DatePicker`, `ui.DateSlider`
- `ui.Draw`, `ui.Dropdown`, `ui.Label`, `ui.Label.setStyle`, `ui.Label.setText`
- `ui.Layout`, `ui.Legend`, `ui.Map.Layer`, `ui.Map.centerObject`
- `ui.Map.layers`, `ui.Map.onClick`, `ui.Map.setCenter`, `ui.Map.setOptions`
- `ui.Panel`, `ui.Panel.Layout`, `ui.Panel.setLayout`, `ui.Panel.setStyle`
- `ui.Panel.setVisible`, `ui.RadioButtons`, `ui.Select.onChange`, `ui.Slider`
- `ui.Slider.onChange`, `ui.Table`, `ui.Textbox`, `ui.Thumbnail`

### 批处理/导出类（约 8 个）
- `Export.video.toDrive`
- `ee.batch.Export.table.toAsset`
- `ee.batch.Export.table.toDrive`
- `ee.batch.Task`, `ee.batch.Task.start`

### 算法类（约 8 个）
- `ee.Algorithms.If`
- `ee.Algorithms.Image.Segmentation.SNIC`
- `ee.Algorithms.Terrain`
- `ee.Classifier`, `ee.Classifier.confusionMatrix`
- `ee.ConfusionMatrix`, `ee.ConfusionMatrix.accuracy`, `ee.ConfusionMatrix.array`
- `ee.ConfusionMatrix.kappa`, `ee.ConfusionMatrix.producersAccuracy`

### 图像/分类类（约 10 个）
- `ee.FeatureCollection.classify`, `ee.FeatureCollection.draw`, `ee.FeatureCollection.first`
- `ee.Filter.inList`, `ee.Filter.stringStartsWith`
- `ee.Image.azimuth`, `ee.Image.bitwiseRightShift`, `ee.Image.bitwiseShiftRight`
- `ee.Image.cast`, `ee.Image.connectedComponents`, `ee.Image.constant`
- `ee.Image.gapfill`, `ee.Image.glcmTexture`, `ee.Image.interpolate`
- `ee.Image.pixelLonLat`, `ee.Image.selfMask`, `ee.Image.shiftLeft`
- `ee.Image.shiftRight`, `ee.Image.square`, `ee.Image.stratifiedSample`
- `ee.Image.where`

### 集合/Reducer 类（约 20 个）
- `ee.ImageCollection.first`, `ee.ImageCollection.last`
- `ee.Join.inner`, `ee.Kernel`
- `ee.Reducer.all`, `ee.Reducer.allNonZero`, `ee.Reducer.eigen`
- `ee.Reducer.first`, `ee.Reducer.firstNonNull`, `ee.Reducer.group`
- `ee.Reducer.linearFit`, `ee.Reducer.linearRegression`
- `require`, `ee.ui.Panel`

---

## ✅ 一对多/多对一关系分析

### 可 Python 实现的一对多关系

以下 GEE API 可以用不同的 Python 实现对应不同的功能：

| GEE API | 可能的 Python 实现 |
|---|---|
| `ui.Map` | 创建地图对象 / 地图配置 |
| `ui.Map.add` | 添加图层 / 添加控件 |
| `ui.Panel.add` | 添加子元素 / 添加布局 |
| `ui.Select` | 创建选择器 / 选择要素 |
| `ee.Filter.equals` | 数值等于 / 字符串等于 |
| `ee.Reducer.mean` | numpy.mean / statistics.mean |
| `ee.Reducer.histogram` | numpy.histogram / plt.hist |

### 多对一关系分析

多个 GEE API 可能映射到同一个 Python 实现：

| Python 实现 | 对应 GEE API |
|---|---|
| `numpy.mean()` | `ee.Reducer.mean`, `ee.ImageCollection.mean` |
| `numpy.median()` | `ee.Reducer.median`, `ee.ImageCollection.median` |
| `numpy.std()` | `ee.Reducer.stdDev` |
| `numpy.var()` | `ee.Reducer.variance`, `ee.Reducer.centeredVariance` |
| `numpy.histogram()` | `ee.Reducer.histogram`, `ui.Chart.image.histogram` |
| `skimage.filters.canny()` | `ee.Algorithms.CannyEdgeDetector` |

---

## 📝 建议实现优先级

### 高优先级（立即实现）
1. **分类器 API**：`ee.Classifier.*` 系列（用 scikit-learn 实现）
2. **Reducer API**：`ee.Reducer.*` 系列（用 numpy 实现）
3. **集合操作**：`ee.FeatureCollection.*` 系列（用 geopandas 实现）
4. **图像处理**：`ee.Image.*` 系列（用 rasterio/numpy 实现）

### 中优先级（规划实现）
1. **UI 组件**：`ui.*` 系列（OGE 可能有对应 UI 组件）
2. **批处理**：`Export.*`, `ee.batch.*`（用 Python 任务调度实现）
3. **连接操作**：`ee.Join.*`（用 pandas merge 实现）

### 低优先级（待需求确认）
1. **复杂算法**：`ee.Algorithms.*`（需要具体需求确认）
2. **纹理分析**：`ee.Image.glcmTexture`（需要具体需求确认）
3. **分类器评估**：`ee.ConfusionMatrix.*`（需要具体需求确认）

---

## 📁 相关文件

- 映射表：`gee_to_oge_matches.xlsx`
- GEE API 详情：`gee.json`
- OGE API 详情：`oge.json`
- Python 函数实现：`gee_python_functions.py`
- 未匹配分析数据：`unmatched_analysis.json`
- 映射审查报告：`GEE_OGE映射审查报告.md`

---

*报告生成完毕*