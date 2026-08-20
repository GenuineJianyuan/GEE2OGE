// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306_20230308_02_T1');

// 选择 RGB 波段用于真彩色显示
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择绿波段和短波红外1波段
var green_band = lc09.select(['SR_B3']);
var swir1_band = lc09.select(['SR_B6']);

// 转换为浮点型
var green_band = green_band.toFloat();
var swir1_band = swir1_band.toFloat();

// 应用缩放因子和偏移量（Landsat Collection 2 Level-2 产品的缩放因子为 0.0000275，偏移量为 -0.2）
var green_band = green_band.multiply(0.0000275).add(-0.2);
var swir1_band = swir1_band.multiply(0.0000275).add(-0.2);

// 计算 MNDWI（改进归一化差异水体指数）
var numerator = green_band.subtract(swir1_band);
var denominator = green_band.add(swir1_band);
var mndwi = numerator.divide(denominator);

// 真彩色影像显示参数
var original_vis = {
  min: 0,
  max: 3000,
  bands: ['SR_B4', 'SR_B3', 'SR_B2']
};

// MNDWI 显示参数
var water_vis = {
  min: -0.5,
  max: 0.5,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(mndwi, water_vis, 'mndwi');

// 设置地图中心点（湖北东部）
Map.setCenter(115.35899045035, 30.296925757799997, 11);