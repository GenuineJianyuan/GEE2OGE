// 加载 DEM 数据（ASTER GDEM 30m）
var dem = ee.Image('NASA/ASTER_GED/AG100_003');

// 计算地形位置指数（TPI）
// TPI = DEM - focalMean(DEM, 环形邻域)
var tpi = dem.subtract(
  dem.reduceNeighborhood({
    reducer: ee.Reducer.mean(),
    kernel: ee.Kernel.circle({
      radius: 1, 
      units: 'pixels'
    })
  })
);

// 可视化参数
var vis_params = {min: -100, max: 100, palette: ['blue', 'white', 'red']};

// 添加图层到地图
Map.addLayer(tpi, vis_params, 'TPI');

// 设置地图中心
Map.setCenter(56.25, 28.40, 11);