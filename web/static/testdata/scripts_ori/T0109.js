// 加载矢量数据
var feature = ee.FeatureCollection('users/your_username/EasternChina_PopulationAging_Vector');

// 添加图层到地图
Map.addLayer(feature, {color: '#000000'}, 'Aging');
Map.setCenter(115, 31, 4);

// 注意：GEE 中没有直接对应的地理探测器（GeoDetector）算法
// 需要手动实现或使用其他统计方法
// 以下为替代方案示例：

// 1. 提取属性数据
var attributes = feature.select(['aging', 'PCGDP', 'GI', 'FD', 'education']);

// 2. 计算各变量的统计信息（示例：计算均值）
var stats = attributes.reduceColumns({
  reducer: ee.Reducer.mean(),
  selectors: ['aging', 'PCGDP', 'GI', 'FD', 'education']
});

// 3. 输出统计结果到控制台
print('变量统计信息:', stats);

// 4. 如果需要空间异质性分析，可以使用空间自相关或其他方法
// 例如计算莫兰指数（Moran's I）等

// 注意：地理探测器（GeoDetector）算法需要手动实现
// 包括因子探测器、交互作用探测器、风险区探测器和生态探测器