// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 转换为浮点型
var lc08_d = lc08.toFloat();

// 计算 MNDWI（使用绿波段 B3 和 SWIR1 波段 B6）
var mndwi = lc08_d.normalizedDifference(['B3', 'B6']);

// 可视化参数
var vis_params = {
  min: -1, 
  max: 1, 
  palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']
};

// 添加图层到地图
Map.addLayer(mndwi, vis_params, 'mndwi');

// 设置地图中心
Map.setCenter(114.28, 30.57, 9);