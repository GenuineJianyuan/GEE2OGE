// 加载宜昌附近 DEM 数据（使用 SRTM 30m 作为替代）
var dem = ee.Image('USGS/SRTMGL1_003').clip(ee.Geometry.Point([111.5, 30.5]).buffer(50000));

// 定义无效值
var NaN_value = -9999;

// 计算基础 DEM（3像素圆形窗口均值平滑）
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(3, 'pixels')
});

// 计算局部均值（15像素圆形窗口）
var dem_local_mean = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(15, 'pixels')
});

// 计算相对高程位置
var relative_position = dem_base.subtract(dem_local_mean);

// 平滑相对高程位置（1像素圆形窗口）
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1, 'pixels')
});

// 计算坡度（使用 GEE 的 Terrain 模块）
var slope = ee.Terrain.slope(dem_base);

// 计算局部最大和最小高程
var focal_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(9, 'pixels')
});

var focal_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(9, 'pixels')
});

// 计算局部起伏
var relief = focal_max.subtract(focal_min);

// 平滑局部起伏（2像素圆形窗口）
var relief_smooth = relief.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2, 'pixels')
});

// 相对高程位置分级
var position_rules = [
  [-5000.0, -10.0, 1.0],
  [-10.0, -3.0, 2.0],
  [-3.0, 3.0, 3.0],
  [3.0, 10.0, 4.0],
  [10.0, 5000.0, 5.0]
];

var position_class = ee.Image(1).where(relative_position_smooth.lt(-10), 1)
  .where(relative_position_smooth.gte(-10).and(relative_position_smooth.lt(-3)), 2)
  .where(relative_position_smooth.gte(-3).and(relative_position_smooth.lt(3)), 3)
  .where(relative_position_smooth.gte(3).and(relative_position_smooth.lt(10)), 4)
  .where(relative_position_smooth.gte(10), 5)
  .updateMask(relative_position_smooth.gte(-5000).and(relative_position_smooth.lte(5000)));

// 坡度分级
var slope_rules = [
  [0.0, 15.0, 1.0],
  [15.0, 90.0, 2.0]
];

var slope_class = ee.Image(1).where(slope.lt(15), 1)
  .where(slope.gte(15), 2)
  .updateMask(slope.gte(0).and(slope.lte(90)));

// 局部起伏分级
var relief_rules = [
  [0.0, 40.0, 1.0],
  [40.0, 5000.0, 2.0]
];

var relief_class = ee.Image(1).where(relief_smooth.lt(40), 1)
  .where(relief_smooth.gte(40), 2)
  .updateMask(relief_smooth.gte(0).and(relief_smooth.lte(5000)));

// 组合编码
var position_code = position_class.multiply(100);
var slope_code = slope_class.multiply(10);
var tmp_code = position_code.add(slope_code);
var combined_code = tmp_code.add(relief_class);

// 结构分区规则
var structure_rules = [
  [110.5, 122.5, 1.0],
  [122.5, 221.5, 2.0],
  [221.5, 222.5, 1.0],
  [222.5, 421.5, 2.0],
  [421.5, 422.5, 3.0],
  [422.5, 510.5, 2.0],
  [510.5, 522.5, 3.0]
];

var structure_band = ee.Image(1).where(combined_code.gt(110.5).and(combined_code.lte(122.5)), 1)
  .where(combined_code.gt(122.5).and(combined_code.lte(221.5)), 2)
  .where(combined_code.gt(221.5).and(combined_code.lte(222.5)), 1)
  .where(combined_code.gt(222.5).and(combined_code.lte(421.5)), 2)
  .where(combined_code.gt(421.5).and(combined_code.lte(422.5)), 3)
  .where(combined_code.gt(422.5).and(combined_code.lte(510.5)), 2)
  .where(combined_code.gt(510.5).and(combined_code.lte(522.5)), 3)
  .updateMask(combined_code.gt(110.5).and(combined_code.lte(522.5)));

// 平滑结构分区（使用众数滤波）
var structure_band_smooth = structure_band.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1, 'pixels')
});

// 可视化参数
var position_vis = {
  min: 1,
  max: 5,
  palette: ['#2b83ba', '#91bfdb', '#ffffbf', '#fdae61', '#d7191c']
};

var slope_vis = {
  min: 1,
  max: 2,
  palette: ['#d9f0d3', '#f46d43']
};

var structure_vis = {
  min: 1,
  max: 3,
  palette: ['#2b83ba', '#fdae61', '#d7191c']
};

// 添加图层到地图
Map.addLayer(position_class, position_vis, '相对高程位置分层结果');
Map.addLayer(slope_class, slope_vis, '坡度分组结果');
Map.addLayer(structure_band_smooth, structure_vis, '山脊-谷地-侧坡结构分区结果');

// 设置地图中心
Map.setCenter(111.5, 30.5, 10);