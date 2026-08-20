// 加载海南岛中部山区DEM数据
var demCollection = ee.ImageCollection('NASA/ASTER_GED/AG100_V003')
  .filterDate('2000-01-01', '2000-01-01')
  .filterBounds(ee.Geometry.Rectangle([108.5, 18.1, 111.0, 20.1]));

// 镶嵌DEM影像
var dem = demCollection.mosaic();

// 对DEM进行均值滤波平滑处理
var demBase = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 生成山体阴影图
var hillshade = ee.Terrain.hillshade(demBase);

// DEM可视化参数
var demVis = {
  palette: ['#274e13', '#5b8a3c', '#b7b26a', '#d9c59a', '#f5f5f5']
};

// 山体阴影可视化参数
var shadeVis = {
  palette: ['#1f1f1f', '#555555', '#8a8a8a', '#c0c0c0', '#f2f2f2']
};

// 添加DEM图层到地图
Map.addLayer(demBase, demVis, 'dem_base');

// 添加山体阴影图层到地图
Map.addLayer(hillshade, shadeVis, 'hillshade');

// 设置地图中心点
Map.setCenter(109.7, 19.1, 9);