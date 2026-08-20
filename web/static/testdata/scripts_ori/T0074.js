// 加载武汉市2023年道路和交通设施数据
var road_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2023');
var trans_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 构造核心区几何
var core_geom = ee.Geometry.Polygon([
  [114.18, 30.53], [114.18, 30.67], [114.42, 30.67], [114.42, 30.53], [114.18, 30.53]
]);

// 构造外围区几何
var outer_geom = ee.Geometry.Polygon([
  [114.02, 30.40], [114.02, 30.80], [114.60, 30.80], [114.60, 30.40], [114.02, 30.40]
]);

// 创建核心区和外围区要素
var core_feature = ee.Feature(core_geom, {name: 'core_area'});
var outer_feature = ee.Feature(outer_geom, {name: 'outer_area'});

// 创建要素集合
var core_fc = ee.FeatureCollection([core_feature]);
var outer_fc = ee.FeatureCollection([outer_feature]);

// 计算外围区独立范围（外围区减去核心区）
var outer_only = outer_fc.difference(core_fc);

// 提取核心区内道路
var road_in_core = road_2023.filterBounds(core_geom);

// 提取外围区内道路（使用外围区独立范围）
var road_in_outer = road_2023.filterBounds(outer_only.geometry());

// 筛选公交站点
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 提取核心区内公交站点
var bus_in_core = bus_stop.filterBounds(core_geom);

// 提取外围区内公交站点
var bus_in_outer = bus_stop.filterBounds(outer_only.geometry());

// 可视化设置
Map.centerObject(core_fc, 11);

// 添加图层
Map.addLayer(core_fc, {color: '#FFCC00'}, '核心区');
Map.addLayer(outer_only, {color: '#CCCCCC'}, '外围区');
Map.addLayer(road_in_core, {color: '#0000FF'}, '核心区内道路');
Map.addLayer(road_in_outer, {color: '#00AAAA'}, '外围区内道路');
Map.addLayer(bus_in_core, {color: '#FF0000'}, '核心区内公交站点');
Map.addLayer(bus_in_outer, {color: '#AA00FF'}, '外围区内公交站点');