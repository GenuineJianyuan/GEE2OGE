// 加载中国东部地区老龄化矢量数据
var feature = ee.FeatureCollection('projects/your-project/assets/EasternChina_PopulationAging_Vector');

// 设置地图中心
Map.setCenter(115, 31, 4);

// 计算描述性统计
var desc = feature.reduceColumns({
  reducer: ee.Reducer.minMax().combine(ee.Reducer.mean(), '', true).combine(ee.Reducer.stdDev(), '', true),
  selectors: ['aging', 'FD', 'education', 'sci_tech', 'revenue', 'expand', 'unemployed']
});
print('Descriptive Statistics:', desc);

// 计算相关系数矩阵
var corr = ee.FeatureCollection(feature.reduceColumns({
  reducer: ee.Reducer.pearsonCorrelation(),
  selectors: ['aging', 'FD', 'education', 'sci_tech', 'revenue', 'expand', 'unemployed']
}).get('array'));

// 打印相关系数矩阵
print('Correlation Matrix:', corr);