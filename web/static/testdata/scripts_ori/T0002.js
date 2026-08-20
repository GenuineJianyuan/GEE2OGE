// 加载海南岛中部山区的DEM数据
var demCollection = ee.ImageCollection('NASA/ASTER_GED/AG100_V003')
  .filterBounds(ee.Geometry.Rectangle([108.5, 18.1, 111.0, 20.1]));

// 拼接DEM影像
var originalDem = demCollection.mosaic();

// 获取投影信息
var crs = originalDem.projection();

// 对DEM进行平滑处理（使用3x3均值滤波）
var smoothDem = originalDem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 生成原始DEM的山体阴影
var originalHillshade = ee.Terrain.hillshade(originalDem);

// 生成平滑后DEM的山体阴影
var processedHillshade = ee.Terrain.hillshade(smoothDem);

// 可视化参数
var demVis = {
  palette: ['#274e13', '#5b8a3c', '#b7b26a', '#d9c59a', '#f5f5f5']
};

var shadeVis = {
  palette: ['#1f1f1f', '#555555', '#8a8a8a', '#c0c0c0', '#f2f2f2']
};

// 添加图层到地图
Map.addLayer(originalDem, demVis, '原始DEM');
Map.addLayer(originalHillshade, shadeVis, '原始山体阴影');
Map.addLayer(processedHillshade, shadeVis, '处理后山体阴影');

// 设置地图中心
Map.setCenter(109.7, 19.1, 9);