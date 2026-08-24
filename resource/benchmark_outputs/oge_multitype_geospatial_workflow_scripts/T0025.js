// 读取 Landsat 9 Collection 2 Level-2 地表反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// Landsat Collection 2 Level-2 SR 波段缩放系数
var srScale = 0.0000275;
var srOffset = -0.2;

// 1) 提取原始影像显示层
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

// 2) 提取所需波段，并转换为物理地表反射率浮点值
var green_band = lc09.select(['SR_B3'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

var red_band = lc09.select(['SR_B4'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

var nir_band = lc09.select(['SR_B5'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

var swir1_band = lc09.select(['SR_B6'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

var swir2_band = lc09.select(['SR_B7'])
  .toFloat()
  .multiply(srScale)
  .add(srOffset);

// 4) 计算植被背景指数 NDVI = (NIR - Red) / (NIR + Red)
var ndvi_num = nir_band.subtract(red_band);
var ndvi_den = nir_band.add(red_band);
var ndvi = ndvi_num.divide(ndvi_den);

// 5) 计算受损植被相关指数 A：NBR = (NIR - SWIR2) / (NIR + SWIR2)
var nbr_num = nir_band.subtract(swir2_band);
var nbr_den = nir_band.add(swir2_band);
var nbr = nbr_num.divide(nbr_den);

// 6) 计算受损植被相关指数 B：NBR2 = (SWIR1 - SWIR2) / (SWIR1 + SWIR2)
var nbr2_num = swir1_band.subtract(swir2_band);
var nbr2_den = swir1_band.add(swir2_band);
var nbr2 = nbr2_num.divide(nbr2_den);

// 7) 计算水体指数 MNDWI = (Green - SWIR1) / (Green + SWIR1)
var mndwi_num = green_band.subtract(swir1_band);
var mndwi_den = green_band.add(swir1_band);
var mndwi = mndwi_num.divide(mndwi_den);

// 8) 候选植被区：NDVI > 0.25
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gt(25);

// 9) 明显水体掩膜：MNDWI > 0.10
var mndwi_scaled = mndwi.multiply(100.0);
var water_mask = mndwi_scaled.gt(10);

// 10) 非水体掩膜
var non_water_mask = water_mask.multiply(-1.0).add(1.0);

// 11) 把 NBR / NBR2 转成“受损倾向分数”
// 分数越高，表示越值得优先关注
// score = (1 - index) / 2
var nbr_score = nbr.multiply(-1.0).add(1.0).divide(2.0);
var nbr2_score = nbr2.multiply(-1.0).add(1.0).divide(2.0);

// 12) 联合受损评分
var joint_score = nbr_score.add(nbr2_score).divide(2.0);

// 13) 限定在“有一定植被且非明显水体”的区域内
joint_score = joint_score.multiply(vegetation_mask);
joint_score = joint_score.multiply(non_water_mask);

// 14) 对联合评分做一次高分提取，生成更聚焦的最终结果
var joint_score_scaled = joint_score.multiply(100.0);
var joint_degraded = joint_score_scaled.gt(20);

// 15) 再做一次简单清理：方形 1 像元邻域中值滤波
var square_kernel = ee.Kernel.square({
  radius: 1,
  units: 'pixels',
  normalize: false
});

joint_degraded = joint_degraded.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: square_kernel
});

// 可视化参数
var original_vis = {};

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

// 16) 组织结果展示
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(nbr, nbr_vis, 'nbr');
Map.addLayer(nbr2, nbr2_vis, 'nbr2');
Map.addLayer(joint_degraded, joint_vis, 'joint_degraded');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);