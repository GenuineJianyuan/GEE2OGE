// 加载 DEM 数据（武汉附近相邻两景）
var dem1 = ee.Image('NASA/ASTER_GED/AG100_V003');
var dem2 = ee.Image('NASA/ASTER_GED/AG100_V003');

// 合并两个 DEM 影像（使用 mosaic 拼接）
var dem_mosaic = ee.ImageCollection([dem1, dem2]).mosaic();

// 定义无效值
var NaN_value = -9999;

// 计算局部均值（9像素圆形邻域）
var dem_local_mean = dem_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(9)
});

// 计算相对位置（DEM 减去局部均值）
var relative_position = dem_mosaic.subtract(dem_local_mean);

// 对相对位置进行平滑（2像素圆形邻域）
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(2)
});

// 计算坡度（使用 GEE 的 Terrain 模块）
var slope = ee.Terrain.slope(dem_mosaic);

// 相对位置分级规则
var position_rules = [
  [-5000.0, -10.0, 1.0],
  [-10.0, 10.0, 2.0],
  [10.0, 5000.0, 3.0]
];

// 相对位置分级
var position_class = ee.Image(2).where(relative_position_smooth.lt(-10), 1)
  .where(relative_position_smooth.gt(10), 3);

// 坡度分级规则
var slope_rules = [
  [0.0, 6.0, 1.0],
  [6.0, 90.0, 2.0]
];

// 坡度分级
var slope_class = ee.Image(2).where(slope.lt(6), 1);

// 组合编码（位置编码乘以10 + 坡度编码）
var position_code = position_class.multiply(10);
var combined_class = position_code.add(slope_class);

// 地貌单元分类规则
var landform_rules = [
  [10.5, 12.5, 1.0],
  [20.5, 21.5, 4.0],
  [21.5, 22.5, 2.0],
  [30.5, 32.5, 3.0]
];

// 地貌单元分类
var landform = ee.Image(0).where(combined_class.gt(10.5).and(combined_class.lt(12.5)), 1)
  .where(combined_class.gt(20.5).and(combined_class.lt(21.5)), 4)
  .where(combined_class.gt(21.5).and(combined_class.lt(22.5)), 2)
  .where(combined_class.gt(30.5).and(combined_class.lt(32.5)), 3);

// 地貌分类平滑（使用众数滤波）
var landform_smooth = landform.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var position_vis = {
  min: 1,
  max: 3,
  palette: ['#2b83ba', '#f7f7f7', '#d7191c']
};

var slope_vis = {
  min: 1,
  max: 2,
  palette: ['#d9f0d3', '#fdae61']
};

var landform_vis = {
  min: 1,
  max: 4,
  palette: ['#2b83ba', '#fdae61', '#d7191c', '#cccccc']
};

// 添加图层到地图
Map.addLayer(position_class, position_vis, '相对位置类型结果');
Map.addLayer(slope_class, slope_vis, '坡度分组结果');
Map.addLayer(landform_smooth, landform_vis, '山脊-坡面-谷地基础粗分');

// 设置地图中心
Map.setCenter(115.0, 30.5, 8);