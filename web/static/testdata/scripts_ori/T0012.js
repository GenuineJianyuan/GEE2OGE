// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 选择 B8 波段（全色波段）
var original_display = ls8.select('B8');

// 方案 A：先平滑（均值滤波），再边缘增强（Prewitt），最后中值滤波
var chain_a_smooth = original_display.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

var kernel_a = ee.Kernel.prewitt({magnitude: 0.5});
var chain_a_stage = chain_a_smooth.convolve(kernel_a);

var chain_a_final = chain_a_stage.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 方案 B：先中值滤波，再拉普拉斯边缘增强，最后均值滤波
var chain_b_smooth = original_display.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

var kernel_b = ee.Kernel.laplacian4();
var chain_b_stage = chain_b_smooth.convolve(kernel_b);

var chain_b_final = chain_b_stage.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 可视化参数
var vis_params = {
  min: 0,
  max: 30000,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 添加图层到地图
Map.addLayer(original_display, vis_params, 'original_display');
Map.addLayer(chain_a_stage, vis_params, 'chain_a_stage');
Map.addLayer(chain_a_final, vis_params, 'chain_a_final');
Map.addLayer(chain_b_stage, vis_params, 'chain_b_stage');
Map.addLayer(chain_b_final, vis_params, 'chain_b_final');

// 设置地图中心
Map.setCenter(114.30, 30.61, 10);