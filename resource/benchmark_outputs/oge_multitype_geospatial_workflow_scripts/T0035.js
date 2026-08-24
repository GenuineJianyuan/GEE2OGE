// =========================
// 初始化与研究区
// =========================
var region = ee.Geometry.Rectangle([110, 30, 112, 31]);

// =========================
// 1. 读取两景 ALOS DEM
// GEE 中使用最接近的 JAXA ALOS AW3D30 DSM 数据集
// =========================
var dem_source = ee.ImageCollection('JAXA/ALOS/AW3D30/V3_2');

var dem1 = ee.Image(
  dem_source
    .filter(ee.Filter.eq('system:index', 'N030E110'))
    .first()
).select('DSM').rename('elevation');

var dem2 = ee.Image(
  dem_source
    .filter(ee.Filter.eq('system:index', 'N030E111'))
    .first()
).select('DSM').rename('elevation');

// =========================
// 2. 合并并镶嵌
// =========================
var dem_collection = ee.ImageCollection.fromImages([dem1, dem2]);
var dem_mosaic = dem_collection.mosaic().clip(region);

// =========================
// 3. 计算坡度与坡向
// ee.Terrain 输出的坡度和坡向单位均为度
// =========================
var slope = ee.Terrain.slope(dem_mosaic).rename('slope');
var aspect = ee.Terrain.aspect(dem_mosaic).rename('aspect');

// =========================
// 4. 坡度分级
// 1: 平缓坡面  0-5
// 2: 缓坡      5-20
// 3: 陡坡      20-90
// =========================
var slope_class = ee.Image(0)
  .updateMask(slope.mask())
  .where(slope.gte(0).and(slope.lt(5)), 1)
  .where(slope.gte(5).and(slope.lt(20)), 2)
  .where(slope.gte(20).and(slope.lte(90)), 3)
  .rename('slope_class')
  .toByte();

// =========================
// 5. 坡向方向分组
// 1: 北向坡  (0-45, 315-360)
// 2: 东向坡  (45-135)
// 3: 南向坡  (135-225)
// 4: 西向坡  (225-315)
// =========================
var aspect_group = ee.Image(0)
  .updateMask(aspect.mask())
  .where(aspect.gte(0).and(aspect.lt(45)), 1)
  .where(aspect.gte(45).and(aspect.lt(135)), 2)
  .where(aspect.gte(135).and(aspect.lt(225)), 3)
  .where(aspect.gte(225).and(aspect.lt(315)), 4)
  .where(aspect.gte(315).and(aspect.lte(360)), 1)
  .rename('aspect_group')
  .toByte();

// =========================
// 6. 联合编码
// 联合编码 = 坡度类别 * 10 + 坡向类别
// =========================
var slope_code = slope_class.multiply(10).rename('slope_code');
var combined_class = slope_code.add(aspect_group).rename('combined_class');

// =========================
// 7. 归并为最终坡面属性类型
// 1: 平缓坡面
// 2: 缓北向坡
// 3: 缓东向坡
// 4: 缓南向坡
// 5: 缓西向坡
// 6: 陡北向坡
// 7: 陡东向坡
// 8: 陡南向坡
// 9: 陡西向坡
// =========================
var slope_aspect_type = ee.Image(0)
  .updateMask(combined_class.mask())
  .where(combined_class.gte(11).and(combined_class.lte(14)), 1)
  .where(combined_class.eq(21), 2)
  .where(combined_class.eq(22), 3)
  .where(combined_class.eq(23), 4)
  .where(combined_class.eq(24), 5)
  .where(combined_class.eq(31), 6)
  .where(combined_class.eq(32), 7)
  .where(combined_class.eq(33), 8)
  .where(combined_class.eq(34), 9)
  .rename('slope_aspect_type')
  .toByte();

// =========================
// 8. 轻量碎斑整理
// 对最终分类结果进行半径 1 像元的圆形邻域众数滤波
// =========================
var slope_aspect_type_smooth = slope_aspect_type
  .focalMode({
    radius: 1,
    kernelType: 'circle',
    units: 'pixels'
  })
  .rename('slope_aspect_type_smooth');

// =========================
// 9. 可视化
// =========================
var slope_vis = {
  min: 1,
  max: 3,
  palette: [
    '#d9f0d3',
    '#fdae61',
    '#d73027'
  ]
};

var aspect_vis = {
  min: 1,
  max: 4,
  palette: [
    '#4575b4',
    '#fee090',
    '#f46d43',
    '#8073ac'
  ]
};

var type_vis = {
  min: 1,
  max: 9,
  palette: [
    '#e0e0e0',
    '#91bfdb',
    '#fee090',
    '#fc8d59',
    '#998ec3',
    '#2166ac',
    '#fddbc7',
    '#b2182b',
    '#542788'
  ]
};

Map.addLayer(slope_class, slope_vis, '坡度分级结果');
Map.addLayer(aspect_group, aspect_vis, '坡向方向组结果');
Map.addLayer(slope_aspect_type_smooth, type_vis, '坡面基础属性类型图');

Map.setCenter(111.0, 30.5, 9);