// 加载矢量数据（需先上传至GEE资产）
var feature = ee.FeatureCollection('users/yourusername/EasternChina_PopulationAging_Vector');

// 显示原始数据
Map.addLayer(feature, {color: '#FF00FF'}, 'Aging');
Map.setCenter(115, 31, 4);

// 注意：GEE没有内置GWR功能，以下为模拟实现
// 使用线性回归作为替代（实际GWR需要自定义实现或使用外部工具）

// 准备自变量和因变量
var dependent = 'aging';
var independents = ['PCGDP', 'GI', 'FD', 'education'];

// 提取属性数据并添加坐标
var withCoords = feature.map(function(f) {
  var geom = f.geometry();
  var coords = geom.coordinates();
  return f.set('x', coords.get(0)).set('y', coords.get(1));
});

// 提取数值矩阵
var trainingData = withCoords.select(independents.concat([dependent, 'x', 'y']));

// 使用线性回归作为GWR的近似（实际GWR需要空间权重）
var linearRegression = trainingData.reduceColumns({
  reducer: ee.Reducer.linearRegression({
    numX: independents.length,
    numY: 1
  }),
  selectors: independents.concat([dependent])
});

// 获取回归系数
var coefficients = ee.Array(linearRegression.get('coefficients'));
var offset = ee.Array(linearRegression.get('offset'));

// 计算预测值
var predicted = feature.map(function(f) {
  var values = independents.map(function(varName) {
    return ee.Number(f.get(varName));
  });
  var xArray = ee.Array(values);
  var yhat = xArray.multiply(coefficients).reduce('sum', [0]).add(offset.get([0, 0]));
  return f.set('yhat', yhat);
});

// 栅格化预测结果
var raster = predicted.reduceToImage({
  properties: ['yhat'],
  reducer: ee.Reducer.first()
});

// 可视化参数
var visParams = {
  palette: ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026']
};

// 显示预测结果
Map.addLayer(raster, visParams, 'valuePrediction');