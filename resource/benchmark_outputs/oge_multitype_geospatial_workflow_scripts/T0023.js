// 读取 Landsat 9 Collection 2 Level-2 地表反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// Landsat Collection 2 Level-2 SR 缩放系数与偏移量
var applyScaleFactors = function(image) {
  var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  return image.addBands(opticalBands, null, true);
};

lc09 = applyScaleFactors(lc09);

// 1) 提取原始影像显示层（Red, Green, Blue）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 提取植被表达和水分表达所需波段
var index_input = lc09.select(['SR_B4', 'SR_B5', 'SR_B6']);

// 3) 转换为浮点型
index_input = index_input.toFloat();

// 4) 计算植被相关指数 NDVI = (NIR - Red) / (NIR + Red)
var ndvi = index_input.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');

// 5) 计算水分相关指数 NDMI = (NIR - SWIR1) / (NIR + SWIR1)
var ndmi = index_input.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDMI');

// 6) 对植被结果做阈值筛选，形成候选植被区：NDVI > 0.2
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gt(20).rename('vegetation_mask');

// 7) 从水分结果中构建偏干区域掩膜：NDMI < 0.1
var ndmi_inverse = ndmi.multiply(-100.0);
var dry_mask = ndmi_inverse.add(10.0).gt(0).rename('dry_mask');

// 8) 将候选植被区与偏干掩膜组合，生成偏干植被区表达结果
var dry_vegetation = vegetation_mask.multiply(dry_mask).rename('dry_vegetation');

// 9) 对组合结果做基础整理：方形 1 像素邻域均值滤波
var squareKernel = ee.Kernel.square({
  radius: 1,
  units: 'pixels',
  normalize: false
});

dry_vegetation = dry_vegetation.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: squareKernel
}).rename('dry_vegetation');

// 可视化参数
var original_vis = {
  min: 0.0,
  max: 0.3,
  bands: ['SR_B4', 'SR_B3', 'SR_B2']
};

var ndvi_vis = {
  min: -0.1,
  max: 0.5,
  palette: ['8c510a', 'd8b365', 'f6e8c3', 'd9f0d3', '7fbf7b', '1b7837']
};

var ndmi_vis = {
  min: -0.2,
  max: 0.3,
  palette: ['8c510a', 'd8b365', 'f6e8c3', 'c7eae5', '5ab4ac', '01665e']
};

var dry_vis = {
  min: 0,
  max: 1,
  palette: ['f5f5f5', 'c51b7d']
};

// 10) 组织原始影像、中间结果和最终结果的对照结构
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndvi, ndvi_vis, 'ndvi');
Map.addLayer(ndmi, ndmi_vis, 'ndmi');
Map.addLayer(dry_vegetation, dry_vis, 'dry_vegetation');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);