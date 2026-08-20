// 加载ASTER GDEM数据
var dem = ee.Image('NASA/ASTER_GED/AG100_V003');

// 定义无效值
var NaN_value = -9999;

// 对DEM进行均值滤波平滑
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 计算坡度
var slope = ee.Terrain.slope(dem_base);

// 坡度分级规则
var slope_rules = [
  (0.0, 12.0, 1.0),
  (12.0, 22.0, 2.0),
  (22.0, 35.0, 3.0),
  (35.0, 90.0, 4.0)
];

// 坡度分级
var slope_class = slope.remap([0, 12, 22, 35], [1, 2, 3, 4], NaN_value);

// 计算局部最大最小值
var focal_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(5)
});

var focal_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(5)
});

// 计算局部起伏
var relief = focal_max.subtract(focal_min);

// 平滑起伏
var relief_smooth = relief.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 起伏分级规则
var relief_rules = [
  (0.0, 120.0, 1.0),
  (120.0, 250.0, 2.0),
  (250.0, 400.0, 3.0),
  (400.0, 5000.0, 4.0)
];

// 起伏分级
var relief_class = relief_smooth.remap([0, 120, 250, 400], [1, 2, 3, 4], NaN_value);

// 进一步平滑DEM
var tri_base = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 计算地形粗糙度指数
var tri = ee.Terrain.roughness(tri_base);

// TRI分级规则
var tri_rules = [
  (0.0, 6.0, 1.0),
  (6.0, 14.0, 2.0),
  (14.0, 24.0, 3.0),
  (24.0, 5000.0, 4.0)
];

// TRI分级
var tri_class = tri.remap([0, 6, 14, 24], [1, 2, 3, 4], NaN_value);

// 计算局部平均高程
var dem_local_mean = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(15)
});

// 计算相对地形位置
var relative_position = dem_base.subtract(dem_local_mean);

// 平滑相对位置
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 位置分级规则
var position_rules = [
  (-5000.0, -25.0, 4.0),
  (-25.0, -8.0, 3.0),
  (-8.0, 8.0, 2.0),
  (8.0, 5000.0, 1.0)
];

// 位置分级
var position_class = relative_position_smooth.remap([-5000, -25, -8, 8], [4, 3, 2, 1], NaN_value);

// 加权计算
var slope_weight = slope_class.multiply(3);
var relief_weight = relief_class.multiply(2);

// 计算综合得分
var tmp_score_1 = slope_weight.add(relief_weight);
var tmp_score_2 = tri_class.add(position_class);
var combined_score = tmp_score_1.add(tmp_score_2);

// 避让等级规则
var avoid_rules = [
  (6.5, 12.5, 1.0),
  (12.5, 17.5, 2.0),
  (17.5, 22.5, 3.0),
  (22.5, 28.5, 4.0)
];

// 避让等级分类
var avoid_zone = combined_score.remap([6.5, 12.5, 17.5, 22.5], [1, 2, 3, 4], NaN_value);

// 平滑避让等级
var avoid_zone_smooth = avoid_zone.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var slope_vis = {
  min: 1,
  max: 4,
  palette: ['#d9f0d3', '#fee08b', '#f46d43', '#a50026']
};

var relief_vis = {
  min: 1,
  max: 4,
  palette: ['#edf8fb', '#9ecae1', '#3182bd', '#08306b']
};

var avoid_vis = {
  min: 1,
  max: 4,
  palette: ['#2ca25f', '#fdae61', '#d73027', '#7f0000']
};

// 添加图层到地图
Map.addLayer(slope_class, slope_vis, '坡度不利等级结果');
Map.addLayer(relief_class, relief_vis, '起伏不利等级结果');
Map.addLayer(avoid_zone_smooth, avoid_vis, '建设不利区与避让等级初评结果');

// 设置地图中心
Map.setCenter(115.5, 30.5, 10);