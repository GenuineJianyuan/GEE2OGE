// 加载 Landsat 8 影像
var landsat = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_127036_20160617');

// 加载 DEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_003');

// 计算 NDVI
var ndvi = landsat.normalizedDifference(['B5', 'B4']).multiply(100.0);

// 将 NDVI 和 DEM 裁剪到共同区域
var ndvi_clip = ndvi.updateMask(dem.mask());
var dem_clip = dem.updateMask(ndvi.mask());

// 计算地形因子
var slope = ee.Terrain.slope(dem_clip);
var aspect = ee.Terrain.aspect(dem_clip);

// 计算局部起伏（使用 5x5 圆形邻域）
var focal_max = dem_clip.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: ee.Kernel.circle(5)
});
var focal_min = dem_clip.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: ee.Kernel.circle(5)
});
var relief = focal_max.subtract(focal_min);

// 重分类函数
function reclassify(image, rules) {
  var classified = ee.Image(0);
  for (var i = 0; i < rules.length; i++) {
    var rule = rules[i];
    classified = classified.where(
      image.gte(rule[0]).and(image.lt(rule[1])), 
      rule[2]
    );
  }
  return classified;
}

// DEM 重分类
var dem_rules = [
  [0, 1000, 1],
  [1000, 1500, 2],
  [1500, 2000, 3],
  [2000, 2500, 4],
  [2500, 5000, 5]
];
var dem_class = reclassify(dem_clip, dem_rules);

// 坡度重分类
var slope_rules = [
  [0, 5, 1],
  [5, 15, 2],
  [15, 25, 3],
  [25, 35, 4],
  [35, 90, 5]
];
var slope_class = reclassify(slope, slope_rules);

// 坡向重分类
var aspect_rules = [
  [0, 45, 1],
  [45, 135, 2],
  [135, 225, 3],
  [225, 315, 4],
  [315, 361, 1]
];
var aspect_class = reclassify(aspect, aspect_rules);

// 局部起伏重分类
var relief_rules = [
  [0, 50, 1],
  [50, 100, 2],
  [100, 200, 3],
  [200, 350, 4],
  [350, 5000, 5]
];
var relief_class = reclassify(relief, relief_rules);

// NDVI 重分类
var ndvi_rules = [
  [-100, 0, 1],
  [0, 20, 2],
  [20, 40, 3],
  [40, 60, 4],
  [60, 100, 5]
];
var ndvi_class = reclassify(ndvi_clip, ndvi_rules);

// 地理探测器函数（简化版）
function geoDetector(y, x) {
  // 计算总体方差
  var y_mean = y.reduceRegion({
    reducer: ee.Reducer.mean(),
    scale: 30,
    maxPixels: 1e9
  }).values().get(0);
  
  var y_var = y.reduceRegion({
    reducer: ee.Reducer.variance(),
    scale: 30,
    maxPixels: 1e9
  }).values().get(0);
  
  // 计算分层方差
  var strata = x.rename('strata');
  var combined = y.addBands(strata);
  
  var strata_vars = combined.reduceRegions({
    collection: strata.rename('strata').selfMask().reduceToVectors({
      geometry: y.geometry(),
      scale: 30,
      geometryType: 'centroid'
    }),
    reducer: ee.Reducer.variance(),
    scale: 30
  });
  
  var strata_var_sum = strata_vars.aggregate_sum('variance');
  
  // 计算 q 统计量
  var q = 1 - (strata_var_sum / (y_var.multiply(ee.Number(y.reduceRegion({
    reducer: ee.Reducer.count(),
    scale: 30,
    maxPixels: 1e9
  }).values().get(0)))));
  
  return q;
}

// 计算各因子的 q 统计量
var q_dem = geoDetector(ndvi_clip, dem_class);
var q_slope = geoDetector(ndvi_clip, slope_class);
var q_aspect = geoDetector(ndvi_clip, aspect_class);
var q_relief = geoDetector(ndvi_clip, relief_class);

// 打印结果
print('高程因子解释结果 (q值):', q_dem);
print('坡度因子解释结果 (q值):', q_slope);
print('坡向因子解释结果 (q值):', q_aspect);
print('局部起伏因子解释结果 (q值):', q_relief);

// 可视化 NDVI 分类结果
var ndvi_vis = {
  min: 1,
  max: 5,
  palette: ['#f7fcf5', '#c7e9c0', '#74c476', '#31a354', '#006d2c']
};
Map.addLayer(ndvi_class, ndvi_vis, '植被状态分布结果');

// 设置地图中心
Map.setCenter(108.43, 33.17, 10);