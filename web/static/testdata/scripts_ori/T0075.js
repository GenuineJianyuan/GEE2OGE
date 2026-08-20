// 加载武汉市2023年道路和交通设施数据
var road_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2023');
var trans_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 构造两个部分重叠的分析区
var zone_a_geom = ee.Geometry.Polygon([
  [114.08, 30.48], [114.08, 30.72], [114.36, 30.72], [114.36, 30.48], [114.08, 30.48]
]);
var zone_b_geom = ee.Geometry.Polygon([
  [114.24, 30.44], [114.24, 30.68], [114.56, 30.68], [114.56, 30.44], [114.24, 30.44]
]);

// 创建区域要素和要素集合
var zone_a_feature = ee.Feature(zone_a_geom, {name: 'zone_a'});
var zone_b_feature = ee.Feature(zone_b_geom, {name: 'zone_b'});

var zone_a_fc = ee.FeatureCollection([zone_a_feature]);
var zone_b_fc = ee.FeatureCollection([zone_b_feature]);

// 计算共享区和独有区
var shared_zone = zone_a_fc.intersection(zone_b_fc);
var zone_a_only = zone_a_fc.difference(zone_b_fc);
var zone_b_only = zone_b_fc.difference(zone_a_fc);

// 筛选高等级道路（高速公路和主干道）
var motorway = road_2023.filter(ee.Filter.eq('fclass', 'motorway'));
var primary = road_2023.filter(ee.Filter.eq('fclass', 'primary'));
var road_skeleton = motorway.merge(primary);

// 筛选渡口设施
var ferry_terminal = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 提取各区域内的高等级道路
var road_shared = road_skeleton.intersection(shared_zone);
var road_a_only = road_skeleton.intersection(zone_a_only);
var road_b_only = road_skeleton.intersection(zone_b_only);

// 提取各区域内的渡口设施
var ferry_shared = ferry_terminal.intersection(shared_zone);
var ferry_a_only = ferry_terminal.intersection(zone_a_only);
var ferry_b_only = ferry_terminal.intersection(zone_b_only);

// 可视化区域
Map.addLayer(shared_zone, {color: '#FFCC00'}, '重叠共享区');
Map.addLayer(zone_a_only, {color: '#66CCFF'}, 'A独有区');
Map.addLayer(zone_b_only, {color: '#CCCCCC'}, 'B独有区');

// 可视化高等级道路
Map.addLayer(road_shared, {color: '#0000FF'}, '共享区内高等级道路');
Map.addLayer(road_a_only, {color: '#00AAAA'}, 'A独有区内高等级道路');
Map.addLayer(road_b_only, {color: '#AA5500'}, 'B独有区内高等级道路');

// 可视化渡口设施
Map.addLayer(ferry_shared, {color: '#FF0000'}, '共享区内渡口设施');
Map.addLayer(ferry_a_only, {color: '#AA00FF'}, 'A独有区内渡口设施');
Map.addLayer(ferry_b_only, {color: '#008800'}, 'B独有区内渡口设施');

// 设置地图中心
Map.setCenter(114.3, 30.58, 11);