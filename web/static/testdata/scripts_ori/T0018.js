// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 选择 RGB 波段作为原始影像
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择并转换为浮点型的单波段
var blue_band = lc09.select('SR_B2').toFloat();
var red_band = lc09.select('SR_B4').toFloat();
var nir_band = lc09.select('SR_B5').toFloat();

// 应用缩放因子和偏移量（Collection 2 Level-2 产品的反射率缩放）
blue_band = blue_band.multiply(0.0000275).add(-0.2);
red_band = red_band.multiply(0.0000275).add(-0.2);
nir_band = nir_band.multiply(0.0000275).add(-0.2);

// 计算 NDVI（归一化植被指数）
var ndvi_num = nir_band.subtract(red_band);
var ndvi_den = nir_band.add(red_band);
var ndvi = ndvi_num.divide(ndvi_den);

// 计算 EVI（增强型植被指数）
var red_scaled = red_band.multiply(6.0);
var blue_scaled = blue_band.multiply(7.5);

var evi_den = nir_band.add(red_scaled).subtract(blue_scaled).add(1.0);
var evi_base = ndvi_num.divide(evi_den);
var evi = evi_base.multiply(2.5);

// 植被可视化参数
var veg_vis = {
  min: 0.0,
  max: 0.8,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#d9f0d3', '#7fbf7b', '#1b7837']
};

// 添加图层到地图
Map.addLayer(original_image, {}, '原始影像 (RGB)');
Map.addLayer(ndvi, veg_vis, 'NDVI');
Map.addLayer(evi, veg_vis, 'EVI');

// 设置地图中心点（湖北东部）
Map.setCenter(115.35899045035, 30.296925757799997, 11);