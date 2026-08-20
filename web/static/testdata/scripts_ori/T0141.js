// 加载 Landsat 8 影像（TOA 反射率）
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');
var lc08_f = lc08.toFloat();

// 加载地表温度波段（使用 Landsat 8 热红外波段）
var b10 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002').select('B10');
var b10_float = b10.toFloat();

// 计算 NDVI
var nir = lc08_f.select('B5');
var red = lc08_f.select('B4');
var ndvi_num = nir.subtract(red);
var ndvi_den = nir.add(red);
var ndvi = ndvi_num.divide(ndvi_den);

// 计算地表温度（LST）
var bt = b10_float.multiply(0.00341802);
var bt_k = bt.add(149.0);
var lst_c = bt_k.subtract(273.15);

// 定义干湿边参数
var a_wet = 25.0;
var b_wet = -10.0;
var a_dry = 45.0;
var b_dry = -5.0;

// 计算湿边和干边温度
var ndvi_bwet = ndvi.multiply(b_wet);
var lst_min = ndvi_bwet.add(a_wet);

var ndvi_bdry = ndvi.multiply(b_dry);
var lst_max = ndvi_bdry.add(a_dry);

// 计算 TVDI
var num = lst_c.subtract(lst_min);
var den = lst_max.subtract(lst_min);
var tvdi = num.divide(den);

// 可视化参数
var vis_params = {
    min: 0,
    max: 1,
    palette: ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FFA500', '#FF0000', '#800000']
};

// 添加图层到地图
Map.addLayer(tvdi, vis_params, '温度植被干旱指数 TVDI');
Map.setCenter(114.28, 30.57, 7);