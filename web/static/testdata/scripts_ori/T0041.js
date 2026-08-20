// 加载 DEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_V003');

// 使用 focalMean 平滑 DEM
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 小尺度（半径2）局部起伏
var small_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(2)
});
var small_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(2)
});
var small_relief = small_max.subtract(small_min);

// 中尺度（半径5）局部起伏
var medium_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(5)
});
var medium_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(5)
});
var medium_relief = medium_max.subtract(medium_min);

// 大尺度（半径9）局部起伏
var large_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(9)
});
var large_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(9)
});
var large_relief = large_max.subtract(large_min);

// 分级规则
var small_rules = [
  {from: 0.0, to: 10.0, value: 1.0},
  {from: 10.0, to: 25.0, value: 2.0},
  {from: 25.0, to: 5000.0, value: 3.0}
];

var medium_rules = [
  {from: 0.0, to: 30.0, value: 1.0},
  {from: 30.0, to: 80.0, value: 2.0},
  {from: 80.0, to: 5000.0, value: 3.0}
];

var large_rules = [
  {from: 0.0, to: 80.0, value: 1.0},
  {from: 80.0, to: 180.0, value: 2.0},
  {from: 180.0, to: 5000.0, value: 3.0}
];

// 重分类函数
function reclassify(image, rules) {
  var classified = ee.Image(1);
  rules.forEach(function(rule) {
    classified = classified.where(
      image.gte(rule.from).and(image.lt(rule.to)),
      rule.value
    );
  });
  return classified;
}

// 各尺度分级
var small_class = reclassify(small_relief, small_rules);
var medium_class = reclassify(medium_relief, medium_rules);
var large_class = reclassify(large_relief, large_rules);

// 提取高起伏区域（等级3）
var high_rules = [
  {from: -0.5, to: 2.5, value: 0.0},
  {from: 2.5, to: 3.5, value: 1.0}
];

var small_high = reclassify(small_class, high_rules);
var medium_high = reclassify(medium_class, high_rules);
var large_high = reclassify(large_class, high_rules);

// 计算高起伏区域叠加次数
var high_count = small_high.add(medium_high).add(large_high);

// 稳定性分级
var stability_rules = [
  {from: -0.5, to: 0.5, value: 1.0},
  {from: 0.5, to: 1.5, value: 2.0},
  {from: 1.5, to: 3.5, value: 3.0}
];

var stability = reclassify(high_count, stability_rules);

// 平滑稳定性结果
var stability_smooth = stability.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var relief_vis = {
  min: 1,
  max: 3,
  palette: ['#edf8fb', '#9ecae1', '#08519c']
};

var stability_vis = {
  min: 1,
  max: 3,
  palette: ['#d9d9d9', '#fdae61', '#d73027']
};

// 添加图层
Map.addLayer(small_class, relief_vis, '小尺度起伏结果');
Map.addLayer(medium_class, relief_vis, '中尺度起伏结果');
Map.addLayer(large_class, relief_vis, '大尺度起伏结果');
Map.addLayer(stability_smooth, stability_vis, '稳定高起伏区与尺度敏感区');

// 设置地图中心
Map.setCenter(109.5, 32.5, 11);