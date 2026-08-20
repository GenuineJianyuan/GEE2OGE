// 加载ASTER GDEM DEM数据
var dem = ee.Image('NASA/ASTER_GED/AG100_V003');

// 使用reproject将DEM重投影到EPSG:4326坐标系
var a = dem.reproject({
  crs: 'EPSG:4326',
  scale: 30
});

// 可视化参数
var vis_params = {
  min: -1, 
  max: 1,
  palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']
};

// 添加重投影后的影像
Map.addLayer(a, vis_params, 'a');

// 添加原始DEM影像
Map.addLayer(dem, vis_params, 'dem');

// 设置地图中心点
Map.setCenter(56.25, 28.40, 11);