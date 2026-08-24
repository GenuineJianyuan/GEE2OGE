var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 整体转浮点
var lc09_f = lc09.toFloat();

// 原始显示层
var original_image = lc09_f.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 整体做 L2 反射率缩放
var lc09_sr = lc09_f.multiply(0.0000275).add(-0.2);

// 直接计算 MNDWI
var mndwi = lc09_sr.normalizedDifference(['SR_B3', 'SR_B6']).rename('MNDWI');

// 阈值提取：MNDWI × 100 >= 5，即 MNDWI >= 0.05
var mndwi_scaled = mndwi.multiply(100.0);
var water_mask = mndwi_scaled.gte(5).rename('water_mask');

// 使用 3 × 3 正方形邻域进行均值滤波
var water_result = water_mask.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1, 'pixels', false)
}).rename('water_result');

var original_vis = {};

var water_index_vis = {
  min: -0.5,
  max: 0.5,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

var water_mask_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#5ab4ac']
};

Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(mndwi, water_index_vis, 'mndwi');
Map.addLayer(water_result, water_mask_vis, 'water_result');

Map.setCenter(115.35899045035, 30.2969257578, 10);