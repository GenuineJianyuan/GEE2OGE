// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 选择绿色波段 (B3)
var target_band = ls8.select('B3');

// 获取原始投影信息
var crs = target_band.projection();
print('target_band_crs', crs);

// 重投影到 EPSG:3857，分辨率 30 米
var standard_band = target_band.reproject({
  crs: 'EPSG:3857',
  scale: 30
});

// 应用中值滤波（圆形核，半径 1 像素）
var final_band = standard_band.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数（灰度渐变）
var vis_params = {
  min: 0,
  max: 0.3,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 添加原始波段到地图
Map.addLayer(target_band, vis_params, 'original_band');

// 添加标准化后的波段到地图
Map.addLayer(final_band, vis_params, 'standardized_band');

// 设置地图中心（武汉东北部）
Map.setCenter(114.30, 30.61, 10);