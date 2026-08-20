// 加载中国东部地区老龄化数据（示例：使用GEE公共数据集或用户上传的资产）
// 注意：原始OGE代码使用矢量数据，GEE中需要先加载为FeatureCollection
var feature = ee.FeatureCollection('users/your_username/EasternChina_PopulationAging_Vector');

Map.setCenter(115, 31, 4);

var vis_params = {
  palette: ['#ffffcc', '#ffeda0', '#fed976', '#feb24c',
            '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026']
};

// 计算老龄化率的局部莫兰指数
// GEE中没有直接的局部莫兰指数计算函数，需要手动实现
// 这里使用邻域统计方法近似实现
var aging = feature.select('aging');

// 创建邻域权重（使用距离权重）
var distanceBand = ee.Image.constant(1).rename('constant').clip(feature);
var kernel = ee.Kernel.gaussian(50, 50, 'meters');

// 计算局部均值
var localMean = aging.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: kernel
});

// 计算全局均值
var globalMean = aging.reduceColumns({
  reducer: ee.Reducer.mean(),
  selectors: ['aging']
}).getNumber('mean');

// 计算局部莫兰指数（简化版）
var re_lisa = aging.subtract(globalMean)
  .multiply(localMean.subtract(globalMean))
  .rename('local_moranI');

// 计算人均GDP的局部加权平均（GWAverage）
// 使用高斯核进行局部加权平均
var pcgdp = feature.select('PCGDP');
var re_gwss = pcgdp.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.gaussian(50, 50, 'meters')
}).rename('PCGDP_LM');

// 将矢量结果栅格化（使用reduceToImage）
var rast_lisa = re_lisa.reduceToImage({
  properties: ['local_moranI'],
  reducer: ee.Reducer.first()
});

var rast_gwss = re_gwss.reduceToImage({
  properties: ['PCGDP_LM'],
  reducer: ee.Reducer.first()
});

// 添加图层到地图
Map.addLayer(rast_lisa, vis_params, 'LISA结果');
Map.addLayer(rast_gwss, vis_params, '人均GDP局部统计背景');