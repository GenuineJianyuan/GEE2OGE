// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LANDSAT_LC09_122039_20230306');

// 选择 RGB 波段用于真彩色显示
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择计算植被指数和水分指数所需的波段
var red_band = lc09.select(['SR_B4']).toFloat();
var nir_band = lc09.select(['SR_B5']).toFloat();
var swir1_band = lc09.select(['SR_B6']).toFloat();

// 计算 NDVI（归一化植被指数）
var ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band));

// 计算 NDMI（归一化水分指数）
var ndmi = nir_band.subtract(swir1_band).divide(nir_band.add(swir1_band));

// 创建植被掩膜：NDVI > 0.2 的区域
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gt(20);

// 创建干燥掩膜：NDMI < 0.1 的区域（通过取反和偏移实现）
var ndmi_inverse = ndmi.multiply(-100.0);
var dry_mask = ndmi_inverse.add(10.0).gt(0);

// 提取干燥植被区域：植被掩膜和干燥掩膜的交集
var dry_vegetation = vegetation_mask.multiply(dry_mask);

// 应用中值滤波去除噪声
var dry_vegetation = dry_vegetation.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// 可视化参数设置
var original_vis = {
  bands: ['SR_B4', 'SR_B3', 'SR_B2'],
  min: 7000,
  max: 12000
};

var ndvi_vis = {
  min: -0.1,
  max: 0.5,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#d9f0d3', '#7fbf7b', '#1b7837']
};

var ndmi_vis = {
  min: -0.2,
  max: 0.3,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

var dry_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#c51b7d']
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, '原始影像');
Map.addLayer(ndvi, ndvi_vis, 'NDVI');
Map.addLayer(ndmi, ndmi_vis, 'NDMI');
Map.addLayer(dry_vegetation, dry_vis, '干燥植被区');

// 设置地图中心点
Map.setCenter(115.35899045035, 30.296925757799997, 11);