// 读取一景 Landsat 9 Collection 2 Level-2 反射率影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 1) 提取原始影像显示层（自然色）
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 提取植被表达所需波段
var nir_band = lc09.select(['SR_B5']);
var red_band = lc09.select(['SR_B4']);

// 3) 转换为浮点型
original_image = original_image.toFloat();
nir_band = nir_band.toFloat();
red_band = red_band.toFloat();

// 4) 应用 Landsat 9 Level-2 地表反射率缩放
original_image = original_image.multiply(0.0000275).add(-0.2);
nir_band = nir_band.multiply(0.0000275).add(-0.2);
red_band = red_band.multiply(0.0000275).add(-0.2);

// 5) 计算常规植被指数 NDVI = (NIR - Red) / (NIR + Red)
var ndvi_num = nir_band.subtract(red_band);
var ndvi_den = nir_band.add(red_band);
var ndvi = ndvi_num.divide(ndvi_den).rename('NDVI');

// 6) 计算低覆盖区更稳的植被指数 SAVI
// SAVI = 1.5 * (NIR - Red) / (NIR + Red + 0.5)
var savi_den = ndvi_den.add(0.5);
var savi_base = ndvi_num.divide(savi_den);
var savi = savi_base.multiply(1.5).rename('SAVI');

// 7) 使用半径为 1 像素的圆形邻域均值进行平滑
var circleKernel = ee.Kernel.circle({
  radius: 1,
  units: 'pixels',
  normalize: false
});

ndvi = ndvi.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: circleKernel
}).rename('NDVI');

savi = savi.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: circleKernel
}).rename('SAVI');

// 可视化参数
var original_vis = {
  min: 0.0,
  max: 0.3
};

var veg_vis = {
  min: 0,
  max: 0.8,
  palette: ['#d9c27a', '#b8d16b', '#7fbf7b', '#3a924a', '#005a32']
};

// 8) 将原始影像、NDVI 和 SAVI 添加到地图
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndvi, veg_vis, 'ndvi');
Map.addLayer(savi, veg_vis, 'savi');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);