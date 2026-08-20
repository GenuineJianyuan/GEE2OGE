// 加载中国东部地区老龄化矢量数据
// 注意：GEE 中需要将本地 GeoJSON 上传为 Asset
var feature = ee.FeatureCollection('projects/your-project/assets/EasternChina_PopulationAging_Vector');

// 设置地图中心
Map.setCenter(115, 31, 4);

// 计算描述性统计
// GEE 中没有直接的 DescriptiveStatistics 进程，使用 reduceColumns 实现
var desc = feature.reduceColumns({
  selectors: ['aging', 'PIP', 'SIP', 'TIP', 'TS'],
  reducers: [
    ee.Reducer.min().setOutputs(['aging_min', 'PIP_min', 'SIP_min', 'TIP_min', 'TS_min']),
    ee.Reducer.max().setOutputs(['aging_max', 'PIP_max', 'SIP_max', 'TIP_max', 'TS_max']),
    ee.Reducer.mean().setOutputs(['aging_mean', 'PIP_mean', 'SIP_mean', 'TIP_mean', 'TS_mean']),
    ee.Reducer.stdDev().setOutputs(['aging_std', 'PIP_std', 'SIP_std', 'TIP_std', 'TS_std'])
  ]
});
print('Descriptive Statistics:', desc);

// 计算相关系数矩阵
// GEE 中没有直接的 corrMat 进程，使用 reduceColumns 和 ee.Reducer.pearsonCorrelation 实现
// 注意：GEE 的 pearsonCorrelation 只能计算两个变量之间的相关系数
// 因此需要分别计算 aging 与其他各指标的相关系数

var corr_aging_PIP = feature.reduceColumns({
  selectors: ['aging', 'PIP'],
  reducers: ee.Reducer.pearsonCorrelation()
});
print('Correlation aging-PIP:', corr_aging_PIP);

var corr_aging_SIP = feature.reduceColumns({
  selectors: ['aging', 'SIP'],
  reducers: ee.Reducer.pearsonCorrelation()
});
print('Correlation aging-SIP:', corr_aging_SIP);

var corr_aging_TIP = feature.reduceColumns({
  selectors: ['aging', 'TIP'],
  reducers: ee.Reducer.pearsonCorrelation()
});
print('Correlation aging-TIP:', corr_aging_TIP);

var corr_aging_TS = feature.reduceColumns({
  selectors: ['aging', 'TS'],
  reducers: ee.Reducer.pearsonCorrelation()
});
print('Correlation aging-TS:', corr_aging_TS);