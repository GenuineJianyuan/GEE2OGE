// 加载武汉市2023年公交站点数据
var trans_2023 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2023');

// 筛选公交站点
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 定义两条支撑骨架线
var support_a_geom = ee.Geometry.LineString([[114.10, 30.46], [114.28, 30.58], [114.50, 30.72]]);
var support_b_geom = ee.Geometry.LineString([[114.02, 30.68], [114.26, 30.60], [114.54, 30.48]]);

// 创建支撑骨架要素
var support_a_feature = ee.Feature(support_a_geom, {name: 'support_a'});
var support_b_feature = ee.Feature(support_b_geom, {name: 'support_b'});

// 创建缓冲区（约1公里）
var support_a_buffer = support_a_feature.buffer(1000); // 约0.01度≈1km
var support_b_buffer = support_b_feature.buffer(1000);

// 创建要素集合
var support_a_fc = ee.FeatureCollection([support_a_buffer]);
var support_b_fc = ee.FeatureCollection([support_b_buffer]);

// 计算共享区和独立区
var shared_zone = support_a_fc.intersection(support_b_fc);
var a_only_zone = support_a_fc.difference(support_b_fc);
var b_only_zone = support_b_fc.difference(support_a_fc);

// 定义研究范围
var study_geom = ee.Geometry.Polygon([[[113.98, 30.40], [113.98, 30.80], [114.62, 30.80], [114.62, 30.40], [113.98, 30.40]]]);
var study_fc = ee.FeatureCollection([ee.Feature(study_geom, {name: 'study_area'})]);

// 计算远离区（研究范围内减去两个缓冲区）
var study_minus_a = study_fc.difference(support_a_fc);
var far_zone = study_minus_a.difference(support_b_fc);

// 统计各区域公交站数量
var bus_a_only = bus_stop.filterBounds(a_only_zone);
var bus_b_only = bus_stop.filterBounds(b_only_zone);
var bus_shared = bus_stop.filterBounds(shared_zone);
var bus_far = bus_stop.filterBounds(far_zone);

var bus_a_only_count = bus_a_only.size();
var bus_b_only_count = bus_b_only.size();
var bus_shared_count = bus_shared.size();
var bus_far_count = bus_far.size();

// 打印统计结果
print('A侧独立区公交站数量:', bus_a_only_count);
print('B侧独立区公交站数量:', bus_b_only_count);
print('共享区公交站数量:', bus_shared_count);
print('远离区公交站数量:', bus_far_count);

// 可视化
Map.centerObject(study_fc, 11);

// 支撑骨架线
Map.addLayer(support_a_feature, {color: '#0000FF'}, '支撑骨架A');
Map.addLayer(support_b_feature, {color: '#0088FF'}, '支撑骨架B');

// 四类分区
Map.addLayer(a_only_zone, {color: '#FFCC00'}, 'A侧归属带');
Map.addLayer(b_only_zone, {color: '#99CC00'}, 'B侧归属带');
Map.addLayer(shared_zone, {color: '#FFA500'}, '双支撑共享区');
Map.addLayer(far_zone, {color: '#CCCCCC'}, '双支撑外远离区');

// 公交站点分布
Map.addLayer(bus_a_only, {color: '#FF0000'}, 'A侧归属公交站');
Map.addLayer(bus_b_only, {color: '#8000FF'}, 'B侧归属公交站');
Map.addLayer(bus_shared, {color: '#00AA88'}, '共享区公交站');
Map.addLayer(bus_far, {color: '#444444'}, '远离区公交站');