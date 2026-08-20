// 加载 Landsat 8 影像（对应 OGE 的 LC812220392015275LGN00）
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 转换为浮点数（对应 OGE 的 Coverage.toFloat）
var lc08_d = lc08.toFloat();

// 计算 NDVI（对应 OGE 的 Coverage.normalizedDifference）
var NDVI = lc08_d.normalizedDifference(['B5', 'B4']);

// 可视化参数
var vis_params = {
  min: -0.2,
  max: 0.8,
  palette: [
    '#0000FF',
    '#FFFFFF',
    '#00FF00',
    '#006400'
  ]
};

// 在地图上展示 NDVI（对应 OGE 的 .styles().getMap()）
Map.addLayer(NDVI, vis_params, 'NDVI');

// 设置地图中心（对应 OGE 的 oge.mapclient.centerMap）
Map.setCenter(114.28, 30.57, 9);