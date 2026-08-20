// 宜昌附近坡面基础属性类型识别
// 基于ALOS PALSAR DEM数据

// 加载相邻DEM数据（覆盖宜昌区域）
var dem1 = ee.Image('JAXA/ALOS/AW3D30_V1_1').select('DSM');
var dem2 = ee.Image('JAXA/ALOS/AW3D30_V1_1').select('DSM');

// 合并DEM数据
var dem_collection = ee.ImageCollection([dem1, dem2]);
var dem_mosaic = dem_collection.mosaic();

// 计算坡度（度）
var slope = ee.Terrain.slope(dem_mosaic);

// 计算坡向（度）
var aspect = ee.Terrain.aspect(dem_mosaic);

// 定义无效值
var NaN_value = 0;

// 坡度分级规则：
// 1 - 平缓坡面 (0-5度)
// 2 - 缓坡 (5-20度)
// 3 - 陡坡 (20-90度)
var slope_class = slope
  .where(slope.gte(0).and(slope.lt(5)), 1)
  .where(slope.gte(5).and(slope.lt(20)), 2)
  .where(slope.gte(20).and(slope.lte(90)), 3)
  .where(slope.lt(0), NaN_value);

// 坡向分组规则：
// 1 - 北向 (0-45度, 315-360度)
// 2 - 东向 (45-135度)
// 3 - 南向 (135-225度)
// 4 - 西向 (225-315度)
var aspect_group = aspect
  .where(aspect.gte(0).and(aspect.lt(45)), 1)
  .where(aspect.gte(45).and(aspect.lt(135)), 2)
  .where(aspect.gte(135).and(aspect.lt(225)), 3)
  .where(aspect.gte(225).and(aspect.lt(315)), 4)
  .where(aspect.gte(315).and(aspect.lte(360)), 1)
  .where(aspect.lt(0), NaN_value);

// 组合编码：坡度代码*10 + 坡向代码
var slope_code = slope_class.multiply(10);
var combined_class = slope_code.add(aspect_group);

// 最终分类规则：
// 1 - 平缓坡面 (坡度<5度)
// 2 - 北向缓坡 (5-20度, 北向)
// 3 - 东向缓坡 (5-20度, 东向)
// 4 - 南向缓坡 (5-20度, 南向)
// 5 - 西向缓坡 (5-20度, 西向)
// 6 - 北向陡坡 (>20度, 北向)
// 7 - 东向陡坡 (>20度, 东向)
// 8 - 南向陡坡 (>20度, 南向)
// 9 - 西向陡坡 (>20度, 西向)
var slope_aspect_type = combined_class
  .where(combined_class.gte(10.5).and(combined_class.lte(14.5)), 1)
  .where(combined_class.gte(20.5).and(combined_class.lte(21.5)), 2)
  .where(combined_class.gte(21.5).and(combined_class.lte(22.5)), 3)
  .where(combined_class.gte(22.5).and(combined_class.lte(23.5)), 4)
  .where(combined_class.gte(23.5).and(combined_class.lte(24.5)), 5)
  .where(combined_class.gte(30.5).and(combined_class.lte(31.5)), 6)
  .where(combined_class.gte(31.5).and(combined_class.lte(32.5)), 7)
  .where(combined_class.gte(32.5).and(combined_class.lte(33.5)), 8)
  .where(combined_class.gte(33.5).and(combined_class.lte(34.5)), 9)
  .where(combined_class.lt(10.5), NaN_value);

// 使用众数滤波进行平滑处理
var slope_aspect_type_smooth = slope_aspect_type
  .reduceNeighborhood({
    reducer: ee.Reducer.mode(),
    kernel: ee.Kernel.circle({radius: 1, units: 'pixels'})
  });

// 可视化参数
var slope_vis = {
  min: 1,
  max: 3,
  palette: ['#d9f0d3', '#fdae61', '#d73027']
};

var aspect_vis = {
  min: 1,
  max: 4,
  palette: ['#4575b4', '#fee090', '#f46d43', '#8073ac']
};

var type_vis = {
  min: 1,
  max: 9,
  palette: [
    '#e0e0e0', '#91bfdb', '#fee090', '#fc8d59', '#998ec3',
    '#2166ac', '#fddbc7', '#b2182b', '#542788'
  ]
};

// 添加图层到地图
Map.addLayer(slope_class, slope_vis, '坡度分级结果');
Map.addLayer(aspect_group, aspect_vis, '坡向方向组结果');
Map.addLayer(slope_aspect_type_smooth, type_vis, '坡面基础属性类型图');

// 设置地图中心
Map.setCenter(111.0, 30.5, 9);