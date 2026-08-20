// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 选择 B8 波段（全色波段）
var target_band = ls8.select('B8');

// 版本 A：轻度平滑（3x3 方形均值）
var smooth_a = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 版本 B：重度平滑（7x7 方形均值）
var smooth_b = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(3)
});

// 最终版本 A：轻度平滑 + 圆形中值滤波（半径 1）
var final_a = smooth_a.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 最终版本 B：重度平滑 + 圆形中值滤波（半径 1）
var final_b = smooth_b.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var vis_params = {
  min: 0,
  max: 30000,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 添加图层到地图
Map.addLayer(target_band, vis_params, '原始波段');
Map.addLayer(final_a, vis_params, '版本 A（轻度平滑）');
Map.addLayer(final_b, vis_params, '版本 B（重度平滑）');

// 设置地图中心
Map.setCenter(114.30, 30.61, 10);