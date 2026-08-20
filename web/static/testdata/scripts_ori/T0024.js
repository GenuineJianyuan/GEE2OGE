// 加载 Landsat 9 Collection 2 Level 2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LANDSAT_LC09_122039_20230306');

// 选择 RGB 波段用于真彩色显示
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// 选择计算植被指数和水分指数所需的波段
var red_band = lc09.select('SR_B4').toFloat();
var nir_band = lc09.select('SR_B5').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();

// 计算 NDVI（归一化植被指数）
var ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band));

// 计算 NDMI（归一化水分指数）
var ndmi = nir_band.subtract(swir1_band).divide(nir_band.add(swir1_band));

// 将 NDVI 和 NDMI 归一化到 [0, 1] 范围
var ndvi_norm = ndvi.add(1.0).divide(2.0);
var ndmi_norm = ndmi.add(1.0).divide(2.0);

// 计算经验型可燃物湿度代理指数
var fuel_moisture_proxy = ndvi_norm.multiply(ndmi_norm);

// 创建植被掩膜（NDVI > 0.2 的区域）
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gt(20);

// 应用植被掩膜
fuel_moisture_proxy = fuel_moisture_proxy.multiply(vegetation_mask);

// 使用中值滤波平滑结果
fuel_moisture_proxy = fuel_moisture_proxy.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// 可视化参数设置
var original_vis = {
  bands: ['SR_B4', 'SR_B3', 'SR_B2'],
  min: 7000,
  max: 12000
};

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

// 添加图层到地图
Map.addLayer(original_image, original_vis, '原始影像');
Map.addLayer(ndvi, ndvi_vis, 'NDVI 植被指数');
Map.addLayer(ndmi, ndmi_vis, 'NDMI 水分指数');
Map.addLayer(fuel_moisture_proxy, fuel_vis, '可燃物湿度代理指数');

// 设置地图中心点（湖北东部）
Map.setCenter(115.35899045035, 30.296925757799997, 11);