// 加载宜昌附近相邻 DEM 数据
var dem1 = ee.Image('JAXA/ALOS/AW3D30_V1_1');
var dem2 = ee.Image('JAXA/ALOS/AW3D30_V1_1');

// 合并两个 DEM 影像
var dem_collection = ee.ImageCollection([dem1, dem2]);
var dem_mosaic = dem_collection.mosaic();

// 计算局部起伏度（焦点最大值 - 焦点最小值）
var focal_max = dem_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(9, 'meters')
});

var focal_min = dem_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(9, 'meters')
});

var local_relief = focal_max.subtract(focal_min);

// 计算地形粗糙度指数（TRI）
var tri = ee.Terrain.roughness(dem_mosaic);

// 对局部起伏度进行分级
var relief_rules = [
  {from: 0.0, to: 40.0, value: 1.0},
  {from: 40.0, to: 120.0, value: 2.0},
  {from: 120.0, to: 5000.0, value: 3.0}
];

var relief_class = ee.Image(1).where(local_relief.gt(0).and(local_relief.lte(40)), 1)
  .where(local_relief.gt(40).and(local_relief.lte(120)), 2)
  .where(local_relief.gt(120), 3);

// 对 TRI 进行分级
var tri_rules = [
  {from: 0.0, to: 5.0, value: 1.0},
  {from: 5.0, to: 20.0, value: 2.0},
  {from: 20.0, to: 2000.0, value: 3.0}
];

var tri_class = ee.Image(1).where(tri.gt(0).and(tri.lte(5)), 1)
  .where(tri.gt(5).and(tri.lte(20)), 2)
  .where(tri.gt(20), 3);

// 组合分级结果
var relief_code = relief_class.multiply(10);
var combined_class = relief_code.add(tri_class);

// 定义地形复杂度分级规则
var complexity_rules = [
  {from: 10.5, to: 11.5, value: 1.0},  // 低复杂度
  {from: 11.5, to: 13.5, value: 2.0},  // 中复杂度
  {from: 20.5, to: 22.5, value: 2.0},  // 中复杂度
  {from: 30.5, to: 31.5, value: 2.0},  // 中复杂度
  {from: 22.5, to: 23.5, value: 3.0},  // 高复杂度
  {from: 31.5, to: 33.5, value: 3.0}   // 高复杂度
];

// 应用复杂度分级
var complexity = ee.Image(1).where(combined_class.gt(10.5).and(combined_class.lte(11.5)), 1)
  .where(combined_class.gt(11.5).and(combined_class.lte(13.5)), 2)
  .where(combined_class.gt(20.5).and(combined_class.lte(22.5)), 2)
  .where(combined_class.gt(30.5).and(combined_class.lte(31.5)), 2)
  .where(combined_class.gt(22.5).and(combined_class.lte(23.5)), 3)
  .where(combined_class.gt(31.5).and(combined_class.lte(33.5)), 3);

// 平滑处理（焦点众数）
var complexity_smooth = complexity.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1, 'meters')
});

// 可视化参数
var relief_vis = {
  min: 1,
  max: 3,
  palette: ['#d9f0d3', '#fdae61', '#d73027']
};

var tri_vis = {
  min: 1,
  max: 3,
  palette: ['#edf8fb', '#b2e2e2', '#2c7fb8']
};

var complexity_vis = {
  min: 1,
  max: 3,
  palette: ['#d9f0d3', '#fdae61', '#d73027']
};

// 添加图层到地图
Map.addLayer(relief_class, relief_vis, '起伏度等级结果');
Map.addLayer(tri_class, tri_vis, '粗糙度等级结果');
Map.addLayer(complexity_smooth, complexity_vis, '地形复杂度等级图');

// 设置地图中心
Map.setCenter(111.0, 30.5, 9);