// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 选择 RGB 波段用于真彩色显示
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择并转换各波段为浮点型
var blue_band = lc09.select('SR_B2').toFloat();
var green_band = lc09.select('SR_B3').toFloat();
var nir_band = lc09.select('SR_B5').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();
var swir2_band = lc09.select('SR_B7').toFloat();

// 应用缩放因子和偏移量进行大气校正
blue_band = blue_band.multiply(0.0000275).add(-0.2);
green_band = green_band.multiply(0.0000275).add(-0.2);
nir_band = nir_band.multiply(0.0000275).add(-0.2);
swir1_band = swir1_band.multiply(0.0000275).add(-0.2);
swir2_band = swir2_band.multiply(0.0000275).add(-0.2);

// 计算 MNDWI (Modified Normalized Difference Water Index)
var mndwi_num = green_band.subtract(swir1_band);
var mndwi_den = green_band.add(swir1_band);
var mndwi = mndwi_num.divide(mndwi_den);

// 计算 AWEIsh (Automated Water Extraction Index with Shadow)
var green_x25 = green_band.multiply(2.5);
var nir_plus_swir1 = nir_band.add(swir1_band);
var nir_swir1_x15 = nir_plus_swir1.multiply(1.5);
var swir2_x025 = swir2_band.multiply(0.25);

var aweish = blue_band.add(green_x25);
aweish = aweish.subtract(nir_swir1_x15);
aweish = aweish.subtract(swir2_x025);

// 可视化参数设置
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

var original_vis = {
  bands: ['SR_B4', 'SR_B3', 'SR_B2'],
  min: 7000,
  max: 12000
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(mndwi, mndwi_vis, 'mndwi');
Map.addLayer(aweish, aweish_vis, 'aweish');

// 设置地图中心点
Map.setCenter(115.35899045035, 30.296925757799997, 11);