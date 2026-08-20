// 加载 Landsat 8 影像（武汉市东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 选择全色波段（B8）
var original_display = ls8.select('B8');

// 第一次平滑：3x3 方形均值滤波
var smooth_display_1 = original_display.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 第二次平滑：3x3 圆形中值滤波
var smooth_display_2 = smooth_display_1.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 使用 Prewitt 核进行边缘增强
var kernel = ee.Kernel.prewitt({magnitude: 0.5});
var stage_display = smooth_display_2.convolve(kernel);

// 最终平滑：3x3 圆形中值滤波
var final_display = stage_display.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 原始影像显示参数
var original_vis = {
  min: 0,
  max: 30000,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 增强影像显示参数
var enhance_vis = {
  min: -2000,
  max: 2000,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 添加图层到地图
Map.addLayer(original_display, original_vis, 'original_display');
Map.addLayer(stage_display, enhance_vis, 'stage_display');
Map.addLayer(final_display, enhance_vis, 'final_display');

// 设置地图中心点
Map.setCenter(114.30, 30.61, 10);