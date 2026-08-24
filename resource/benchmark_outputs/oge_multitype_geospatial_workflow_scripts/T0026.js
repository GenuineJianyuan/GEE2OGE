// 读取 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
  .filter(ee.Filter.eq(
    'LANDSAT_PRODUCT_ID',
    'LC09_L2SP_122039_20230306_20230308_02_T1'
  ))
  .first();

// Landsat Collection 2 Level-2 SR 缩放：reflectance = DN * 0.0000275 - 0.2
var applyScaleFactors = function(image) {
  var opticalBands = image.select('SR_B.*')
    .multiply(0.0000275)
    .add(-0.2);
  return image.addBands(opticalBands, null, true);
};

lc09 = applyScaleFactors(lc09);

// 1) 原始影像（仅做参考背景）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 分别为每个指数单独准备两波段输入
var ndvi_input = lc09.select(['SR_B5', 'SR_B4']).toFloat();
var nbr_input = lc09.select(['SR_B5', 'SR_B7']).toFloat();
var nbr2_input = lc09.select(['SR_B6', 'SR_B7']).toFloat();
var mndwi_input = lc09.select(['SR_B3', 'SR_B6']).toFloat();

// 3) 分别计算归一化指数
var ndvi = ndvi_input.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');
var nbr = nbr_input.normalizedDifference(['SR_B5', 'SR_B7']).rename('NBR');
var nbr2 = nbr2_input.normalizedDifference(['SR_B6', 'SR_B7']).rename('NBR2');
var mndwi = mndwi_input.normalizedDifference(['SR_B3', 'SR_B6']).rename('MNDWI');

// ---- 初筛：用 NBR 圈出可疑区 ----
// -100 * NBR + 17 >= 0，等价于 NBR <= 0.17
var nbr_inv = nbr.multiply(-100.0).add(17.0);
var candidate_nbr = nbr_inv.gte(0).rename('candidate_nbr');

// ---- 约束 1：限定“确实有一定植被背景” ----
// NDVI * 100 >= 22，等价于 NDVI >= 0.22
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gte(22).rename('vegetation_mask');

// ---- 约束 2：排除明显水体 ----
// MNDWI * 100 >= 10，等价于 MNDWI >= 0.10
var mndwi_scaled = mndwi.multiply(100.0);
var water_mask = mndwi_scaled.gte(10).rename('water_mask');
var non_water_mask = water_mask.not().rename('non_water_mask');

// 初筛结果先做“植被 + 非水体”约束
var candidate_masked = candidate_nbr
  .and(vegetation_mask)
  .and(non_water_mask)
  .rename('candidate_initial');

// ---- 二次筛查：用 NBR2 再收一遍 ----
// -100 * NBR2 + 8 >= 0，等价于 NBR2 <= 0.08
var nbr2_inv = nbr2.multiply(-100.0).add(8.0);
var candidate_nbr2 = nbr2_inv.gte(0).rename('candidate_nbr2');

var priority_raw = candidate_masked
  .and(candidate_nbr2)
  .rename('priority_raw');

// ---- 基础清理 ----
var priority_final = priority_raw.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square({radius: 1, units: 'pixels'})
}).rename('priority_final');

// 可视化参数
var original_vis = {
  bands: ['SR_B4', 'SR_B3', 'SR_B2'],
  min: 0.0,
  max: 0.3
};

var nbr_vis = {
  min: -0.2,
  max: 0.6,
  palette: ['7f3b08', 'b35806', 'f1a340', 'fee0b6', 'd8daeb', '998ec3', '542788']
};

var nbr2_vis = {
  min: -0.2,
  max: 0.4,
  palette: ['7f3b08', 'b35806', 'f1a340', 'fee0b6', 'd8daeb', '998ec3', '542788']
};

var mask_vis = {
  min: 0,
  max: 1,
  palette: ['f5f5f5', 'b2182b']
};

// 输出
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(nbr, nbr_vis, 'nbr');
Map.addLayer(nbr2, nbr2_vis, 'nbr2');
Map.addLayer(candidate_masked, mask_vis, 'candidate_initial');
Map.addLayer(priority_final, mask_vis, 'priority_final');

Map.setCenter(115.35899045035, 30.296925757799997, 11);