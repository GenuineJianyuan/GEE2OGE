// 加载中国东部地区老龄化矢量数据
var feature = ee.FeatureCollection('projects/your-project/assets/EasternChina_PopulationAging_Vector');

// 设置地图中心点
Map.setCenter(115, 31, 4);

// 计算老龄化率的局部莫兰指数
var lisaResult = feature.map(function(f) {
  // 获取当前要素的几何和属性
  var geom = f.geometry();
  var aging = f.getNumber('aging');
  
  // 查找空间邻域要素（使用缓冲区和空间连接）
  var neighbors = feature.filterBounds(geom.buffer(50000)); // 50km缓冲区作为邻域
  
  // 计算邻域要素的权重（使用反距离权重）
  var weights = neighbors.map(function(n) {
    var dist = geom.distance(n.geometry());
    var weight = ee.Number(1).divide(dist.add(1)); // 反距离权重
    return n.set('weight', weight);
  });
  
  // 计算邻域老龄化率的加权平均
  var sumWeight = weights.aggregate_sum('weight');
  var sumWeightedAging = weights.reduceColumns({
    reducer: ee.Reducer.sum(),
    selectors: ['aging', 'weight']
  }).get('sum');
  
  // 计算全局均值
  var globalMean = feature.aggregate_mean('aging');
  
  // 计算局部莫兰指数（简化版）
  var localMoran = ee.Number(aging).subtract(globalMean)
    .multiply(ee.Number(sumWeightedAging).divide(sumWeight));
  
  return f.set('LISA', localMoran);
});

// 添加图层到地图
Map.addLayer(lisaResult, {palette: ['#FFFF00']}, 'LISA结果');