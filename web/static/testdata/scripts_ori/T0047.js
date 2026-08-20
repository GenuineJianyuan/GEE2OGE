// 加载宜昌附近DEM数据（使用SRTM作为替代，因为GEE中没有ALOS_PALSAR_DEM12.5）
var dem = ee.Image('USGS/SRTMGL1_003').clip(ee.Geometry.Point([111.5, 30.5]).buffer(50000));

// 计算基础DEM（3像素圆形邻域均值）
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(3)
});

// 计算局部均值（15像素圆形邻域均值）
var dem_local_mean = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(15)
});

// 计算相对高程位置
var relative_position = dem_base.subtract(dem_local_mean);

// 平滑相对高程位置
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 相对高程位置分级
var position_class = relative_position_smooth.expression(
  "b(0) < 0 ? 3 : (b(0) < 12 ? 2 : 1)"
).rename('position_class');

// 计算坡度
var slope = ee.Terrain.slope(dem_base);

// 坡度分级
var slope_class = slope.expression(
  "b(0) < 12 ? 1 : (b(0) < 22 ? 2 : 3)"
).rename('slope_class');

// 计算局部起伏（9像素圆形邻域最大最小值差）
var focal_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(9)
});

var focal_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(9)
});

var relief = focal_max.subtract(focal_min);

// 平滑局部起伏
var relief_smooth = relief.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 局部起伏分级
var relief_class = relief_smooth.expression(
  "b(0) < 35 ? 1 : (b(0) < 80 ? 2 : 3)"
).rename('relief_class');

// 计算地形粗糙度指数（TRI）
var tri_base = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

var tri = ee.Terrain.roughness(tri_base);

// TRI分级
var tri_class = tri.expression(
  "b(0) < 8 ? 1 : (b(0) < 18 ? 2 : 3)"
).rename('tri_class');

// 加权计算综合得分
var position_weight = position_class.multiply(2);
var slope_weight = slope_class.multiply(2);
var tmp_score_1 = position_weight.add(slope_weight);
var tmp_score_2 = relief_class.add(tri_class);
var observe_score = tmp_score_1.add(tmp_score_2);

// 观察点候选区分级
var observe_zone = observe_score.expression(
  "b(0) < 7.5 ? 1 : (b(0) < 10.5 ? 2 : 3)"
).rename('observe_zone');

// 平滑观察点候选区
var observe_zone_smooth = observe_zone.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var position_vis = {
  min: 1,
  max: 3,
  palette: ['#d73027', '#fdae61', '#91bfdb']
};

var slope_vis = {
  min: 1,
  max: 3,
  palette: ['#d9f0d3', '#fdae61', '#d73027']
};

var observe_vis = {
  min: 1,
  max: 3,
  palette: ['#2ca25f', '#fdae61', '#d73027']
};

// 添加图层到地图
Map.addLayer(position_class, position_vis, '高位位置分级结果');
Map.addLayer(slope_class, slope_vis, '坡度约束等级结果');
Map.addLayer(observe_zone_smooth, observe_vis, '观察点候选区初筛结果');

// 设置地图中心
Map.setCenter(111.5, 30.5, 10);