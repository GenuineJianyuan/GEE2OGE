// 读取一景 Landsat 9 Collection 2 Level-2 反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 1) 提取原始影像显示层（自然色）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 提取植被表达所需波段
var blue_band = lc09.select(['SR_B2']);
var red_band = lc09.select(['SR_B4']);
var nir_band = lc09.select(['SR_B5']);

// 3) 转换为浮点型
// original_image = original_image.toFloat();
blue_band = blue_band.toFloat();
red_band = red_band.toFloat();
nir_band = nir_band.toFloat();

// 4) 应用 Landsat 9 Collection 2 Level-2 地表反射率缩放
// original_image = original_image.toFloat().multiply(0.0000275).add(-0.2);
blue_band = blue_band.multiply(0.0000275).add(-0.2);
red_band = red_band.multiply(0.0000275).add(-0.2);
nir_band = nir_band.multiply(0.0000275).add(-0.2);

// 5) 计算常规植被指数 NDVI = (NIR - Red) / (NIR + Red)
var ndvi_num = nir_band.subtract(red_band);
var ndvi_den = nir_band.add(red_band);
var ndvi = ndvi_num.divide(ndvi_den).rename('NDVI');

// 6) 计算另一种植被状态表达结果 EVI
// EVI = 2.5 * (NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1)
var red_scaled = red_band.multiply(6.0);
var blue_scaled = blue_band.multiply(7.5);

var evi_den = nir_band.add(red_scaled);
evi_den = evi_den.subtract(blue_scaled);
evi_den = evi_den.add(1.0);

var evi_base = ndvi_num.divide(evi_den);
var evi = evi_base.multiply(2.5).rename('EVI');

// 7) 对两种结果做统一范围整理
var veg_vis = {
  min: 0.0,
  max: 0.8,
  palette: ['8c510a', 'd8b365', 'f6e8c3', 'd9f0d3', '7fbf7b', '1b7837']
};

// 原始影像未按 OGE 示例进行缩放，因此显示参数使用 Landsat L2 原始 DN 范围。
var original_vis = {
  min: 7273,
  max: 43636,
  gamma: 1.2
};

// 8) 组织原始影像、两种植被结果及其对照结构
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndvi, veg_vis, 'ndvi');
Map.addLayer(evi, veg_vis, 'evi');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);