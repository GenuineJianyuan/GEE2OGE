// 加载 Landsat 8 影像
var landsat8 = ee.Image('LANDSAT/LC08/C02/T1_L2/LC08_144030_20230831');

// 计算 NDVI
var ndvi = landsat8.normalizedDifference(['SR_B5', 'SR_B4']).multiply(100);

// 加载 DEM 数据
var dem = ee.Image('NASA/ASTER_GED/AG100_003');

// 将 NDVI 和 DEM 裁剪到共同区域
var ndvi_clip = ndvi.clip(dem.geometry());
var dem_clip = dem.clip(ndvi.geometry());

// 计算坡度和坡向
var slope = ee.Terrain.slope(dem_clip);
var aspect = ee.Terrain.aspect(dem_clip);

// 定义重分类函数
function reclassify(image, thresholds, values) {
  var reclassified = ee.Image(0);
  for (var i = 0; i < thresholds.length; i++) {
    var mask = image.gte(thresholds[i][0]).and(image.lt(thresholds[i][1]));
    reclassified = reclassified.where(mask, values[i]);
  }
  return reclassified;
}

// 重分类 DEM
var dem_reclass = reclassify(dem_clip, 
  [[500, 1500], [1500, 2500], [2500, 3000], [3000, 3500], [3500, 4500]], 
  [1, 2, 3, 4, 5]);

// 重分类坡度
var slope_reclass = reclassify(slope, 
  [[0, 5], [5, 15], [15, 25], [25, 35], [35, 45], [45, 90]], 
  [1, 2, 3, 4, 5, 6]);

// 重分类坡向
var aspect_reclass = reclassify(aspect, 
  [[0, 60], [60, 120], [120, 180], [180, 240], [240, 300], [300, 360]], 
  [1, 2, 3, 4, 5, 6]);

// 重分类 NDVI
var ndvi_reclass = reclassify(ndvi_clip, 
  [[-50, 0], [0, 10], [10, 20], [20, 30], [30, 40], [40, 50]], 
  [1, 2, 3, 4, 5, 6]);

// 显示重分类 NDVI
Map.addLayer(ndvi_reclass, {min: 1, max: 6, palette: ['red', 'orange', 'yellow', 'green', 'darkgreen', 'darkblue']}, '重分类NDVI数据');

// 定义地理探测器函数
function geoDetector(y, x, strata) {
  // 计算总体方差
  var y_mean = y.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: y.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).getNumber('nd');
  
  var y_var = y.reduceRegion({
    reducer: ee.Reducer.variance(),
    geometry: y.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).getNumber('nd');
  
  // 计算分层方差
  var strata_values = ee.List([1, 2, 3, 4, 5, 6]);
  
  var strata_vars = strata_values.map(function(v) {
    var mask = strata.eq(ee.Number(v));
    var y_strata = y.updateMask(mask);
    var count = y_strata.reduceRegion({
      reducer: ee.Reducer.count(),
      geometry: y.geometry(),
      scale: 30,
      maxPixels: 1e9
    }).getNumber('nd');
    
    var var_strata = y_strata.reduceRegion({
      reducer: ee.Reducer.variance(),
      geometry: y.geometry(),
      scale: 30,
      maxPixels: 1e9
    }).getNumber('nd');
    
    return ee.Feature(null, {
      'count': count,
      'variance': var_strata
    });
  });
  
  var strata_vars_fc = ee.FeatureCollection(strata_vars);
  
  // 计算 q 统计量
  var total_count = y.reduceRegion({
    reducer: ee.Reducer.count(),
    geometry: y.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).getNumber('nd');
  
  var sum_strata_var = strata_vars_fc.reduceColumns({
    reducer: ee.Reducer.sum(),
    selectors: ['variance']
  }).getNumber('sum');
  
  var q = ee.Number(1).subtract(sum_strata_var.divide(y_var));
  
  return ee.Dictionary({
    'q_statistic': q,
    'total_variance': y_var,
    'strata_variance_sum': sum_strata_var
  });
}

// 计算各因子的地理探测器结果
var geo_res_dem = geoDetector(ndvi_clip, dem_clip, dem_reclass);
var geo_res_slope = geoDetector(ndvi_clip, slope, slope_reclass);
var geo_res_aspect = geoDetector(ndvi_clip, aspect, aspect_reclass);
var geo_res_ndvi = geoDetector(ndvi_clip, ndvi_clip, ndvi_reclass);

// 输出结果
print('高程因子计算结果:', geo_res_dem);
print('坡度因子计算结果:', geo_res_slope);
print('坡向因子计算结果:', geo_res_aspect);
print('NDVI因子（对照组）计算结果:', geo_res_ndvi);

// 设置地图中心
Map.setCenter(85.22, 43.16, 10);