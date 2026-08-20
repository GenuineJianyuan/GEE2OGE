// 加载 DEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_V003');

// 定义无效值
var NaN_value = -9999;

// 对 DEM 进行均值滤波平滑
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 计算坡度
var slope = ee.Terrain.slope(dem_base);

// 坡度分级规则
var slope_rules = [
  [0.0, 8.0, 1.0],
  [8.0, 18.0, 2.0],
  [18.0, 90.0, 3.0]
];

// 坡度分级
var slope_class = ee.Image(1).where(slope.gt(8).and(slope.lte(18)), 2)
  .where(slope.gt(18), 3)
  .where(slope.lte(0), NaN_value);

// 计算局部最大和最小高程
var focal_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(9)
});

var focal_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(9)
});

// 计算局部起伏
var relief = focal_max.subtract(focal_min);

// 对起伏进行平滑
var relief_smooth = relief.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 起伏分级规则
var relief_rules = [
  [0.0, 40.0, 1.0],
  [40.0, 100.0, 2.0],
  [100.0, 5000.0, 3.0]
];

// 起伏分级
var relief_class = ee.Image(1).where(relief_smooth.gt(40).and(relief_smooth.lte(100)), 2)
  .where(relief_smooth.gt(100), 3)
  .where(relief_smooth.lte(0), NaN_value);

// 对 DEM 进行进一步平滑用于 TRI 计算
var dem_tri = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 计算地形粗糙度指数 (TRI)
var tri = ee.Algorithms.Terrain.tri(dem_tri);

// TRI 分级规则
var tri_rules = [
  [0.0, 5.0, 1.0],
  [5.0, 12.0, 2.0],
  [12.0, 5000.0, 3.0]
];

// TRI 分级
var tri_class = ee.Image(1).where(tri.gt(5).and(tri.lte(12)), 2)
  .where(tri.gt(12), 3)
  .where(tri.lte(0), NaN_value);

// 计算综合约束得分
var tmp_score = slope_class.add(relief_class);
var constraint_score = tmp_score.add(tri_class);

// 候选区分类规则
var candidate_rules = [
  [2.5, 4.5, 1.0],
  [4.5, 6.5, 2.0],
  [6.5, 9.5, 3.0]
];

// 候选区分类
var candidate_zone = ee.Image(1).where(constraint_score.gt(4.5).and(constraint_score.lte(6.5)), 2)
  .where(constraint_score.gt(6.5), 3)
  .where(constraint_score.lte(2.5), NaN_value);

// 对候选区进行众数滤波平滑
var candidate_zone_smooth = candidate_zone.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var slope_vis = {
  min: 1,
  max: 3,
  palette: ['#d9f0d3', '#fdae61', '#d73027']
};

var relief_vis = {
  min: 1,
  max: 3,
  palette: ['#edf8fb', '#9ecae1', '#08519c']
};

var candidate_vis = {
  min: 1,
  max: 3,
  palette: ['#2ca25f', '#fdae61', '#d73027']
};

// 添加图层到地图
Map.addLayer(slope_class, slope_vis, '坡度约束等级结果');
Map.addLayer(relief_class, relief_vis, '起伏约束等级结果');
Map.addLayer(candidate_zone_smooth, candidate_vis, '基础候选区初筛结果');

// 设置地图中心
Map.setCenter(115.5, 30.5, 10);