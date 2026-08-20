// 加载 Landsat 9 Collection 2 Level 2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LANDSAT_LC09_122039_20230306');

// 选择原始 RGB 波段
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择各波段并转换为浮点型
var green_band = lc09.select('SR_B3').toFloat();
var red_band = lc09.select('SR_B4').toFloat();
var nir_band = lc09.select('SR_B5').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();
var swir2_band = lc09.select('SR_B7').toFloat();

// 计算 NDVI
var ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band));

// 计算 NBR
var nbr = nir_band.subtract(swir2_band).divide(nir_band.add(swir2_band));

// 计算 NBR2
var nbr2 = swir1_band.subtract(swir2_band).divide(swir1_band.add(swir2_band));

// 计算 MNDWI
var mndwi = green_band.subtract(swir1_band).divide(green_band.add(swir1_band));

// 植被掩膜：NDVI > 0.25
var vegetation_mask = ndvi.multiply(100).gt(25);

// 水体掩膜：MNDWI > 0.10
var water_mask = mndwi.multiply(100).gt(10);

// 非水体掩膜
var non_water_mask = water_mask.multiply(-1).add(1);

// NBR 受损评分（归一化到 0-1）
var nbr_score = nbr.multiply(-1).add(1).divide(2);

// NBR2 受损评分（归一化到 0-1）
var nbr2_score = nbr2.multiply(-1).add(1).divide(2);

// 联合受损评分
var joint_score = nbr_score.multiply(nbr2_score);

// 应用植被和非水体掩膜
joint_score = joint_score.multiply(vegetation_mask).multiply(non_water_mask);

// 中值滤波平滑
joint_score = joint_score.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// 联合受损阈值：评分 > 0.35
var joint_degraded = joint_score.multiply(100).gt(35);

// 再次中值滤波
joint_degraded = joint_degraded.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// 可视化参数
var original_vis = {bands: ['SR_B4', 'SR_B3', 'SR_B2'], min: 7000, max: 12000};

var nbr_vis = {
  min: -0.2,
  max: 0.6,
  palette: ['#7f3b08', '#b35806', '#f1a340', '#fee0b6', '#d8daeb', '#998ec3', '#542788']
};

var nbr2_vis = {
  min: -0.2,
  max: 0.4,
  palette: ['#7f3b08', '#b35806', '#f1a340', '#fee0b6', '#d8daeb', '#998ec3', '#542788']
};

var joint_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#b2182b']
};

// 添加图层到地图
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(nbr, nbr_vis, 'nbr');
Map.addLayer(nbr2, nbr2_vis, 'nbr2');
Map.addLayer(joint_degraded, joint_vis, 'joint_degraded');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);