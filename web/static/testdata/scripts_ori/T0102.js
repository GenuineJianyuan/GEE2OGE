// 加载点要素数据（假设为FeatureCollection）
var feature = ee.FeatureCollection('users/your_username/EasternChina_PopulationAging_Vector');

// 在地图上显示点数据
Map.addLayer(feature, {color: '000000'}, 'Aging');
Map.setCenter(115, 31, 4);

// 计算Ripley's K函数（空间聚集性分析）
// GEE中没有直接对应的Ripley's K函数，但可以使用距离直方图或缓冲区分析近似
// 这里使用缓冲区分析来近似空间聚集性
var distances = ee.List.sequence(0, 100000, 10000); // 距离序列（米）

var ripleyK = distances.map(function(d) {
  var buffer = feature.map(function(f) {
    return f.buffer(ee.Number(d));
  });
  
  // 计算每个点的缓冲区内的其他点数
  var counts = feature.map(function(f) {
    var pt = f.geometry();
    var count = buffer.filterBounds(pt.buffer(1)).size();
    return ee.Feature(null, {'count': count});
  });
  
  // 计算平均点数
  var meanCount = counts.reduceColumns(ee.Reducer.mean(), ['count']).get('mean');
  
  // 计算K值：K(d) = (A/n^2) * sum(count_i)
  var area = feature.geometry().bounds().area();
  var n = feature.size();
  var K = area.multiply(meanCount).divide(n.multiply(n));
  
  return ee.Feature(null, {'distance': d, 'K': K});
});

// 输出结果到控制台
print('Ripley\'s K 分析结果:', ripleyK);

// 也可以输出为表格
var resultTable = ee.FeatureCollection(ripleyK);
print('Ripley\'s K 结果表格:', resultTable);