// 加载宜昌附近DEM数据（使用SRTM作为替代，因为GEE中没有ALOS_PALSAR_DEM12.5）
var dem = ee.Image('USGS/SRTMGL1_003').clip(ee.Geometry.Point([111.5, 30.5]).buffer(50000));

// 定义无效值
var NaN_value = -9999;

// 基础平滑（半径2像元）
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 小尺度平滑（半径1像元）
var dem_small = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 计算小尺度地形崎岖度指数（TRI）
var tri_small = ee.Terrain.roughness(dem_small);

// 计算区域最大高程（半径11像元）
var focal_max = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(11)
});

// 计算区域最小高程（半径11像元）
var focal_min = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(11)
});

// 计算区域起伏度
var regional_relief = focal_max.subtract(focal_min);

// 区域起伏度平滑（半径2像元）
var regional_relief_smooth = regional_relief.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 定义TRI分级规则
var tri_rules = [
  {from: 0.0, to: 8.0, value: 1.0},
  {from: 8.0, to: 20.0, value: 2.0},
  {from: 20.0, to: 5000.0, value: 3.0}
];

// 定义起伏度分级规则
var relief_rules = [
  {from: 0.0, to: 60.0, value: 1.0},
  {from: 60.0, to: 150.0, value: 2.0},
  {from: 150.0, to: 5000.0, value: 3.0}
];

// TRI分级
var tri_class = tri_small.remap(
  tri_rules.map(function(r) { return r.from; }),
  tri_rules.map(function(r) { return r.to; }),
  tri_rules.map(function(r) { return r.value; }),
  NaN_value
);

// 起伏度分级
var relief_class = regional_relief_smooth.remap(
  relief_rules.map(function(r) { return r.from; }),
  relief_rules.map(function(r) { return r.to; }),
  relief_rules.map(function(r) { return r.value; }),
  NaN_value
);

// 定义高值提取规则
var high_rules = [
  {from: -0.5, to: 2.5, value: 0.0},
  {from: 2.5, to: 3.5, value: 1.0}
];

// 提取高TRI区域
var broken_high = tri_class.remap(
  high_rules.map(function(r) { return r.from; }),
  high_rules.map(function(r) { return r.to; }),
  high_rules.map(function(r) { return r.value; }),
  NaN_value
);

// 提取高起伏区域
var relief_high = relief_class.remap(
  high_rules.map(function(r) { return r.from; }),
  high_rules.map(function(r) { return r.to; }),
  high_rules.map(function(r) { return r.value; }),
  NaN_value
);

// 破碎度编码（乘以10）
var broken_code = broken_high.multiply(10);

// 组合编码
var combined_code = broken_code.add(relief_high);

// 定义地形类型规则
var type_rules = [
  {from: -0.5, to: 0.5, value: 1.0},
  {from: 0.5, to: 1.5, value: 3.0},
  {from: 9.5, to: 10.5, value: 2.0},
  {from: 10.5, to: 11.5, value: 4.0}
];

// 地形类型分类
var terrain_type = combined_code.remap(
  type_rules.map(function(r) { return r.from; }),
  type_rules.map(function(r) { return r.to; }),
  type_rules.map(function(r) { return r.value; }),
  NaN_value
);

// 地形类型平滑（众数滤波）
var terrain_type_smooth = terrain_type.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var tri_vis = {
  min: 1,
  max: 3,
  palette: ['#edf8fb', '#9ecae1', '#08519c']
};

var relief_vis = {
  min: 1,
  max: 3,
  palette: ['#fff7bc', '#fdae61', '#d73027']
};

var type_vis = {
  min: 1,
  max: 4,
  palette: ['#d9d9d9', '#2b83ba', '#fdae61', '#d7191c']
};

// 添加图层到地图
Map.addLayer(tri_class, tri_vis, '细尺度破碎度结果');
Map.addLayer(relief_class, relief_vis, '中大尺度起伏结果');
Map.addLayer(terrain_type_smooth, type_vis, '局部破碎—区域起伏分离识别结果');

// 设置地图中心
Map.setCenter(111.5, 30.5, 10);