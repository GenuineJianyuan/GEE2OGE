// 加载中国东部城市人口老龄化数据（示例：使用模拟数据，实际需替换为真实数据集）
var feature = ee.FeatureCollection('FAO/GAUL/2015/level2')
  .filterBounds(ee.Geometry.Rectangle([110, 20, 125, 40])); // 中国东部范围

// 添加模拟老龄化字段（实际应用中需从真实数据源获取）
feature = feature.map(function(f) {
  return f.set('aging', ee.Number.parse(f.get('POP2000')).multiply(0.1));
});

// 添加模拟影响因素字段
feature = feature.map(function(f) {
  return f.set('PCGDP', ee.Number.parse(f.get('POP2000')).multiply(0.05))
    .set('GI', ee.Number.parse(f.get('POP2000')).multiply(0.03))
    .set('FD', ee.Number.parse(f.get('POP2000')).multiply(0.02))
    .set('TS', ee.Number.parse(f.get('POP2000')).multiply(0.04))
    .set('CL', ee.Number.parse(f.get('POP2000')).multiply(0.06))
    .set('PCD', ee.Number.parse(f.get('POP2000')).multiply(0.07))
    .set('PIP', ee.Number.parse(f.get('POP2000')).multiply(0.08))
    .set('SIP', ee.Number.parse(f.get('POP2000')).multiply(0.09))
    .set('TIP', ee.Number.parse(f.get('POP2000')).multiply(0.1))
    .set('education', ee.Number.parse(f.get('POP2000')).multiply(0.11));
});

// 可视化参数
var vis_params = {
  palette: ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026']
};

// 显示老龄化率
Map.centerObject(feature, 4);
Map.addLayer(feature, {color: '#FF7744'}, '东部城市人口老龄化率');

// 全局莫兰指数（GEE 无直接实现，需自定义计算）
// 注意：GEE 没有内置空间自相关分析，以下为示意代码
var morani = feature.reduceColumns({
  reducer: ee.Reducer.mean(),
  selectors: ['aging']
});
print('全局莫兰指数（示意）:', morani);

// 局部莫兰指数（LISA）- GEE 无直接实现，需自定义
// 以下为示意代码，实际需使用邻域计算
var re_lisa = feature.map(function(f) {
  var neighbors = feature.filterBounds(f.geometry().buffer(50000));
  var localMoran = neighbors.reduceColumns({
    reducer: ee.Reducer.mean(),
    selectors: ['aging']
  });
  return f.set('local_moranI', localMoran.get('mean'));
});

// 地理加权平均（GWA）- GEE 无直接实现，需自定义
var re_gwss = feature.map(function(f) {
  var neighbors = feature.filterBounds(f.geometry().buffer(50000));
  var pcdpMean = neighbors.reduceColumns({
    reducer: ee.Reducer.mean(),
    selectors: ['PCGDP']
  });
  return f.set('PCGDP_LM', pcdpMean.get('mean'));
});

// 显示 LISA 结果（示意）
Map.addLayer(re_lisa, vis_params, 'LISA结果');

// 显示 GWA 结果（示意）
Map.addLayer(re_gwss, vis_params, '人均GDP变量局部地理加权平均值');

// 相关系数矩阵（GEE 无直接实现，需自定义）
var corrVars = ['aging', 'PCGDP', 'GI', 'FD', 'TS', 'CL', 'PCD', 'PIP', 'SIP', 'TIP', 'education'];
var re_corr = feature.reduceColumns({
  reducer: ee.Reducer.pearsonsCorrelation(),
  selectors: corrVars
});
print('相关系数矩阵（示意）:', re_corr);

// 地理探测器因子探测器（GEE 无直接实现，需自定义）
// 以下为示意代码
var re_detect = feature.reduceColumns({
  reducer: ee.Reducer.mean(),
  selectors: ['aging']
});
print('地理探测器因子探测器结果（示意）:', re_detect);

// 线性回归（GEE 支持）
var re_lr = feature.reduceColumns({
  reducer: ee.Reducer.linearRegression(4, 1),
  selectors: ['PCGDP', 'GI', 'FD', 'education', 'aging']
});
print('线性回归结果:', re_lr);

// 空间滞后模型（GEE 无直接实现，需自定义）
// 以下为示意代码
var re_slm = feature.reduceColumns({
  reducer: ee.Reducer.mean(),
  selectors: ['aging']
});
print('空间滞后模型结果（示意）:', re_slm);

// 地理加权回归（GEE 无直接实现，需自定义）
// 以下为示意代码
var re_gwr = feature.map(function(f) {
  var neighbors = feature.filterBounds(f.geometry().buffer(50000));
  var gwrResult = neighbors.reduceColumns({
    reducer: ee.Reducer.linearRegression(4, 1),
    selectors: ['PCGDP', 'GI', 'FD', 'education', 'aging']
  });
  return f.set('gwr_coefficients', gwrResult);
});
print('地理加权回归结果（示意）:', re_gwr);