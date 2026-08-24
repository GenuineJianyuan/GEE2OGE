// 读取一景 Landsat 9 Collection 2 Level-2 地表反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_115028_20230116');

// Landsat 9 Collection 2 Level-2 SR 波段缩放系数
var srScale = 0.0000275;
var srOffset = -0.2;

// 1) 原始影像显示层（自然色）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2'])
  .multiply(srScale)
  .add(srOffset);

// 2) 提取雪盖表达所需波段，并转换为浮点型和实际地表反射率
var green_band = lc09.select(['SR_B3'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

var swir1_band = lc09.select(['SR_B6'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

// 3) 计算 NDSI = (Green - SWIR1) / (Green + SWIR1)
var ndsi_num = green_band.subtract(swir1_band);
var ndsi_den = green_band.add(swir1_band);
var ndsi = ndsi_num.divide(ndsi_den).rename('NDSI');

// 4) 对指数结果做阈值提取，生成初步雪区结果
// NDSI > 0.40；保留先乘以 100、再以 40 阈值二值化的原始逻辑
var ndsi_scaled = ndsi.multiply(100.0);
var snow_initial = ndsi_scaled.gt(40).rename('snow_initial');

// 5) 对初步雪区结果做基础整理：3 × 3 像元方形邻域中值滤波
var snow_final = snow_initial.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square({
    radius: 1,
    units: 'pixels',
    normalize: false
  })
}).rename('snow_final');

// 可视化参数
var original_vis = {
  min: 0.0,
  max: 0.3,
  bands: ['SR_B4', 'SR_B3', 'SR_B2']
};

var ndsi_vis = {
  min: -0.2,
  max: 1.0,
  palette: ['8c510a', 'd8b365', 'f6e8c3', 'd9f0d3', 'c7eae5', '2166ac', 'f7fbff']
};

var snow_vis = {
  min: 0,
  max: 1,
  palette: ['f5f5f5', '2166ac']
};

// 6) 将原始影像、雪盖指数、初步雪区和整理后雪区添加到地图
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndsi, ndsi_vis, 'ndsi');
Map.addLayer(snow_initial, snow_vis, 'snow_initial');
Map.addLayer(snow_final, snow_vis, 'snow_final');

// 设置地图中心
Map.setCenter(131.0412992405, 46.01424296135, 11);