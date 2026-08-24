// 读取一景 Landsat 9 Collection 2 Level-2 反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 1) 提取原始影像显示层（自然色）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 为 MNDWI 单独准备输入波段
var mndwi_input = lc09.select(['SR_B3', 'SR_B6']);

// 3) 转换为浮点型
mndwi_input = mndwi_input.toFloat();

// 4) 应用 Landsat 9 Level-2 表面反射率缩放
mndwi_input = mndwi_input
  .multiply(0.0000275)
  .add(-0.2);

// 5) 计算 MNDWI = (Green - SWIR1) / (Green + SWIR1)
var mndwi = mndwi_input.normalizedDifference(['SR_B3', 'SR_B6']);

// 可视化参数
var original_vis = {};

var water_vis = {
  min: -0.5,
  max: 0.5,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

// 6) 组织原始影像与水体结果的对照展示
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(mndwi, water_vis, 'mndwi');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);