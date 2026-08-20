// 加载中国东部地区老龄化矢量数据
var feature = ee.FeatureCollection('projects/your-project/assets/EasternChina_PopulationAging_Vector');

// 设置地图中心
Map.setCenter(115, 31, 4);

// 基础全局回归：因变量为aging，自变量为PCGDP和PCD
var baseline_result = feature.reduceColumns({
  reducer: ee.Reducer.linearRegression({
    numX: 2,
    numY: 1
  }),
  selectors: ['PCGDP', 'PCD', 'aging']
});

// 扩展全局回归：因变量为aging，自变量为PCGDP、GI、FD和education
var extended_result = feature.reduceColumns({
  reducer: ee.Reducer.linearRegression({
    numX: 4,
    numY: 1
  }),
  selectors: ['PCGDP', 'GI', 'FD', 'education', 'aging']
});

// 提取回归系数并添加到要素集合中
var baseline_coefs = baseline_result.get('coefficients');
var extended_coefs = extended_result.get('coefficients');

// 创建带回归结果的要素图层
var baseline_layer = feature.map(function(f) {
  return f.set('baseline_coefs', baseline_coefs);
});

var extended_layer = feature.map(function(f) {
  return f.set('extended_coefs', extended_coefs);
});

// 添加图层到地图
Map.addLayer(baseline_layer, {color: '#FFCC00'}, '基础全局回归结果');
Map.addLayer(extended_layer, {color: '#00FFFF'}, '多变量全局回归结果');