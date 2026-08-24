// 初始化并读取 Landsat 9 Collection 2 Level-2 Surface Reflectance 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306')
  .select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6'])
  // Landsat Collection 2 Level-2 SR 缩放系数与偏移量。
  .multiply(0.0000275)
  .add(-0.2);

// 1) 提取原始影像显示层
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 2) 提取经验表达所需波段
var red_band = lc09.select(['SR_B4']);
var nir_band = lc09.select(['SR_B5']);
var swir1_band = lc09.select(['SR_B6']);

// 3) 转换为浮点型
red_band = red_band.toFloat();
nir_band = nir_band.toFloat();
swir1_band = swir1_band.toFloat();

// 4) 计算植被相关指数 NDVI = (NIR - Red) / (NIR + Red)
var ndvi_num = nir_band.subtract(red_band);
var ndvi_den = nir_band.add(red_band);
var ndvi = ndvi_num.divide(ndvi_den).rename('NDVI');

// 5) 计算水分相关指数 NDMI = (NIR - SWIR1) / (NIR + SWIR1)
var ndmi_num = nir_band.subtract(swir1_band);
var ndmi_den = nir_band.add(swir1_band);
var ndmi = ndmi_num.divide(ndmi_den).rename('NDMI');

// 6) 构建经验型可燃物湿度表达
// 先把 NDVI 和 NDMI 归一到约 0~1，再组合成经验型湿度表达。
var ndvi_norm = ndvi.add(1.0);
ndvi_norm = ndvi_norm.divide(2.0);

var ndmi_norm = ndmi.add(1.0);
ndmi_norm = ndmi_norm.divide(2.0);

var fuel_moisture_proxy = ndvi_norm.multiply(ndmi_norm)
  .rename('fuel_moisture_proxy');

// 7) 用植被阈值压掉明显非植被区，减少裸地干扰
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gt(20);

fuel_moisture_proxy = fuel_moisture_proxy.multiply(vegetation_mask)
  .rename('fuel_moisture_proxy');

// 8) 对结果做统一整理：1 像元半径圆形邻域均值滤波
fuel_moisture_proxy = fuel_moisture_proxy.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle({
    radius: 1,
    units: 'pixels',
    normalize: false
  })
}).rename('fuel_moisture_proxy');

// 可视化参数
var original_vis = {};

var ndvi_vis = {
  min: -0.1,
  max: 0.5,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#d9f0d3', '#7fbf7b', '#1b7837']
};

var ndmi_vis = {
  min: -0.2,
  max: 0.3,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

var fuel_vis = {
  min: 0.0,
  max: 0.6,
  palette: ['#8c510a', '#d8b365', '#f6e8c3', '#c7eae5', '#5ab4ac', '#01665e']
};

// 9) 组织原始影像、中间结果和最终结果的对照结构
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndvi, ndvi_vis, 'ndvi');
Map.addLayer(ndmi, ndmi_vis, 'ndmi');
Map.addLayer(fuel_moisture_proxy, fuel_vis, 'fuel_moisture_proxy');

// 设置地图中心
Map.setCenter(115.35899045035, 30.296925757799997, 11);