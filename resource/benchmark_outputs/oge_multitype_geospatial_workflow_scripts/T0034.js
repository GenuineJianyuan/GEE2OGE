// =========================
// 1. 定义两景 ALOS DEM 覆盖范围
// =========================
var dem1_region = ee.Geometry.Rectangle([110.0, 30.0, 111.0, 31.0]);
var dem2_region = ee.Geometry.Rectangle([111.0, 30.0, 112.0, 31.0]);
var study_area = ee.Geometry.Rectangle([110.0, 30.0, 112.0, 31.0]);

// GEE 中以 ALOS AW3D30 DSM 作为 ALOS DEM12.5 的可用近似数据源。
var alos_dem_collection = ee.ImageCollection('JAXA/ALOS/AW3D30/V3_2');

var dem1 = alos_dem_collection
  .filterBounds(dem1_region)
  .select('DSM')
  .mosaic()
  .clip(dem1_region);

var dem2 = alos_dem_collection
  .filterBounds(dem2_region)
  .select('DSM')
  .mosaic()
  .clip(dem2_region);

// =========================
// 2. 合并并镶嵌为连续 DEM
// =========================
var dem_collection = ee.ImageCollection.fromImages([dem1, dem2]);

var dem_mosaic = dem_collection
  .mosaic()
  .clip(study_area)
  .rename('elevation');

// =========================
// 3. 计算坡度
// GEE Terrain.slope 输出单位为度
// =========================
var slope = ee.Terrain.slope(dem_mosaic).rename('slope');

// =========================
// 4. 高程分带
// 0-300m   -> 1 低位带
// 300-800m -> 2 中位带
// 800m+    -> 3 高位带
// =========================
var NaN_value = 0;

var elev_rules = [
  [0.0, 300.0, 1.0],
  [300.0, 800.0, 2.0],
  [800.0, 5000.0, 3.0]
];

var elev_class = dem_mosaic.expression(
  '(elevation >= 0 && elevation < 300) ? 1' +
  ': (elevation >= 300 && elevation < 800) ? 2' +
  ': (elevation >= 800 && elevation <= 5000) ? 3' +
  ': 0',
  {'elevation': dem_mosaic}
).updateMask(dem_mosaic.mask()).toByte().rename('elev_class');

// =========================
// 5. 坡度分级
// 0-8°   -> 1 平缓坡
// 8-20°  -> 2 起伏坡
// 20-90° -> 3 陡坡
// =========================
var slope_rules = [
  [0.0, 8.0, 1.0],
  [8.0, 20.0, 2.0],
  [20.0, 90.0, 3.0]
];

var slope_class = slope.expression(
  '(slope >= 0 && slope < 8) ? 1' +
  ': (slope >= 8 && slope < 20) ? 2' +
  ': (slope >= 20 && slope <= 90) ? 3' +
  ': 0',
  {'slope': slope}
).updateMask(slope.mask()).toByte().rename('slope_class');

// =========================
// 6. 联合编码
// 联合编码 = 高程类别 * 10 + 坡度类别
// =========================
var elev_class_x10 = elev_class.multiply(10).rename('elev_class_x10');
var combined_class = elev_class_x10.add(slope_class).rename('combined_class');

// =========================
// 7. 归并为 4 类基础地形层次带
// =========================
var terrain_rules = [
  [10.5, 11.5, 1.0],
  [11.5, 13.5, 2.0],
  [20.5, 21.5, 2.0],
  [21.5, 23.5, 3.0],
  [30.5, 31.5, 3.0],
  [31.5, 33.5, 4.0]
];

var terrain_band = combined_class.expression(
  '(combined == 11) ? 1' +
  ': (combined == 12 || combined == 13 || combined == 21) ? 2' +
  ': (combined == 22 || combined == 23 || combined == 31) ? 3' +
  ': (combined == 32 || combined == 33) ? 4' +
  ': 0',
  {'combined': combined_class}
).updateMask(combined_class.mask()).toByte().rename('terrain_band');

// =========================
// 8. 轻量整理最终层次带结果
// 使用 focalMode 减少局部碎斑
// =========================
var terrain_band_smooth = terrain_band
  .focalMode({
    radius: 1,
    kernelType: 'circle',
    units: 'pixels',
    iterations: 1
  })
  .rename('terrain_band_smooth');

// =========================
// 9. 可视化
// =========================
var dem_vis = {
  min: 0,
  max: 3000,
  palette: [
    '#1a1a1a', '#4d4d4d', '#808080',
    '#b3b3b3', '#d9d9d9', '#f2f2f2'
  ]
};

var slope_vis = {
  min: 1,
  max: 3,
  palette: [
    '#d9f0d3',
    '#fdae61',
    '#d73027'
  ]
};

var terrain_vis = {
  min: 1,
  max: 4,
  palette: [
    '#d9f0d3',
    '#fee08b',
    '#f46d43',
    '#a50026'
  ]
};

Map.addLayer(dem_mosaic, dem_vis, 'DEM参考图层');
Map.addLayer(slope_class, slope_vis, '坡度分级结果');
Map.addLayer(terrain_band_smooth, terrain_vis, '基础地形层次分带');

Map.setCenter(111.0, 30.5, 9);