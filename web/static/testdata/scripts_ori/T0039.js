// 加载宜昌附近DEM数据（使用SRTM作为替代，因为GEE中没有ALOS_PALSAR_DEM12.5）
var dem = ee.Image('USGS/SRTMGL1_003').clip(ee.Geometry.Point([111.5, 30.5]).buffer(50000));

var NaN_value = -9999;

// 均值滤波平滑DEM
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(3)
});

// 计算坡度
var slope = ee.Terrain.slope(dem_base);

// 坡度分级
var slope_rules = [
  (0.0, 12.0, 1.0),
  (12.0, 90.0, 2.0)
];

var slope_class = slope.where(slope.lte(12), 1).where(slope.gt(12), 2);

// 计算局部起伏
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
var relief_class = relief_smooth.where(relief_smooth.lte(30), 1).where(relief_smooth.gt(30), 2);

// 计算相对高程位置
var dem_local_mean = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(15)
});

var relative_position = dem_base.subtract(dem_local_mean);

// 平滑相对高程位置
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 相对高程位置分级
var position_class = relative_position_smooth
  .where(relative_position_smooth.lte(-15), 1)
  .where(relative_position_smooth.gt(-15).and(relative_position_smooth.lte(-5)), 2)
  .where(relative_position_smooth.gt(-5).and(relative_position_smooth.lte(6)), 3)
  .where(relative_position_smooth.gt(6), 4);

// 组合编码
var slope_code = slope_class.multiply(100);
var relief_code = relief_class.multiply(10);
var tmp_code = slope_code.add(relief_code);
var combined_code = tmp_code.add(position_class);

// 地貌单元分类
var unit_rules = [
  (110.5, 111.5, 4.0),
  (111.5, 113.5, 3.0),
  (113.5, 114.5, 2.0),
  (114.5, 224.5, 1.0)
];

var landform_unit = combined_code
  .where(combined_code.gt(110.5).and(combined_code.lte(111.5)), 4)
  .where(combined_code.gt(111.5).and(combined_code.lte(113.5)), 3)
  .where(combined_code.gt(113.5).and(combined_code.lte(114.5)), 2)
  .where(combined_code.gt(114.5).and(combined_code.lte(224.5)), 1);

// 平滑地貌单元
var landform_unit_smooth = landform_unit.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var slope_vis = {
  min: 1,
  max: 2,
  palette: ['#d9f0d3', '#fdae61']
};

var relief_vis = {
  min: 1,
  max: 2,
  palette: ['#edf8fb', '#2c7fb8']
};

var unit_vis = {
  min: 1,
  max: 4,
  palette: ['#d9d9d9', '#d7191c', '#fdae61', '#2b83ba']
};

// 添加图层到地图
Map.addLayer(slope_class, slope_vis, '坡度候选分组结果');
Map.addLayer(relief_class, relief_vis, '局部起伏分组结果');
Map.addLayer(landform_unit_smooth, unit_vis, '关键平缓地貌单元识别结果');

// 设置地图中心
Map.setCenter(111.5, 30.5, 10);