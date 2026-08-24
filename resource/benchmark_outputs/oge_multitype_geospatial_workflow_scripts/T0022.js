// 读取一景 Landsat 9 Collection 2 Level-2 地表反射率影像
var lc09 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
  .filter(ee.Filter.eq(
    'LANDSAT_PRODUCT_ID',
    'LC09_L2SP_122039_20230306_20230308_02_T1'
  ))
  .first();

// 1) 提取原始影像显示层，并应用 Landsat Collection 2 Level-2 反射率缩放系数
var original_image = lc09
  .select(['SR_B4', 'SR_B3', 'SR_B2'])
  .multiply(0.0000275)
  .add(-0.2);

// 2) 为 NDMI 单独准备输入波段，并转换为实际地表反射率浮点值
var ndmi_input = lc09
  .select(['SR_B5', 'SR_B6'])
  .multiply(0.0000275)
  .add(-0.2)
  .toFloat();

// 3) 计算植被水分相关指数 NDMI = (NIR - SWIR1) / (NIR + SWIR1)
var ndmi = ndmi_input.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDMI');

// 可视化参数
var original_vis = {};

var ndmi_vis = {
  min: -0.2,
  max: 0.3,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

// 4) 组织原始影像与指数结果的对照展示
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndmi, ndmi_vis, 'ndmi');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);