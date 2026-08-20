// 加载矢量数据（人口老龄化数据）
var feature = ee.FeatureCollection('projects/myData/EasternChina_PopulationAging_Vector');

// 显示矢量数据
Map.addLayer(feature, {color: '000000'}, 'Aging');
Map.setCenter(115, 31, 4);

// 注意：GEE 中没有直接对应的 ACF 计算函数
// 需要手动实现自相关函数计算
// 以下为 ACF 计算的简化实现示例

// 获取特征集合中的属性值
var values = feature.aggregate_array('aging');

// 计算自相关函数（ACF）
// 这里使用一个简单的示例函数来计算不同滞后阶数的自相关
function calculateACF(values, maxLag) {
  var n = values.size();
  var mean = values.reduce(ee.Reducer.mean());
  
  // 计算方差
  var variance = values.map(function(v) {
    return ee.Number(v).subtract(mean).pow(2);
  }).reduce(ee.Reducer.mean());
  
  // 计算不同滞后阶数的自相关系数
  var acfValues = ee.List.sequence(0, maxLag).map(function(lag) {
    var lagNum = ee.Number(lag);
    var nLag = n.subtract(lagNum);
    
    // 计算滞后协方差
    var covariance = ee.List.sequence(0, nLag.subtract(1)).map(function(i) {
      var iNum = ee.Number(i);
      var v1 = values.get(iNum);
      var v2 = values.get(iNum.add(lagNum));
      return ee.Number(v1).subtract(mean).multiply(ee.Number(v2).subtract(mean));
    }).reduce(ee.Reducer.mean());
    
    // 自相关系数 = 协方差 / 方差
    return covariance.divide(variance);
  });
  
  return acfValues;
}

// 计算前10阶自相关系数
var acfResult = calculateACF(values, 10);
print('ACF values:', acfResult);