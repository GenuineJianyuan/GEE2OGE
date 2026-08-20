// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 选择 RGB 波段用于真彩色显示
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择 NIR 和 SWIR1 波段用于 NDMI 计算
var nir_band = lc09.select('SR_B5').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();

// 计算 NDMI = (NIR - SWIR1) / (NIR + SWIR1)
var numerator = nir_band.subtract(swir1_band);
var denominator = nir_band.add(swir1_band);
var ndmi = numerator.divide(denominator);

// 真彩色显示参数
var original_vis = {
  bands: ['SR_B4', 'SR_B3', 'SR_B2'],
  min: 7000,
  max: 12000
};

// NDMI 显示参数（蓝绿色表示湿润，棕黄色表示干燥）
var ndmi_vis = {
  min: -0.2,
  max: 0.3,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, '原始影像');
Map.addLayer(ndmi, ndmi_vis, 'NDMI 植被水分指数');

// 设置地图中心点为湖北东部区域
Map.setCenter(115.35899045035, 30.296925757799997, 11);