// 加载中国东部地区老龄化数据（假设为FeatureCollection）
var feature = ee.FeatureCollection('projects/your-project/assets/EasternChina_PopulationAging_Vector');

// 地图居中显示
Map.setCenter(115, 31, 4);

// 计算描述性统计
var desc = feature.reduceColumns({
  reducer: ee.Reducer.minMax().combine(ee.Reducer.mean(), null, true)
    .combine(ee.Reducer.stdDev(), null, true)
    .combine(ee.Reducer.median(), null, true),
  selectors: ['aging', 'PCGDP', 'PCD', 'PIP', 'SIP', 'TIP', 'FD', 'education', 'sci_tech', 'revenue', 'unemployed', 'expand']
});
print('Descriptive Statistics:', desc);

// 计算候选变量之间的Pearson相关系数矩阵
var corr = feature.reduceColumns({
  reducer: ee.Reducer.pearsonsCorrelation(),
  selectors: ['aging', 'PCGDP', 'PCD', 'PIP', 'SIP', 'TIP', 'FD', 'education', 'sci_tech', 'revenue', 'unemployed', 'expand']
});
print('Correlation Matrix:', corr);