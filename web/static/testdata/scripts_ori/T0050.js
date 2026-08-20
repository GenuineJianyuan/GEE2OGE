// Landsat 地表温度与地形因子热环境分析
// 基于 Landsat 地表温度波段构建热环境结果，并结合 DEM 派生的地形因子进行分析

// 加载 Landsat 8 Collection 2 Level 2 地表温度数据
var landsat_l2 = ee.Image('LANDSAT/LC08/C02/T1_L2/LC08_126037_20230513');

// 加载 ALOS PALSAR DEM 数据
var dem = ee.Image('JAXA/ALOS/AW3D30/V2_2');

// 定义无效值
var NaN_value = 0;

// 选择地表温度波段并转换为双精度
var st_b10 = landsat_l2.select('ST_B10').toDouble();

// 应用缩放因子和偏移量计算开尔文温度
var lst_k = st_b10.multiply(0.00341802).add(149.0);

// 转换为摄氏度
var lst_c = lst_k.subtract(273.15);

// 裁剪 LST 和 DEM 到共同范围
var lst_clip = lst_c.clip(dem.geometry());
var dem_clip = dem.clip(lst_clip.geometry());

// 计算坡度（度）
var slope = ee.Terrain.slope(dem_clip);

// 计算坡向（度）
var aspect = ee.Terrain.aspect(dem_clip);

// 计算局部起伏（5x5 圆形邻域）
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
function reclassify(image, rules, noDataValue) {
  var classified = ee.Image(noDataValue).rename('class');
  for (var i = 0; i < rules.length; i++) {
    var rule = rules[i];
    var mask = image.gte(rule[0]).and(image.lt(rule[1]));
    classified = classified.where(mask, rule[2]);
  }
  return classified;
}

// 高程重分类
var dem_rules = [
  [0.0, 800.0, 1.0],
  [800.0, 1200.0, 2.0],
  [1200.0, 1600.0, 3.0],
  [1600.0, 2200.0, 4.0],
  [2200.0, 5000.0, 5.0]
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

// 局部起伏重分类
var relief_rules = [
  [0.0, 40.0, 1.0],
  [40.0, 80.0, 2.0],
  [80.0, 150.0, 3.0],
  [150.0, 250.0, 4.0],
  [250.0, 5000.0, 5.0]
];
var relief_class = reclassify(relief, relief_rules, NaN_value);

// LST 重分类
var lst_rules = [
  [-50.0, 18.0, 1.0],
  [18.0, 22.0, 2.0],
  [22.0, 26.0, 3.0],
  [26.0, 30.0, 4.0],
  [30.0, 60.0, 5.0]
];
var lst_class = reclassify(lst_clip, lst_rules, NaN_value);

// 定义 LST 范围
var lst_min = -50.0;
var lst_max = 60.0;

// 地理探测器函数（简化版）
function geoDetector(yImage, xImage, yMin, yMax, noDataValue) {
  // 计算总方差
  var yMean = yImage.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: yImage.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).getNumber('ST_B10');
  
  var totalVariance = yImage.subtract(yMean).pow(2).reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: yImage.geometry(),
    scale: 30,
    maxPixels: 1e9
  }).getNumber('ST_B10');
  
  // 计算层内方差
  var strata = xImage.rename('strata');
  var combined = yImage.addBands(strata);
  
  var strataMeans = combined.reduceRegions({
    collection: strata.rename('strata').reduceToVectors({
      geometry: yImage.geometry(),
      scale: 30,
      geometryType: 'polygon',
      eightConnected: false
    }),
    reducer: ee.Reducer.mean(),
    scale: 30
  });
  
  var withinVariance = strataMeans.aggregate_sum('sum');
  
  // 计算 q 统计量
  var q = 1 - (withinVariance.divide(totalVariance));
  
  return ee.Feature(null, {q_statistic: q});
}

// 计算各因子的地理探测器结果
var geo_res_dem = geoDetector(lst_clip, dem_class, lst_min, lst_max, NaN_value);
var geo_res_slope = geoDetector(lst_clip, slope_class, lst_min, lst_max, NaN_value);
var geo_res_aspect = geoDetector(lst_clip, aspect_class, lst_min, lst_max, NaN_value);
var geo_res_relief = geoDetector(lst_clip, relief_class, lst_min, lst_max, NaN_value);

// 可视化参数
var lst_vis = {
  min: 1,
  max: 5,
  palette: ['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c']
};

// 添加图层到地图
Map.addLayer(lst_class, lst_vis, '地表热环境分布结果');

// 打印地理探测器结果
print('高程因子热环境解释结果:', geo_res_dem);
print('坡度因子热环境解释结果:', geo_res_slope);
print('坡向因子热环境解释结果:', geo_res_aspect);
print('局部起伏因子热环境解释结果:', geo_res_relief);

// 设置地图中心
Map.setCenter(109.5, 33.5, 10);