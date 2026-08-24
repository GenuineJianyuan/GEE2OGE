// 读取一景 Landsat 9 Collection 2 Level-2 反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 1) 提取原始影像显示层（自然色）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 为 NDVI 单独准备输入波段
var ndvi_input = lc09.select(['SR_B5', 'SR_B4']);

// 3) 转换为浮点型，便于后续计算
ndvi_input = ndvi_input.toFloat();

// 4) 计算常规植被指数 NDVI = (NIR - Red) / (NIR + Red)
var ndvi = ndvi_input.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');

// 可视化参数
var original_vis = {
  min: 0,
  max: 30000
};

var ndvi_vis = {
  min: 0,
  max: 0.8,
  palette: ['#d9c27a', '#b8d16b', '#7fbf7b', '#3a924a', '#005a32']
};

// 5) 组织原始影像与指数结果的对照展示
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndvi, ndvi_vis, 'ndvi');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);