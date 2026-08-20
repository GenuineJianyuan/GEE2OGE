// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 转换为浮点数
var lc08_d = lc08.toFloat();

// 选择绿波段 (B3) 和近红外波段 (B5)
var green = lc08_d.select('B3');
var nir = lc08_d.select('B5');

// 计算 NDWI: (Green - NIR) / (Green + NIR)
var numerator = green.subtract(nir);
var denominator = green.add(nir);
var ndwi = numerator.divide(denominator);

// 可视化参数
var vis_params = {
  min: -1,
  max: 1,
  palette: ['blue', 'lightblue', 'green', 'yellow', 'red']
};

// 在地图上显示 NDWI 结果
Map.addLayer(ndwi, vis_params, 'NDWI');

// 设置地图中心点
Map.setCenter(114.28, 30.57, 9);