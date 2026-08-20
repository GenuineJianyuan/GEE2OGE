// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 选择 RGB 波段用于真彩色显示
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 提取各波段并转换为浮点型
var green_band = lc09.select('SR_B3').toFloat();
var red_band = lc09.select('SR_B4').toFloat();
var nir_band = lc09.select('SR_B5').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();
var swir2_band = lc09.select('SR_B7').toFloat();

// 计算 NDVI (归一化植被指数)
var ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band));

// 计算 NBR (归一化燃烧指数)
var nbr = nir_band.subtract(swir2_band).divide(nir_band.add(swir2_band));

// 计算 MNDWI (改进型归一化水体指数)
var mndwi = green_band.subtract(swir1_band).divide(green_band.add(swir1_band));

// 植被掩膜：NDVI > 0.2 视为有植被覆盖
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gt(20);

// 受损候选区：NBR 异常低值（NBR*100 < -15）
var nbr_inverse = nbr.multiply(-100.0).add(15.0);
var candidate_nbr = nbr_inverse.gt(0);

// 水体掩膜：MNDWI > 0.1 视为水体
var mndwi_scaled = mndwi.multiply(100.0);
var water_mask = mndwi_scaled.gt(10);

// 非水体掩膜
var non_water_mask = water_mask.multiply(-1.0).add(1.0);

// 组合条件：有植被覆盖 + NBR异常 + 非水体
var degraded_candidate = candidate_nbr.multiply(vegetation_mask).multiply(non_water_mask);

// 中值滤波去除孤立像元
var degraded_candidate = degraded_candidate.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// 可视化参数
var original_vis = {
  bands: ['SR_B4', 'SR_B3', 'SR_B2'],
  min: 7000,
  max: 12000
};

var nbr_vis = {
  min: -0.2,
  max: 0.6,
  palette: ['#7f3b08', '#b35806', '#f1a340', '#fee0b6', '#d8daeb', '#998ec3', '#542788']
};

var candidate_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#b2182b']
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(nbr, nbr_vis, 'nbr');
Map.addLayer(degraded_candidate, candidate_vis, 'degraded_candidate');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);