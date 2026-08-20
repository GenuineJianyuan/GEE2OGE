// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// 选择 B8 波段（全色波段）作为原始显示
var original_display = ls8.select('B8');

// 方案 A：先平滑降噪，再提取线状细节
// A1: 使用 3x3 方形均值滤波平滑噪声
var chain_a_smooth = original_display.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// A2: 使用 Prewitt 核进行卷积，提取边缘/线状特征
var kernel_a = ee.Kernel.prewitt({magnitude: 0.5});
var chain_a_stage = chain_a_smooth.convolve(kernel_a);

// A3: 使用圆形中值滤波去除卷积后的椒盐噪声
var chain_a_final = chain_a_stage.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 方案 B：先提取局部边界和纹理，再规整画面
// B1: 使用圆形中值滤波保留边缘信息
var chain_b_smooth = original_display.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// B2: 使用 Laplacian4 核进行卷积，提取局部边界和纹理
var kernel_b = ee.Kernel.laplacian4();
var chain_b_stage = chain_b_smooth.convolve(kernel_b);

// B3: 使用方形均值滤波平滑结果，规整画面
var chain_b_final = chain_b_stage.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
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
Map.addLayer(original_display, original_vis, '原始影像 (B8)');
Map.addLayer(chain_a_stage, enhance_vis, '方案A-中间结果 (Prewitt卷积)');
Map.addLayer(chain_a_final, enhance_vis, '方案A-最终结果 (中值滤波后)');
Map.addLayer(chain_b_stage, enhance_vis, '方案B-中间结果 (Laplacian卷积)');
Map.addLayer(chain_b_final, enhance_vis, '方案B-最终结果 (均值滤波后)');

// 设置地图中心点和缩放级别
Map.setCenter(114.30, 30.61, 10);