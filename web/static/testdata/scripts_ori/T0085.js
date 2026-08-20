// 加载 ASTER GDEM 数据集
var dem = ee.ImageCollection('NASA/ASTER_GED/AG100_V003')
  .filterDate('2000-01-01', '2000-01-01')
  .filterBounds(ee.Geometry.Rectangle([108.5, 18.1, 111, 20.1]))
  .mosaic();

// 计算地形阴影
var hillshade = ee.Terrain.hillshade(dem, 1, 1);

// 可视化参数
var vis_params = {
  min: -1, 
  max: 1, 
  palette: ['#808080', '#949494', '#a9a9a9', '#bdbebd', '#d3d3d3', '#e9e9e9']
};

// 添加图层到地图
Map.addLayer(hillshade, vis_params, 'DEM Hillshade');

// 设置地图中心
Map.setCenter(109.7, 19.1, 9);