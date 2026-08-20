// 加载 Landsat 9 Collection 2 Level-2 影像
var landsat = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_115028_20230116');

// 加载 DEM 数据 (ASTER GDEM)
var dem = ee.Image('NASA/ASTER_GED/AG100_v003');

// 定义无效值
var NaN_value = 0;

// 选择绿色波段和短波红外波段
var green = landsat.select('SR_B3');
var swir1 = landsat.select('SR_B6');

// 转换为浮点型并应用缩放因子
var green = green.toDouble().multiply(0.0000275).add(-0.2);
var swir1 = swir1.toDouble().multiply(0.0000275).add(-0.2);

// 计算 NDSI (归一化差分积雪指数)
var ndsi_num = green.subtract(swir1);
var ndsi_den = green.add(swir1);
var ndsi = ndsi_num.divide(ndsi_den);

// 缩放 NDSI 到 0-100 范围
var ndsi_scaled = ndsi.multiply(100.0);

// 裁剪到 DEM 范围
var ndsi_clip = ndsi_scaled.updateMask(dem.mask());
var dem_clip = dem.updateMask(ndsi_clip.mask());

// 计算地形因子
var slope = ee.Terrain.slope(dem_clip);
var aspect = ee.Terrain.aspect(dem_clip);

// 计算相对地形位置 (TPI)
var dem_local_mean = dem_clip.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(9)
});
var relative_position = dem_clip.subtract(dem_local_mean);
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle(1)
});

// 重分类函数
function reclassify(image, rules, noDataValue) {
  var classified = ee.Image(noDataValue);
  for (var i = 0; i < rules.length; i++) {
    var min = rules[i][0];
    var max = rules[i][1];
    var value = rules[i][2];
    classified = classified.where(image.gte(min).and(image.lt(max)), value);
  }
  return classified;
}

// 高程重分类
var dem_rules = [
  [0.0, 300.0, 1.0],
  [300.0, 500.0, 2.0],
  [500.0, 700.0, 3.0],
  [700.0, 900.0, 4.0],
  [900.0, 5000.0, 5.0]
];
var dem_class = reclassify(dem_clip, dem_rules, NaN_value);

// 坡度重分类
var slope_rules = [
  [0.0, 5.0, 1.0],
  [5.0, 15.0, 2.0],
  [15.0, 25.0, 3.0],
  [25.0, 35.0, 4.0],
  [35.0, 90.0, 5.0]
];
var slope_class = reclassify(slope, slope_rules, NaN_value);

// 坡向重分类
var aspect_rules = [
  [0.0, 45.0, 1.0],
  [45.0, 135.0, 2.0],
  [135.0, 225.0, 3.0],
  [225.0, 315.0, 4.0],
  [315.0, 361.0, 1.0]
];
var aspect_class = reclassify(aspect, aspect_rules, NaN_value);

// 相对地形位置重分类
var position_rules = [
  [-5000.0, -20.0, 1.0],
  [-20.0, -5.0, 2.0],
  [-5.0, 5.0, 3.0],
  [5.0, 20.0, 4.0],
  [20.0, 5000.0, 5.0]
];
var position_class = reclassify(relative_position_smooth, position_rules, NaN_value);

// NDSI 重分类
var ndsi_rules = [
  [-100.0, 10.0, 1.0],
  [10.0, 40.0, 2.0],
  [40.0, 100.0, 3.0]
];
var ndsi_class = reclassify(ndsi_clip, ndsi_rules, NaN_value);

// 定义积雪范围
var snow_min = -100.0;
var snow_max = 100.0;

// 地理探测器函数 (简化版)
function geoDetector(response, explanatory, strata, minVal, maxVal) {
  // 计算总体方差
  var overallMean = response.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: response.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).values().get(0);
  
  var overallVariance = response.reduceRegion({
    reducer: ee.Reducer.variance(),
    geometry: response.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).values().get(0);
  
  // 计算分层方差
  var strataValues = strata.reduceRegion({
    reducer: ee.Reducer.toList(),
    geometry: response.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).values().get(0);
  
  var uniqueStrata = ee.List(strataValues).distinct();
  
  var strataVarianceSum = uniqueStrata.map(function(s) {
    var mask = strata.eq(ee.Number(s));
    var strataResponse = response.updateMask(mask);
    var count = strataResponse.reduceRegion({
      reducer: ee.Reducer.count(),
      geometry: response.geometry(),
      scale: 30,
      maxPixels: 1e9
    }).values().get(0);
    var variance = strataResponse.reduceRegion({
      reducer: ee.Reducer.variance(),
      geometry: response.geometry(),
      scale: 30,
      maxPixels: 1e9
    }).values().get(0);
    return ee.Number(count).multiply(ee.Number(variance));
  }).reduce(ee.Reducer.sum());
  
  // 计算 q 统计量
  var totalCount = response.reduceRegion({
    reducer: ee.Reducer.count(),
    geometry: response.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).values().get(0);
  
  var q = ee.Number(1).subtract(
    ee.Number(strataVarianceSum).divide(
      ee.Number(totalCount).multiply(ee.Number(overallVariance))
    )
  );
  
  return q;
}

// 计算各因子的 q 统计量
var geo_res_dem = geoDetector(ndsi_clip, dem_class, dem_class, snow_min, snow_max);
var geo_res_slope = geoDetector(ndsi_clip, slope_class, slope_class, snow_min, snow_max);
var geo_res_aspect = geoDetector(ndsi_clip, aspect_class, aspect_class, snow_min, snow_max);
var geo_res_position = geoDetector(ndsi_clip, position_class, position_class, snow_min, snow_max);

// 识别积雪敏感地形带
var elev_sensitive = reclassify(dem_class, [[-0.5, 3.5, 0.0], [3.5, 5.5, 1.0]], NaN_value);
var aspect_sensitive = reclassify(aspect_class, [[0.5, 1.5, 1.0], [1.5, 4.5, 0.0]], NaN_value);
var slope_sensitive = reclassify(slope_class, [[-0.5, 0.5, 0.0], [0.5, 3.5, 1.0], [3.5, 5.5, 0.0]], NaN_value);

var tmp_sensitive = elev_sensitive.add(aspect_sensitive);
var snow_sensitive_score = tmp_sensitive.add(slope_sensitive);
var snow_sensitive_band = reclassify(snow_sensitive_score, [[-0.5, 2.5, 0.0], [2.5, 3.5, 1.0]], NaN_value);

// 可视化参数
var ndsi_vis = {
  min: 1,
  max: 3,
  palette: ['#f0f0f0', '#9ecae1', '#2171b5']
};

var sensitive_vis = {
  min: 0,
  max: 1,
  palette: ['#d9d9d9', '#d73027']
};

// 添加图层到地图
Map.addLayer(ndsi_class, ndsi_vis, '积雪分布结果');
Map.addLayer(snow_sensitive_band, sensitive_vis, '积雪敏感地形带结果');

// 输出地理探测器结果
print('高程因子积雪解释结果:', geo_res_dem);
print('坡度因子积雪解释结果:', geo_res_slope);
print('坡向因子积雪解释结果:', geo_res_aspect);
print('相对地形位置因子积雪解释结果:', geo_res_position);

// 设置地图中心
Map.setCenter(130.5, 45.5, 10);