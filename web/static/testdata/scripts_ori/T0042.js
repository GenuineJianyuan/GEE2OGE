// 加载宜昌附近DEM数据（使用SRTM作为替代）
var dem = ee.Image('USGS/SRTMGL1_003')
  .clip(ee.Geometry.Point([111.5, 30.5]).buffer(50000));

// 定义无效值
var NaN_value = -9999;

// 小尺度：1像素半径均值滤波
var dem_small = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 中尺度：3像素半径均值滤波
var dem_medium = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(3)
});

// 大尺度：7像素半径均值滤波
var dem_large = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(7)
});

// 计算各尺度地形粗糙度指数（TRI）
var tri_small = ee.Terrain.roughness(dem_small);
var tri_medium = ee.Terrain.roughness(dem_medium);
var tri_large = ee.Terrain.roughness(dem_large);

// 定义各尺度分级规则
var small_rules = [
  [0.0, 8.0, 1.0],
  [8.0, 20.0, 2.0],
  [20.0, 5000.0, 3.0]
];

var medium_rules = [
  [0.0, 5.0, 1.0],
  [5.0, 12.0, 2.0],
  [12.0, 5000.0, 3.0]
];

var large_rules = [
  [0.0, 3.0, 1.0],
  [3.0, 8.0, 2.0],
  [8.0, 5000.0, 3.0]
];

// 各尺度粗糙度分级
var tri_small_class = tri_small.where(tri_small.gte(0).and(tri_small.lt(8)), 1)
  .where(tri_small.gte(8).and(tri_small.lt(20)), 2)
  .where(tri_small.gte(20), 3)
  .updateMask(tri_small.gt(0));

var tri_medium_class = tri_medium.where(tri_medium.gte(0).and(tri_medium.lt(5)), 1)
  .where(tri_medium.gte(5).and(tri_medium.lt(12)), 2)
  .where(tri_medium.gte(12), 3)
  .updateMask(tri_medium.gt(0));

var tri_large_class = tri_large.where(tri_large.gte(0).and(tri_large.lt(3)), 1)
  .where(tri_large.gte(3).and(tri_large.lt(8)), 2)
  .where(tri_large.gte(8), 3)
  .updateMask(tri_large.gt(0));

// 高粗糙度识别规则
var high_rules = [
  [-0.5, 2.5, 0.0],
  [2.5, 3.5, 1.0]
];

// 各尺度高粗糙度识别
var small_high = tri_small_class.eq(3).toInt();
var medium_high = tri_medium_class.eq(3).toInt();
var large_high = tri_large_class.eq(3).toInt();

// 高粗糙度计数
var high_count = small_high.add(medium_high).add(large_high);

// 粗糙度等级总和
var roughness_sum = tri_small_class.add(tri_medium_class).add(tri_large_class);

// 综合评分
var high_count_x10 = high_count.multiply(10);
var combined_score = high_count_x10.add(roughness_sum);

// 综合复杂度分级
var complexity = combined_score.where(combined_score.gte(0).and(combined_score.lt(4.5)), 1)
  .where(combined_score.gte(4.5).and(combined_score.lt(6.5)), 2)
  .where(combined_score.gte(14.5).and(combined_score.lt(19.5)), 2)
  .where(combined_score.gte(24.5).and(combined_score.lt(39.5)), 3)
  .updateMask(combined_score.gt(0));

// 平滑处理
var complexity_smooth = complexity.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var roughness_vis = {
  min: 1,
  max: 3,
  palette: ['#edf8fb', '#9ecae1', '#08519c']
};

var complexity_vis = {
  min: 1,
  max: 3,
  palette: ['#d9d9d9', '#fdae61', '#d73027']
};

// 添加图层到地图
Map.setCenter(111.5, 30.5, 10);
Map.addLayer(tri_small_class, roughness_vis, '小尺度粗糙度结果');
Map.addLayer(tri_medium_class, roughness_vis, '中尺度粗糙度结果');
Map.addLayer(tri_large_class, roughness_vis, '大尺度粗糙度结果');
Map.addLayer(complexity_smooth, complexity_vis, '综合复杂度等级结果');