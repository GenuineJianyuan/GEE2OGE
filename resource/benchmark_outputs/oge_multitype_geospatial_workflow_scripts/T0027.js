// 读取 Landsat 9 Collection 2 Level-2 地表反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306')
  .select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'])
  .multiply(0.0000275)
  .add(-0.2);

// 1) 原始影像显示层
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 提取所需波段
var green_band = lc09.select(['SR_B3']);
var red_band = lc09.select(['SR_B4']);
var nir_band = lc09.select(['SR_B5']);
var swir1_band = lc09.select(['SR_B6']);
var swir2_band = lc09.select(['SR_B7']);

// 3) 转换为浮点型
// Landsat 9 SR 波段在完成比例因子和偏移量转换后已为浮点型。
green_band = green_band.toFloat();
red_band = red_band.toFloat();
nir_band = nir_band.toFloat();
swir1_band = swir1_band.toFloat();
swir2_band = swir2_band.toFloat();

// 4) 计算植被背景指数 NDVI = (NIR - Red) / (NIR + Red)
var ndvi_num = nir_band.subtract(red_band);
var ndvi_den = nir_band.add(red_band);
var ndvi = ndvi_num.divide(ndvi_den).rename('NDVI');

// 5) 计算主提取指数 NBR = (NIR - SWIR2) / (NIR + SWIR2)
var nbr_num = nir_band.subtract(swir2_band);
var nbr_den = nir_band.add(swir2_band);
var nbr = nbr_num.divide(nbr_den).rename('NBR');

// 6) 计算水体指数 MNDWI = (Green - SWIR1) / (Green + SWIR1)
var mndwi_num = green_band.subtract(swir1_band);
var mndwi_den = green_band.add(swir1_band);
var mndwi = mndwi_num.divide(mndwi_den).rename('MNDWI');

// 7) 候选植被区：NDVI > 0.20
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi.gt(0.20).rename('vegetation_mask');

// 8) 初步异常区：NBR < 0.15
var nbr_inverse = nbr.multiply(-100.0);
nbr_inverse = nbr_inverse.add(15.0);
var candidate_nbr = nbr.lt(0.15).rename('candidate_nbr');

// 9) 明显水体掩膜：MNDWI > 0.10
var mndwi_scaled = mndwi.multiply(100.0);
var water_mask = mndwi.gt(0.10).rename('water_mask');

// 10) 非水体掩膜
var non_water_mask = water_mask.multiply(-1.0).add(1.0).rename('non_water_mask');

// 11) 用植被背景和非水体区域约束初步异常区
var degraded_candidate = candidate_nbr
  .multiply(vegetation_mask)
  .multiply(non_water_mask)
  .rename('degraded_candidate');

// 12) 基础清理：方形 1 像元邻域中值滤波
var degraded_kernel = ee.Kernel.square({
  radius: 1,
  units: 'pixels',
  normalize: false
});

degraded_candidate = degraded_candidate
  .reduceNeighborhood({
    reducer: ee.Reducer.median(),
    kernel: degraded_kernel
  })
  .rename('degraded_candidate');

// 可视化参数
var original_vis = {
  min: 0.0,
  max: 0.3,
  bands: ['SR_B4', 'SR_B3', 'SR_B2']
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

// 13) 添加原始影像、NBR 指数图和最终结果图层
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(nbr, nbr_vis, 'nbr');
Map.addLayer(degraded_candidate, candidate_vis, 'degraded_candidate');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);