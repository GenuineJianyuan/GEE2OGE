// 加载海南岛中部山区 DEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_V003')
  .select(' elevation_m')
  .clip(ee.Geometry.Rectangle([108.5, 18.1, 111.0, 20.1]));

// 获取原始投影信息
var original_crs = dem.projection();
print('原始投影:', original_crs);

// 重投影到 Web Mercator (EPSG:3857)，分辨率 100 米
var standard_dem = dem.reproject({
  crs: 'EPSG:3857',
  scale: 100
});

// 平滑处理（3x3 均值滤波）
var smooth_dem = standard_dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 生成山体阴影
var hillshade = ee.Terrain.hillshade(smooth_dem);

// 可视化参数
var dem_vis = {
  min: 0,
  max: 1000,
  palette: ['#274e13', '#5b8a3c', '#b7b26a', '#d9c59a', '#f5f5f5']
};

var shade_vis = {
  min: 0,
  max: 255,
  palette: ['#1f1f1f', '#555555', '#8a8a8a', '#c0c0c0', '#f2f2f2']
};

// 添加图层到地图
Map.addLayer(standard_dem, dem_vis, '标准化 DEM');
Map.addLayer(hillshade, shade_vis, '山体阴影');

// 设置地图中心
Map.setCenter(109.7, 19.1, 8);