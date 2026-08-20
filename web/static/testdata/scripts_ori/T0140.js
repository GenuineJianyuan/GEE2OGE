// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 选择绿波段和蓝波段
var green = lc08.select('B3');
var blue = lc08.select('B2');

// 计算 NDPI = (Green - Blue) / (Green + Blue)
var numerator = green.subtract(blue);
var denominator = green.add(blue);
var ndpi = numerator.divide(denominator);

// 可视化参数
var vis_params = {
  min: -1,
  max: 1,
  palette: ['blue', 'cyan', 'green']
};

// 添加图层到地图
Map.addLayer(ndpi, vis_params, 'NDPI');

// 设置地图中心
Map.setCenter(114.28, 30.57, 9);