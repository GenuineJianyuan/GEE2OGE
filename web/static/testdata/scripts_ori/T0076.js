// 加载道路和交通设施数据
var road_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2023');
var trans_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 定义核心区和外围区几何
var core_geom = ee.Geometry.Polygon([
  [114.18, 30.53], [114.18, 30.66], [114.40, 30.66], [114.40, 30.53], [114.18, 30.53]
]);
var outer_geom = ee.Geometry.Polygon([
  [114.00, 30.38], [114.00, 30.82], [114.62, 30.82], [114.62, 30.38], [114.00, 30.38]
]);

// 创建核心区和外围区要素
var core_feature = ee.Feature(core_geom, {name: 'core_area'});
var outer_feature = ee.Feature(outer_geom, {name: 'outer_area'});

var core_fc = ee.FeatureCollection([core_feature]);
var outer_fc = ee.FeatureCollection([outer_feature]);

// 创建过渡区（核心区向外缓冲0.08度）
var transition_buffer_feature = core_feature.buffer(0.08);
var transition_buffer_fc = ee.FeatureCollection([transition_buffer_feature]);

// 过渡区 = 缓冲区域与外围区的交集减去核心区
var transition_clip = transition_buffer_fc.intersection(outer_fc);
var transition_zone = transition_clip.difference(core_fc);

// 外围区 = 外围区减去过渡区
var outer_zone = outer_fc.difference(transition_clip);

// 筛选高等级道路（高速公路和主干道）
var motorway = road_2023.filter(ee.Filter.eq('fclass', 'motorway'));
var primary = road_2023.filter(ee.Filter.eq('fclass', 'primary'));
var road_skeleton = motorway.merge(primary);

// 筛选公交站点和渡口设施
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));
var ferry_terminal = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 各分区内的道路
var road_core = road_skeleton.intersection(core_fc);
var road_transition = road_skeleton.intersection(transition_zone);
var road_outer = road_skeleton.intersection(outer_zone);

// 各分区内的公交站点
var bus_core = bus_stop.intersection(core_fc);
var bus_transition = bus_stop.intersection(transition_zone);
var bus_outer = bus_stop.intersection(outer_zone);

// 各分区内的渡口设施
var ferry_core = ferry_terminal.intersection(core_fc);
var ferry_transition = ferry_terminal.intersection(transition_zone);
var ferry_outer = ferry_terminal.intersection(outer_zone);

// 可视化分区
Map.addLayer(core_fc, {color: '#FFCC00'}, '核心区');
Map.addLayer(transition_zone, {color: '#CCCCCC'}, '过渡区');
Map.addLayer(outer_zone, {color: '#E6E6E6'}, '外围区');

// 可视化各分区内的道路
Map.addLayer(road_core, {color: '#0000FF'}, '核心区内高等级道路');
Map.addLayer(road_transition, {color: '#00AAAA'}, '过渡区内高等级道路');
Map.addLayer(road_outer, {color: '#AA5500'}, '外围区内高等级道路');

// 可视化各分区内的公交站点
Map.addLayer(bus_core, {color: '#FF0000'}, '核心区内公交站点');
Map.addLayer(bus_transition, {color: '#AA00FF'}, '过渡区内公交站点');
Map.addLayer(bus_outer, {color: '#008800'}, '外围区内公交站点');

// 可视化各分区内的渡口设施
Map.addLayer(ferry_core, {color: '#990000'}, '核心区内渡口设施');
Map.addLayer(ferry_transition, {color: '#663399'}, '过渡区内渡口设施');
Map.addLayer(ferry_outer, {color: '#006666'}, '外围区内渡口设施');

// 设置地图中心
Map.setCenter(114.3, 30.6, 11);