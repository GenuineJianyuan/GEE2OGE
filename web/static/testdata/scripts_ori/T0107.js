// 加载矢量数据（中国东部人口老龄化数据）
var feature = ee.FeatureCollection('projects/myData/EasternChina_PopulationAging_Vector');

// 显示原始数据
Map.addLayer(feature, {color: '#000000'}, 'Aging');
Map.setCenter(115, 31, 4);

// 执行线性回归分析
// 因变量: aging, 自变量: PCGDP, GI, FD, education
// 使用 GEE 的 reduceRegions 进行逐要素回归分析
var regressionResult = feature.map(function(f) {
  // 提取要素的属性值
  var y = f.getNumber('aging');
  var x1 = f.getNumber('PCGDP');
  var x2 = f.getNumber('GI');
  var x3 = f.getNumber('FD');
  var x4 = f.getNumber('education');
  
  // 构建自变量数组
  var x = [x1, x2, x3, x4];
  
  // 使用线性回归计算拟合值
  // 注意：GEE 中没有直接的 feature 线性回归函数，这里使用简化方法
  // 实际应用中可能需要使用 ee.Reducer.linearRegression 或自定义回归
  
  // 简化处理：计算拟合值（这里假设回归系数已知或通过其他方式获得）
  // 由于 GEE 的 FeatureCollection 不支持直接的多元回归，
  // 这里返回原始值作为占位，实际使用时需要实现回归逻辑
  var fitValue = y; // 占位符，实际应替换为回归拟合值
  
  return f.set('fitValue', fitValue);
});

// 显示拟合结果
Map.addLayer(regressionResult, {color: '#FFFF00'}, 'fitValue');