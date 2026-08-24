// =========================
// 1. 读取宜昌附近单景 ALOS DEM
// =========================
// GEE 中没有与 OGE ALOS_PALSAR_DEM12.5 完全一致的 12.5 m 数据集，
// 此处使用可用的 ALOS AW3D30 DSM（约 30 m）N030E111 瓦片替代。
var dem = ee.ImageCollection('JAXA/ALOS/AW3D30/V4_1')
  .filter(ee.Filter.eq('system:index', 'N030E111'))
  .select('DSM')
  .mosaic()
  .rename('elevation');

// =========================
// 辅助函数：按区间重分类
// 区间采用 [min, max)；本例中的输入值均为整数类别编码，边界差异通常不影响结果。
// =========================
function reclass(image, rules) {
  var result = image.multiply(0);

  rules.forEach(function(rule) {
    var minValue = rule[0];
    var maxValue = rule[1];
    var classValue = rule[2];

    var condition = image.gte(minValue).and(image.lt(maxValue));
    result = result.where(condition, classValue);
  });

  return result.updateMask(result.neq(0));
}

// =========================
// 2. DEM轻量平滑
// =========================
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle({
    radius: 3,
    units: 'pixels',
    normalize: true
  })
}).rename('elevation');

// =========================
// 3. 计算局部相对高程
// =========================
var dem_local_mean = dem_base.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle({
    radius: 15,
    units: 'pixels',
    normalize: true
  })
}).rename('local_mean');

var relative_position = dem_base.subtract(dem_local_mean)
  .rename('relative_position');

var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle({
    radius: 1,
    units: 'pixels',
    normalize: true
  })
}).rename('relative_position_smooth');

// =========================
// 4. 计算坡度
// ee.Terrain.slope 输出单位为度。
// =========================
var slope = ee.Terrain.slope(dem_base).rename('slope');

// =========================
// 5. 相对高程位置分层
// =========================
var position_rules = [
  [-5000.0, -15.0, 1.0],
  [-15.0, -5.0, 2.0],
  [-5.0, 5.0, 3.0],
  [5.0, 15.0, 4.0],
  [15.0, 5000.0, 5.0]
];

var position_class = reclass(relative_position_smooth, position_rules)
  .rename('position_class');

// =========================
// 6. 坡度分级
// =========================
var slope_rules = [
  [0.0, 20.0, 1.0],
  [20.0, 35.0, 2.0],
  [35.0, 90.0, 3.0]
];

var slope_class = reclass(slope, slope_rules)
  .rename('slope_class');

// =========================
// 7. 联合编码
// =========================
var position_code = position_class.multiply(10)
  .rename('position_code');

var combined_class = position_code.add(slope_class)
  .rename('combined_class');

// =========================
// 8. 归并为坡位层级带
// 1: 谷底带；2: 下坡带；3: 中坡带；4: 上坡带；5: 脊顶带
// =========================
var slope_position_rules = [
  [10.5, 11.5, 1.0],
  [11.5, 13.5, 2.0],

  [20.5, 23.5, 2.0],
  [30.5, 33.5, 3.0],
  [40.5, 43.5, 4.0],

  [50.5, 52.5, 5.0],
  [52.5, 53.5, 4.0]
];

var slope_position = reclass(combined_class, slope_position_rules)
  .rename('slope_position');

// =========================
// 9. 去碎斑
// =========================
var slope_position_smooth = slope_position.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle({
    radius: 1,
    units: 'pixels',
    normalize: false
  })
}).rename('slope_position_smooth');

// =========================
// 10. 可视化
// =========================
var position_vis = {
  min: 1,
  max: 5,
  palette: [
    '#2b83ba',
    '#91bfdb',
    '#ffffbf',
    '#fdae61',
    '#d7191c'
  ]
};

var slope_vis = {
  min: 1,
  max: 3,
  palette: [
    '#fee08b',
    '#f46d43',
    '#a50026'
  ]
};

var slope_position_vis = {
  min: 1,
  max: 5,
  palette: [
    '#2b83ba',
    '#91bfdb',
    '#ffffbf',
    '#fdae61',
    '#d7191c'
  ]
};

Map.addLayer(position_class, position_vis, '相对高程位置分层结果');
Map.addLayer(slope_class, slope_vis, '坡度分级结果');
Map.addLayer(slope_position_smooth, slope_position_vis, '坡位层级分带结果');

Map.setCenter(111.5, 30.5, 10);