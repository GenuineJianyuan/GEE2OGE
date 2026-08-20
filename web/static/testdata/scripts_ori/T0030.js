// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_115028_20230116');

// 选择原始影像波段 (RGB)
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择所需波段并转换为浮点型
var green_band = lc09.select('SR_B3').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();
var red_band = lc09.select('SR_B4').toFloat();
var nir_band = lc09.select('SR_B5').toFloat();

// 计算 NDSI (归一化差异雪指数)
var ndsi = green_band.subtract(swir1_band).divide(green_band.add(swir1_band));

// 计算 NDVI (归一化差异植被指数)
var ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band));

// 雪候选区：NDSI > 0.4 (即 NDSI*100 > 40)
var ndsi_scaled = ndsi.multiply(100.0);
var snow_candidate = ndsi_scaled.gt(40);

// 低植被掩膜：NDVI < 0.15 (即 -NDVI*100 + 15 > 0)
var ndvi_inverse = ndvi.multiply(-100.0).add(15.0);
var low_vegetation_mask = ndvi_inverse.gt(0);

// 高置信雪区：雪候选区与低植被掩膜的交集
var snow_high_conf = snow_candidate.multiply(low_vegetation_mask);

// 对高置信雪区应用中值滤波平滑
snow_high_conf = snow_high_conf.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// 可视化参数设置
var original_vis = {bands: ['SR_B4', 'SR_B3', 'SR_B2'], min: 7000, max: 12000};

var ndsi_vis = {
  min: -0.2,
  max: 1.0,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#d9f0d3', '#c7eae5', '#2166ac', '#f7fbff']
};

var ndvi_vis = {
  min: -0.2,
  max: 0.4,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#d9f0d3', '#7fbf7b', '#1b7837']
};

var snow_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#2166ac']
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, '原始影像');
Map.addLayer(ndsi, ndsi_vis, 'NDSI');
Map.addLayer(ndvi, ndvi_vis, 'NDVI');
Map.addLayer(snow_high_conf, snow_vis, '高置信雪区');

// 设置地图中心
Map.setCenter(131.0412992405, 46.01424296135, 11);