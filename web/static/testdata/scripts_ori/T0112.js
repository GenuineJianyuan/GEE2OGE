// 加载 DEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_V003');

// 计算地形粗糙度（使用标准差作为粗糙度指标）
var roughness = dem.reduceNeighborhood({
  reducer: ee.Reducer.stdDev(),
  kernel: ee.Kernel.square(3)
});

// 可视化参数
var vis_params = {
  min: -1, 
  max: 1,
  palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']
};

// 添加图层到地图
Map.addLayer(roughness, vis_params, 'roughness');
Map.addLayer(dem, vis_params, 'dem');

// 设置地图中心
Map.setCenter(56.25, 28.40, 11);