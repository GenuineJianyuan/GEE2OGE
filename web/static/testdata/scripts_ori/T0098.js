// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 转换为浮点型
var lc08_d = lc08.toFloat();

// 选择波段
var blue = lc08_d.select('B2');
var green = lc08_d.select('B3');
var nir = lc08_d.select('B5');
var swir1 = lc08_d.select('B6');
var swir2 = lc08_d.select('B7');

// 计算 AWEIsh 公式的各项
var term1 = green.multiply(2.5);
var term2 = nir.add(swir1);
var term3 = term2.multiply(1.5);
var term4 = swir2.multiply(0.25);

// 计算 AWEIsh
var aweish = blue.add(term1);
aweish = aweish.subtract(term3);
aweish = aweish.subtract(term4);

// 地图展示
Map.setCenter(114.28, 30.57, 9);
Map.addLayer(aweish, {min: -1, max: 1, palette: ['white', 'blue']}, 'AWEIsh');