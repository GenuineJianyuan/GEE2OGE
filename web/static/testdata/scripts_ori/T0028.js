// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_115028_20230116');

// 选择 RGB 波段用于真彩色显示
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择绿波段和短波红外1波段用于计算 NDSI
var green_band = lc09.select('SR_B3').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();

// 计算 NDSI (归一化差分积雪指数)
var ndsi_num = green_band.subtract(swir1_band);
var ndsi_den = green_band.add(swir1_band);
var ndsi = ndsi_num.divide(ndsi_den);

// 真彩色影像可视化参数
var original_vis = {
  min: 0,
  max: 3000,
  bands: ['SR_B4', 'SR_B3', 'SR_B2']
};

// NDSI 可视化参数
var ndsi_vis = {
  min: -0.2,
  max: 1.0,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#d9f0d3', '#c7eae5', '#2166ac', '#f7fbff']
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndsi, ndsi_vis, 'ndsi');

// 设置地图中心点
Map.setCenter(131.0412992405, 46.01424296135, 11);