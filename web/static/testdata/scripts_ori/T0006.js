// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 选择绿色波段 (B3)
var target_band = ls8.select('B3');

// 原始波段
var original_band = target_band;

// 处理链 A：先轻度平滑，再用 Prewitt 提取边缘，最后中值滤波
var chain_a_smooth = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

var kernel_a = ee.Kernel.prewitt({magnitude: 0.5});
var chain_a_intermediate = chain_a_smooth.convolve(kernel_a);

var chain_a_final = chain_a_intermediate.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 处理链 B：先较强平滑，再用 Laplacian 提取细节，最后中值滤波
var chain_b_smooth = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(3)
});

var kernel_b = ee.Kernel.laplacian4();
var chain_b_intermediate = chain_b_smooth.convolve(kernel_b);

var chain_b_final = chain_b_intermediate.reduceNeighborhood({
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
Map.addLayer(original_band, original_vis, 'original_band');
Map.addLayer(chain_a_intermediate, enhance_vis, 'chain_a_intermediate');
Map.addLayer(chain_b_intermediate, enhance_vis, 'chain_b_intermediate');
Map.addLayer(chain_a_final, enhance_vis, 'chain_a_final');
Map.addLayer(chain_b_final, enhance_vis, 'chain_b_final');

// 设置地图中心
Map.setCenter(114.30, 30.61, 10);