// 加载 Landsat 8 影像（武汉东北部）
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// 选择红、绿、蓝波段
var red_band = ls8.select('B4');
var green_band = ls8.select('B3');
var blue_band = ls8.select('B2');

// 原始自然色合成
var original_display = ls8.select(['B4', 'B3', 'B2']);

// 对绿色波段进行均值滤波（平滑处理）
var smooth_green = green_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 使用 Prewitt 核进行卷积（边缘增强）
var kernel = ee.Kernel.prewitt({magnitude: 0.5});
var enhanced_green = smooth_green.convolve(kernel);

// 将处理后的绿色波段与红、蓝波段重新组合
var optimized_display = red_band.addBands(enhanced_green).addBands(blue_band);

// 可视化参数
var vis_params = {
  min: 0,
  max: 30000
};

// 在地图上显示原始自然色结果
Map.addLayer(original_display, vis_params, '原始自然色');

// 在地图上显示优化后的结果
Map.addLayer(optimized_display, vis_params, '优化结果');

// 设置地图中心点
Map.setCenter(114.30, 30.61, 10);