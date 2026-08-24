// 读取一景 Landsat 9 Collection 2 Level-2 地表反射率影像
var lc09 = ee.Image(
  'LANDSAT/LC09/C02/T1_L2/LC09_L2SP_122039_20230306_20230308_02_T1'
);

// 1) 提取原始影像显示层（自然色）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 提取两类水体表达所需波段
var blue_band = lc09.select(['SR_B2']);
var green_band = lc09.select(['SR_B3']);
var nir_band = lc09.select(['SR_B5']);
var swir1_band = lc09.select(['SR_B6']);
var swir2_band = lc09.select(['SR_B7']);

// 3) 转换为浮点型
blue_band = blue_band.toFloat();
green_band = green_band.toFloat();
nir_band = nir_band.toFloat();
swir1_band = swir1_band.toFloat();
swir2_band = swir2_band.toFloat();

// 4) 应用 Landsat 9 Level-2 地表反射率缩放系数
blue_band = blue_band.multiply(0.0000275).add(-0.2);
green_band = green_band.multiply(0.0000275).add(-0.2);
nir_band = nir_band.multiply(0.0000275).add(-0.2);
swir1_band = swir1_band.multiply(0.0000275).add(-0.2);
swir2_band = swir2_band.multiply(0.0000275).add(-0.2);

// 5) 计算水体指数 A：MNDWI = (Green - SWIR1) / (Green + SWIR1)
var mndwi_num = green_band.subtract(swir1_band);
var mndwi_den = green_band.add(swir1_band);
var mndwi = mndwi_num.divide(mndwi_den).rename('MNDWI');

// 6) 计算水体指数 B：AWEIsh
// AWEIsh = Blue + 2.5*Green - 1.5*(NIR + SWIR1) - 0.25*SWIR2
var green_x25 = green_band.multiply(2.5);
var nir_plus_swir1 = nir_band.add(swir1_band);
var nir_swir1_x15 = nir_plus_swir1.multiply(1.5);
var swir2_x025 = swir2_band.multiply(0.25);

var aweish = blue_band.add(green_x25);
aweish = aweish.subtract(nir_swir1_x15);
aweish = aweish.subtract(swir2_x025).rename('AWEIsh');

// 7) 对两种结果做统一整理
var mndwi_vis = {
  min: -0.5,
  max: 0.5,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

var aweish_vis = {
  min: -1.0,
  max: 1.0,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

// Landsat C2 L2 SR 原始整数值对应约 0～0.3 的表面反射率。
var original_vis = {
  min: 7273,
  max: 18182,
  gamma: 1.2
};

// 8) 添加原始影像、两种水体指数结果图层
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(mndwi, mndwi_vis, 'mndwi');
Map.addLayer(aweish, aweish_vis, 'aweish');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);