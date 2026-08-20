// 加载宜昌附近 DEM 数据（使用 SRTM 作为替代，因为 GEE 中没有 ALOS_PALSAR_DEM12.5）
var dem = ee.Image('USGS/SRTMGL1_003');

var NaN_value = -9999;

// 计算基础 DEM 的局部均值（3x3 窗口）
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(3)
});

// 计算局部均值（15x15 窗口）
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

// 计算坡度
var slope = ee.Terrain.slope(dem_base);

// 相对高程位置分级规则
var position_rules = [
  [-5000.0, -15.0, 1.0],
  [-15.0, -5.0, 2.0],
  [-5.0, 5.0, 3.0],
  [5.0, 15.0, 4.0],
  [15.0, 5000.0, 5.0]
];

// 相对高程位置分级
var position_class = relative_position_smooth.remap(
  position_rules.map(function(r) { return r[0]; }),
  position_rules.map(function(r) { return r[1]; }),
  position_rules.map(function(r) { return r[2]; }),
  NaN_value
);

// 坡度分级规则
var slope_rules = [
  [0.0, 20.0, 1.0],
  [20.0, 35.0, 2.0],
  [35.0, 90.0, 3.0]
];

// 坡度分级
var slope_class = slope.remap(
  slope_rules.map(function(r) { return r[0]; }),
  slope_rules.map(function(r) { return r[1]; }),
  slope_rules.map(function(r) { return r[2]; }),
  NaN_value
);

// 组合编码
var position_code = position_class.multiply(10);
var combined_class = position_code.add(slope_class);

// 坡位层级分带规则
var slope_position_rules = [
  [10.5, 11.5, 1.0],
  [11.5, 13.5, 2.0],
  [20.5, 23.5, 2.0],
  [30.5, 33.5, 3.0],
  [40.5, 43.5, 4.0],
  [50.5, 52.5, 5.0],
  [52.5, 53.5, 4.0]
];

// 坡位层级分带
var slope_position = combined_class.remap(
  slope_position_rules.map(function(r) { return r[0]; }),
  slope_position_rules.map(function(r) { return r[1]; }),
  slope_position_rules.map(function(r) { return r[2]; }),
  NaN_value
);

// 平滑坡位结果
var slope_position_smooth = slope_position.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var position_vis = {
  min: 1,
  max: 5,
  palette: ['#2b83ba', '#91bfdb', '#ffffbf', '#fdae61', '#d7191c']
};

var slope_vis = {
  min: 1,
  max: 3,
  palette: ['#fee08b', '#f46d43', '#a50026']
};

var slope_position_vis = {
  min: 1,
  max: 5,
  palette: ['#2b83ba', '#91bfdb', '#ffffbf', '#fdae61', '#d7191c']
};

// 添加图层到地图
Map.addLayer(position_class, position_vis, '相对高程位置分层结果');
Map.addLayer(slope_class, slope_vis, '坡度分级结果');
Map.addLayer(slope_position_smooth, slope_position_vis, '坡位层级分带结果');

// 设置地图中心
Map.setCenter(111.5, 30.5, 10);