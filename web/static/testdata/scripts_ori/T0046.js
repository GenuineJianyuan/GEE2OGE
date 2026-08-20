// 宜昌附近地形友好通行初筛 - GEE JavaScript 版本

// 加载 DEM 数据（使用 SRTM 30m 作为替代，因为 GEE 中没有 ALOS PALSAR 12.5m 直接数据）
var dem = ee.Image('USGS/SRTMGL1_003');

// 裁剪到宜昌附近区域
var geometry = ee.Geometry.Point([111.5, 30.5]).buffer(50000);
dem = dem.clip(geometry);

// 1. 坡度计算
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(3)
});

var slope = ee.Terrain.slope(dem_base);

// 坡度分级
var slope_class = slope
  .where(slope.lte(10), 1)
  .where(slope.gt(10).and(slope.lte(20)), 2)
  .where(slope.gt(20), 3);

// 2. 低位地形位置计算
var dem_local_mean = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(15)
});

var relative_position = dem_base.subtract(dem_local_mean);

var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 位置分级
var position_class = relative_position_smooth
  .where(relative_position_smooth.lte(-15), 1)
  .where(relative_position_smooth.gt(-15).and(relative_position_smooth.lte(-5)), 2)
  .where(relative_position_smooth.gt(-5), 3);

// 3. 局部起伏计算
var focal_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(9)
});

var focal_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(9)
});

var relief = focal_max.subtract(focal_min);

var relief_smooth = relief.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 起伏分级
var relief_class = relief_smooth
  .where(relief_smooth.lte(40), 1)
  .where(relief_smooth.gt(40).and(relief_smooth.lte(100)), 2)
  .where(relief_smooth.gt(100), 3);

// 4. 综合评分
var slope_weight = slope_class.multiply(2);
var relief_weight = relief_class.multiply(2);

var tmp_score = position_class.add(slope_weight);
var friendly_score = tmp_score.add(relief_weight);

// 友好通行带分级
var friendly_zone = friendly_score
  .where(friendly_score.gt(4.5).and(friendly_score.lte(6.5)), 1)
  .where(friendly_score.gt(6.5).and(friendly_score.lte(9.5)), 2)
  .where(friendly_score.gt(9.5), 3);

// 平滑处理
var friendly_zone_smooth = friendly_zone.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(2)
});

// 可视化参数
var slope_vis = {
  min: 1,
  max: 3,
  palette: ['#d9f0d3', '#fdae61', '#d73027']
};

var position_vis = {
  min: 1,
  max: 3,
  palette: ['#2b83ba', '#91bfdb', '#fdae61']
};

var relief_vis = {
  min: 1,
  max: 3,
  palette: ['#edf8fb', '#9ecae1', '#08519c']
};

var friendly_vis = {
  min: 1,
  max: 3,
  palette: ['#2ca25f', '#fdae61', '#d73027']
};

// 添加图层到地图
Map.setCenter(111.5, 30.5, 10);
Map.addLayer(slope_class, slope_vis, '坡度分级结果');
Map.addLayer(position_class, position_vis, '低位地形位置结果');
Map.addLayer(relief_class, relief_vis, '局部起伏分级结果');
Map.addLayer(friendly_zone_smooth, friendly_vis, '友好通行带初筛结果');