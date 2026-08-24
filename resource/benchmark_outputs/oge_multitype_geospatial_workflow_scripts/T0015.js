// 读取单景 Landsat 8 Collection 2 TOA 影像
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122038_20151002');

// 1) 提取更适合看细节的输入层：全色波段 B8
var original_display = ls8.select(['B8']);

// 2) 保留原始输入作为基准版本
// original_display 直接作为基准版本使用

// 邻域核：半径 1 像元
var squareKernel = ee.Kernel.square({
  radius: 1,
  units: 'pixels',
  normalize: false
});

var circleKernel = ee.Kernel.circle({
  radius: 1,
  units: 'pixels',
  normalize: false
});

// 3) 构建处理链 A：先做轻度平滑降噪
var chain_a_smooth = original_display.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: squareKernel
});

// 4) 链 A：使用 Prewitt 算子提取线状细节
var kernel_a = ee.Kernel.prewitt();
var chain_a_stage = chain_a_smooth.convolve(kernel_a);

// 5) 链 A：再做一次中值滤波整理画面
var chain_a_final = chain_a_stage.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: circleKernel
});

// 6) 构建处理链 B：先做中值滤波邻域优化
var chain_b_smooth = original_display.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: circleKernel
});

// 7) 链 B：使用四邻域 Laplacian 算子增强局部边界和纹理
var kernel_b = ee.Kernel.laplacian4();
var chain_b_stage = chain_b_smooth.convolve(kernel_b);

// 8) 链 B：再进行均值滤波，使画面更规整
var chain_b_final = chain_b_stage.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: squareKernel
});

// Collection 2 TOA 数据的 B8 反射率通常约为 0~1，
// 因此将原 OGE DN 范围调整为适用于 TOA 数据的显示范围。
var original_vis = {
  min: 0,
  max: 0.3,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

var enhance_vis = {
  min: -0.1,
  max: 0.1,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 9) 将原始结果、两套处理中间结果和最终结果添加到地图对照
Map.addLayer(original_display, original_vis, 'original_display');
Map.addLayer(chain_a_stage, enhance_vis, 'chain_a_stage');
Map.addLayer(chain_a_final, enhance_vis, 'chain_a_final');
Map.addLayer(chain_b_stage, enhance_vis, 'chain_b_stage');
Map.addLayer(chain_b_final, enhance_vis, 'chain_b_final');

// 设置地图中心
Map.setCenter(115.74080156644999, 31.7318082104, 11);