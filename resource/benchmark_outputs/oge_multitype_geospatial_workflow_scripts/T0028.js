var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_115028_20230116');

// 1) 原始影像显示层（自然色）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 提取雪盖表达所需波段
var green_band = lc09.select(['SR_B3']);
var swir1_band = lc09.select(['SR_B6']);

// 3) 转换为浮点型
var green_band = green_band.toFloat();
var swir1_band = swir1_band.toFloat();

// 4) 计算 NDSI = (Green - SWIR1) / (Green + SWIR1)
var ndsi_num = green_band.subtract(swir1_band);
var ndsi_den = green_band.add(swir1_band);
var ndsi = ndsi_num.divide(ndsi_den);

// 可视化参数
var original_vis = {};

var ndsi_vis = {
  min: -0.2,
  max: 1.0,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#d9f0d3', '#c7eae5', '#2166ac', '#f7fbff']
};

// 5) 组织原始影像与雪盖结果的对照展示
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndsi, ndsi_vis, 'ndsi');

// 设置地图中心
Map.setCenter(131.0412992405, 46.01424296135, 11);