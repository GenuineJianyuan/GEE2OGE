// 读取单景 Landsat 8 TOA 影像
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122038_20151002');

// 1) 提取目标波段：全色波段 B8
var target_band = ls8.select(['B8']);

// 2) 构建处理链 A：先做轻度平滑降噪
var chain_a_smooth = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1, 'pixels', false)
});

// 3) 在链 A 上执行 Prewitt 卷积增强
// OGE 中的 0.5 按卷积响应增益处理。
var kernel_a = ee.Kernel.prewitt(true, false);
var chain_a_final = chain_a_smooth
  .convolve(kernel_a)
  .multiply(0.5);

// 4) 构建处理链 B：直接执行 Laplacian 结构增强
var kernel_b = ee.Kernel.laplacian4();
var chain_b_enhanced = target_band.convolve(kernel_b);

// 5) 对链 B 结果执行基础后处理
var chain_b_final = chain_b_enhanced.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1, 'pixels', false)
});

// Landsat Collection 2 TOA 数据的反射率通常约为 0～1，
// 因此可视化范围相对于 OGE 原始 DN 范围进行了调整。
var original_vis = {
  min: 0,
  max: 0.3,
  palette: ['1f1f1f', '5a5a5a', '9a9a9a', 'd9d9d9', 'ffffff']
};

var enhance_vis = {
  min: -0.02,
  max: 0.02,
  palette: ['1f1f1f', '5a5a5a', '9a9a9a', 'd9d9d9', 'ffffff']
};

// 6) 将原始全色波段、链 A、链 B 加载到地图进行对照
Map.addLayer(target_band, original_vis, 'original_band');
Map.addLayer(chain_a_final, enhance_vis, 'chain_a_final');
Map.addLayer(chain_b_final, enhance_vis, 'chain_b_final');

// 设置地图中心
Map.setCenter(115.74080156644999, 31.7318082104, 11);