// 加载 Landsat 8 影像（TOA 反射率）
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 转换为浮点型
var lc08_d = lc08.toFloat();

// 选择绿波段（B3）和短波红外波段（B6）用于 NDSI 计算
var b8 = lc08_d.select('B3');
var b2 = lc08_d.select('B6');

// 计算 NDSI = (Green - SWIR) / (Green + SWIR)
var numerator = b8.subtract(b2);
var denominator = b8.add(b2);
var ndsi = numerator.divide(denominator);

// 设置可视化参数并添加到地图
Map.addLayer(ndsi, {min: 0.9, max: 1.1, palette: ['red', 'white', 'blue']}, 'NDSI');

// 设置地图中心点
Map.setCenter(114.28, 30.57, 9);