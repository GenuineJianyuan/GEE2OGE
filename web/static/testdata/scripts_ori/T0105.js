// 加载矢量数据（需先上传至GEE资产）
var feature = ee.FeatureCollection('users/yourusername/EasternChina_PopulationAging_Vector');

// 显示老龄化空间分布
Map.addLayer(feature, {color: '#000000'}, 'Aging');
Map.setCenter(115, 31, 4);

// 注意：GEE没有内置的地理探测器（GeoDetector）算法
// 需要自行实现或使用外部库
// 以下为地理探测器因子探测器的简化实现思路

// 1. 提取属性数据
var attributes = feature.select(['aging', 'PCGDP', 'GI', 'FD', 'education']);

// 2. 定义分层函数（示例：按分位数分层）
function stratify(collection, property, numClasses) {
  var min = collection.aggregate_min(property);
  var max = collection.aggregate_max(property);
  var step = ee.Number(max).subtract(min).divide(numClasses);
  
  return collection.map(function(f) {
    var value = ee.Number(f.get(property));
    var classIndex = value.subtract(min).divide(step).floor().min(numClasses - 1);
    return f.set(property + '_class', classIndex);
  });
}

// 3. 对目标变量和影响因素进行分层
var numClasses = 5;
var stratified = attributes;
['aging', 'PCGDP', 'GI', 'FD', 'education'].forEach(function(prop) {
  stratified = stratify(stratified, prop, numClasses);
});

// 4. 计算q统计量（简化版）
function calculateQ(collection, target, factor) {
  var totalVar = collection.aggregate_sum(
    ee.Reducer.variance(), target
  );
  
  var classVar = collection.select([target, factor + '_class'])
    .reduceColumns(ee.Reducer.sum(), [target, factor + '_class']);
  
  // 实际实现需要按类计算方差并加权求和
  // 此处为示意代码
  
  return ee.Number(1); // 占位返回值
}

// 5. 计算各因素的解释力
var factors = ['PCGDP', 'GI', 'FD', 'education'];
var results = factors.map(function(f) {
  var q = calculateQ(stratified, 'aging', f);
  return ee.Feature(null, {factor: f, q_statistic: q});
});

// 6. 输出结果
print('地理探测器因子探测结果：', ee.FeatureCollection(results));