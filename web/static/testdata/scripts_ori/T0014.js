// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151003');

// 选择全色波段 B8
var target_band = ls8.select('B8');

// 链 A：先平滑再提取边缘（Prewitt）
var chain_a_smooth = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

var kernel_a = ee.Kernel.prewitt({magnitude: 0.5});
var chain_a_final = chain_a_smooth.convolve(kernel_a);

// 链 B：先提取边缘（Laplacian）再中值滤波
var kernel_b = ee.Kernel.laplacian4();
var chain_b_enhanced = target_band.convolve(kernel_b);

var chain_b_final = chain_b_enhanced.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数
var original_vis = {
  min: 0,
  max: 30000,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

var enhance_vis = {
  min: -2000,
  max: 2000,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 添加图层到地图
Map.addLayer(target_band, original_vis, '原始全色波段');
Map.addLayer(chain_a_final, enhance_vis, '链A：平滑+边缘提取');
Map.addLayer(chain_b_final, enhance_vis, '链B：边缘提取+中值滤波');

// 设置地图中心（武汉东北部）
Map.setCenter(114.30, 30.61, 10);