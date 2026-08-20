// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 选择所需波段并应用缩放因子
var green = lc08.select('B3').multiply(0.0001);
var red = lc08.select('B4').multiply(0.0001);
var nir = lc08.select('B5').multiply(0.0001);
var swir1 = lc08.select('B6').multiply(0.0001);
var swir2 = lc08.select('B7').multiply(0.0001);

// 计算 WI2015 指数的各项
var term_green = green.multiply(171.0);
var term_red = red.multiply(3.0);
var term_nir = nir.multiply(-70.0);
var term_swir1 = swir1.multiply(-45.0);
var term_swir2 = swir2.multiply(-71.0);

// 求和并添加常数项
var wi_sum = term_green.add(term_red);
wi_sum = wi_sum.add(term_nir);
wi_sum = wi_sum.add(term_swir1);
wi_sum = wi_sum.add(term_swir2);
var wi2015 = wi_sum.add(1.7204);

// 可视化参数
var vis_params = {
  min: -100,
  max: 200,
  palette: ['#000000', '#303030', '#606060', '#909090', '#C0C0C0', '#FFFFFF']
};

// 在地图上显示结果
Map.addLayer(wi2015, vis_params, 'WI2015');
Map.setCenter(114.28, 30.57, 9);