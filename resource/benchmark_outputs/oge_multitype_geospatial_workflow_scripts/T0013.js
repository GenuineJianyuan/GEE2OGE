// 读取单景 Landsat 8 Collection 2 TOA 影像
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122038_20151002');

// 1) 提取目标波段：全色波段 B8
var target_band = ls8.select(['B8']);

// 2) 使用参数方案 A 执行平滑处理（较轻）
var smooth_a = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square({radius: 1, units: 'pixels', normalize: false})
});

// 3) 使用参数方案 B 执行平滑处理（较强）
var smooth_b = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square({radius: 3, units: 'pixels', normalize: false})
});

// 4) 对方案 A 结果执行统一的基础后处理
var final_a = smooth_a.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle({radius: 1, units: 'pixels', normalize: false})
});

// 5) 对方案 B 结果执行统一的基础后处理
var final_b = smooth_b.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle({radius: 1, units: 'pixels', normalize: false})
});

// LANDSAT/LC08/C02/T1_TOA 的 B8 是 TOA 反射率，通常约为 0~1。
var vis_params = {
  min: 0,
  max: 0.6,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 6) 组织原始波段、方案 A、方案 B 的对照图层
Map.addLayer(target_band, vis_params, 'original_band', true);
Map.addLayer(final_a, vis_params, 'version_a', false);
Map.addLayer(final_b, vis_params, 'version_b', false);

// ==================== 原始代码中的第二套显示/增强流程 ====================

// 1) 提取目标显示层
var original_display = ls8.select(['B8']);

// 2) 第一次平滑降噪
var smooth_display_1 = original_display.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square({radius: 1, units: 'pixels', normalize: false})
});

// 3) 第二次邻域优化处理
var smooth_display_2 = smooth_display_1.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle({radius: 1, units: 'pixels', normalize: false})
});

// 4) 细节增强，作为阶段性结果
var kernel = ee.Kernel.prewitt(true, 0.5);
var stage_display = smooth_display_2.convolve(kernel);

// 5) 对增强结果再做一次轻度整理，压一压毛躁感
var final_display = stage_display.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle({radius: 1, units: 'pixels', normalize: false})
});

var original_vis = {
  min: 0,
  max: 0.6,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

var enhance_vis = {
  min: -0.04,
  max: 0.04,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 原始结果、中间增强结果和最终增强结果对照展示
Map.addLayer(original_display, original_vis, 'original_display', false);
Map.addLayer(stage_display, enhance_vis, 'stage_display', false);
Map.addLayer(final_display, enhance_vis, 'final_display', false);

// 设置地图中心
Map.setCenter(115.74080156644999, 31.7318082104, 11);