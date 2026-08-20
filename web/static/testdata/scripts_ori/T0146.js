// 加载 Landsat 8 影像（对应 OGE 的 LC81220392015275LGN00）
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 转换为浮点型（对应 Coverage.toFloat）
var lc08_d = lc08.toFloat();

// 计算 GNDVI（对应 Coverage.normalizedDifference，使用 B5 和 B2 波段）
var GNDVI = lc08_d.normalizedDifference(['B5', 'B2']);

// 可视化参数
var vis_params = {
  min: -1, 
  max: 1, 
  palette: ['gold', 'yellow', 'green', 'lightblue']
};

// 在地图上显示 GNDVI（对应 .styles().getMap()）
Map.addLayer(GNDVI, vis_params, 'GNDVI');

// 设置地图中心（对应 oge.mapclient.centerMap）
Map.setCenter(114.28, 30.57, 9);