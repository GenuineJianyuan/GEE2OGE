// 加载中国东部地区老龄化数据（使用GEE公共数据集或用户上传的资产）
// 注意：原始OGE代码使用的是用户自定义的矢量数据，GEE中需要替换为对应的资产ID
var feature = ee.FeatureCollection('users/your_username/EasternChina_PopulationAging_Vector');

// 设置地图中心点
Map.setCenter(115, 31, 4);

// 执行全局线性回归
// GEE中没有直接的线性回归处理函数，需要使用reduceRegions或自定义方法
// 这里使用ee.Reducer.linearFit()作为替代方案
var regressionResult = feature.map(function(f) {
  // 提取自变量和因变量
  var aging = f.get('aging');
  var pcgdp = f.get('PCGDP');
  var pcd = f.get('PCD');
  
  // 构建回归所需的数组
  var x = ee.Array([pcgdp, pcd]);
  var y = ee.Array([aging]);
  
  // 使用线性拟合（简化版，实际需要更复杂的回归计算）
  // 这里仅作为示例，实际应用中可能需要使用ee.Reducer.linearRegression()
  var fit = ee.Array.cat([x, y], 1).reduce(ee.Reducer.linearFit(), [0]);
  
  return f.set({
    'regression_coefficients': fit,
    'regression_residual': aging - (pcgdp * fit.get(0) + pcd * fit.get(1))
  });
});

// 可视化回归结果
Map.addLayer(regressionResult, {color: '#FFFF00'}, '全局回归结果');