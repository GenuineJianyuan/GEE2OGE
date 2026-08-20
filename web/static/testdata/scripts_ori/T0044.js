// 加载 DEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_V003');

// 使用 focalMean 平滑 DEM
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 小尺度（半径 2）地形起伏计算
var small_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(2)
});
var small_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(2)
});
var small_relief = small_max.subtract(small_min);

// 中尺度（半径 5）地形起伏计算
var medium_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(5)
});
var medium_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(5)
});
var medium_relief = medium_max.subtract(medium_min);

// 大尺度（半径 9）地形起伏计算
var large_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(9)
});
var large_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(9)
});
var large_relief = large_max.subtract(large_min);

// 小尺度分级规则
var small_rules = [
  [0.0, 10.0, 1.0],
  [10.0, 25.0, 2.0],
  [25.0, 5000.0, 3.0]
];

// 中尺度分级规则
var medium_rules = [
  [0.0, 30.0, 1.0],
  [30.0, 80.0, 2.0],
  [80.0, 5000.0, 3.0]
];

// 大尺度分级规则
var large_rules = [
  [0.0, 80.0, 1.0],
  [80.0, 180.0, 2.0],
  [180.0, 5000.0, 3.0]
];

// 应用分级规则
var small_class = small_relief.remap(
  [0, 10, 25],
  [1, 2, 3],
  0
);
var medium_class = medium_relief.remap(
  [0, 30, 80],
  [1, 2, 3],
  0
);
var large_class = large_relief.remap(
  [0, 80, 180],
  [1, 2, 3],
  0
);

// 组合编码：小尺度×100 + 中尺度×10 + 大尺度
var small_code = small_class.multiply(100);
var medium_code = medium_class.multiply(10);
var tmp_code = small_code.add(medium_code);
var combined_code = tmp_code.add(large_class);

// 一致性规则定义
var consistency_rules = [
  [110.5, 111.5, 1.0],
  [111.5, 112.5, 1.0],
  [120.5, 121.5, 1.0],
  [210.5, 211.5, 1.0],
  [121.5, 122.5, 2.0],
  [211.5, 212.5, 2.0],
  [220.5, 221.5, 2.0],
  [221.5, 222.5, 2.0],
  [222.5, 223.5, 2.0],
  [231.5, 232.5, 2.0],
  [321.5, 322.5, 2.0],
  [232.5, 233.5, 3.0],
  [322.5, 323.5, 3.0],
  [331.5, 332.5, 3.0],
  [332.5, 333.5, 3.0],
  [112.5, 113.5, 4.0],
  [122.5, 123.5, 4.0],
  [130.5, 131.5, 4.0],
  [131.5, 132.5, 4.0],
  [132.5, 133.5, 4.0],
  [212.5, 213.5, 4.0],
  [230.5, 231.5, 4.0],
  [310.5, 311.5, 4.0],
  [311.5, 312.5, 4.0],
  [312.5, 313.5, 4.0],
  [320.5, 321.5, 4.0],
  [330.5, 331.5, 4.0]
];

// 应用一致性规则
var consistency = combined_code.remap(
  consistency_rules.map(function(r) { return r[0]; }),
  consistency_rules.map(function(r) { return r[2]; }),
  0
);

// 可视化参数
var relief_vis = {
  min: 1,
  max: 3,
  palette: ['#edf8fb', '#9ecae1', '#08519c']
};

var consistency_vis = {
  min: 1,
  max: 4,
  palette: ['#91bfdb', '#ffffbf', '#d73027', '#fdae61']
};

// 添加图层到地图
Map.addLayer(small_class, relief_vis, '小尺度起伏等级结果');
Map.addLayer(medium_class, relief_vis, '中尺度起伏等级结果');
Map.addLayer(large_class, relief_vis, '大尺度起伏等级结果');
Map.addLayer(consistency, consistency_vis, '地形结构稳定带与尺度分歧带');

// 设置地图中心
Map.setCenter(111.5, 32.5, 11);