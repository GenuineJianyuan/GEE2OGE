// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// 选择 B3 波段（绿色波段）
var target_band = ls8.select('B3');

// 分支 A：轻度平滑 + Prewitt 边缘增强
var branch_a_smooth = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

var kernel_a = ee.Kernel.prewitt({magnitude: 1.0});
var branch_a_enhanced = branch_a_smooth.convolve(kernel_a);

// 分支 B：重度平滑 + Laplacian 边缘增强
var branch_b_smooth = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(3)
});

var kernel_b = ee.Kernel.laplacian4();
var branch_b_enhanced = branch_b_smooth.convolve(kernel_b);

// 最终处理：中值滤波去噪
var branch_a_final = branch_a_enhanced.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

var branch_b_final = branch_b_enhanced.reduceNeighborhood({
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
Map.addLayer(target_band, original_vis, 'target_band');
Map.addLayer(branch_a_final, enhance_vis, 'branch_a_final');
Map.addLayer(branch_b_final, enhance_vis, 'branch_b_final');

// 设置地图中心
Map.setCenter(114.30, 30.61, 10);