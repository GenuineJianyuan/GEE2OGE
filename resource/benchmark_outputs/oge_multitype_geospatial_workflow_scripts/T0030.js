// 读取 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_115028_20230116');

// Landsat Collection 2 Level-2 地表反射率缩放参数
var scaleFactor = 0.0000275;
var addOffset = -0.2;

// 1) 原始影像显示层（自然色）
var original_image = lc09
  .select(['SR_B4', 'SR_B3', 'SR_B2'])
  .multiply(scaleFactor)
  .add(addOffset);

// 2) 为 NDSI 单独准备输入波段
var ndsi_input = lc09
  .select(['SR_B3', 'SR_B6'])
  .multiply(scaleFactor)
  .add(addOffset)
  .toFloat();

// 3) 为 NDVI 单独准备输入波段
var ndvi_input = lc09
  .select(['SR_B5', 'SR_B4'])
  .multiply(scaleFactor)
  .add(addOffset)
  .toFloat();

// 4) 计算雪盖相关指数 NDSI = (Green - SWIR1) / (Green + SWIR1)
var ndsi = ndsi_input.normalizedDifference(['SR_B3', 'SR_B6']).rename('NDSI');

// 5) 计算辅助背景区分结果 NDVI = (NIR - Red) / (NIR + Red)
var ndvi = ndvi_input.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');

// 6) 对雪盖结果做初步阈值提取，形成候选雪区：NDSI > 0.40
var ndsi_scaled = ndsi.multiply(100.0);
var snow_candidate = ndsi_scaled.gt(40).rename('snow_candidate');

// 7) 利用辅助结果压制更像植被背景的区域：NDVI < 0.15
var ndvi_inverse = ndvi.multiply(-100.0);
ndvi_inverse = ndvi_inverse.add(15.0);
var low_vegetation_mask = ndvi_inverse.gt(0).rename('low_vegetation_mask');

// 8) 生成高置信雪区结果
var snow_high_conf = snow_candidate
  .multiply(low_vegetation_mask)
  .rename('snow_high_conf');

// 9) 对高置信雪区结果做基础整理：方形 1 像元邻域中值滤波
snow_high_conf = snow_high_conf
  .reduceNeighborhood({
    reducer: ee.Reducer.median(),
    kernel: ee.Kernel.square({radius: 1, units: 'pixels', normalize: false})
  })
  .rename('snow_high_conf');

// 可视化参数
var original_vis = {
  min: 0.0,
  max: 0.3,
  bands: ['SR_B4', 'SR_B3', 'SR_B2']
};

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

// 10) 组织原始影像、中间结果和最终结果的对照结构
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndsi, ndsi_vis, 'ndsi');
Map.addLayer(ndvi, ndvi_vis, 'ndvi');
Map.addLayer(snow_high_conf, snow_vis, 'snow_high_conf');

// 设置地图中心
Map.setCenter(131.0412992405, 46.01424296135, 11);