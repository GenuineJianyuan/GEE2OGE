// 加载 Landsat 8 影像（对应 OGE 的 LC81220392015275LGN00）
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 转换为浮点型（对应 Coverage.toFloat）
var lc08_f = lc08.toFloat();

// 选择近红外和红光波段（对应 Coverage.selectBands）
var nir = lc08_f.select('B5');
var red = lc08_f.select('B4');

// 计算 NDVI（归一化植被指数）
var ndvi_num = nir.subtract(red);
var ndvi_den = nir.add(red);
var ndvi = ndvi_num.divide(ndvi_den);

// 设置常数（对应 M = 2.0）
var M = 2.0;

// 设置植被和土壤的 NDVI 阈值
var NDVI_veg = 0.9;
var NDVI_soil = 0.1;

// 计算植被覆盖度 f_v（对应 Coverage.subtractNum 和 divideNum）
var f_v = ndvi.subtract(NDVI_soil);
f_v = f_v.divide(0.8);

// 设置植被和土壤的反射率参数
var R_red_v = 0.25;
var R_nir_v = 0.65;

// 计算 MPDI（改进型垂直干旱指数）
// term1 = red + red * M
var red_mnir = red.multiply(M);
var term1 = red.add(red_mnir);

// term2 = f_v * (nir * M + R_red_v)
var nir_mnir_v = nir.multiply(M);
var term2_v = nir_mnir_v.add(R_red_v);
var term2 = f_v.multiply(term2_v);

// term3 = (1 - f_v) * sqrt(1 + M^2) = (1 - f_v) * 2.236
var one_minus_fv_1 = f_v.multiply(2);
var one_minus_fv_2 = f_v.subtract(one_minus_fv_1);
var one_minus_fv = one_minus_fv_2.add(1);
var term3 = one_minus_fv.multiply(2.236);

// MPDI = (term1 - term2) / term3
var mpdi = term1.subtract(term2);
mpdi = mpdi.divide(term3);

// 可视化参数（对应 vis_params）
var vis_params = {
    min: 0,
    max: 1,
    palette: [
        '#0000FF', '#00FFFF', '#00FF00', '#FFFF00',
        '#FFA500', '#FF0000', '#800000'
    ]
};

// 在地图上显示 MPDI 结果（对应 .styles().getMap()）
Map.addLayer(mpdi, vis_params, '垂直干旱指数 PDI');

// 设置地图中心点（对应 oge.mapclient.centerMap）
Map.setCenter(114.28, 30.57, 7);