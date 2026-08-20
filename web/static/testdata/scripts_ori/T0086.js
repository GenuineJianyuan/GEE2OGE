// 加载 ASTER GDEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_003');

// 计算地形坡向
var aspect = ee.Terrain.aspect(dem);

// 可视化参数
var vis_params = {
  min: -1,
  max: 1,
  palette: ['#808080', '#949494', '#a9a9a9', '#bdbebd', '#d3d3d3', '#e9e9e9']
};

// 添加图层到地图
Map.addLayer(aspect, vis_params, 'terrAspect');

// 设置地图中心
Map.setCenter(56.25, 28.40, 11);