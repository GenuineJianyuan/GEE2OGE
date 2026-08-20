// 加载矢量数据
var feature = ee.FeatureCollection('projects/your-project/assets/EasternChina_PopulationAging_Vector');

// 显示矢量数据
Map.addLayer(feature, {color: '#000000'}, 'Aging');
Map.setCenter(115, 31, 4);

// 计算平均最近邻指数
var ann = feature.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.euclidean(1000)  // 需要根据数据范围调整搜索半径
});

// 打印结果
print('Average Nearest Neighbor Analysis:', ann);