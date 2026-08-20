// 加载武汉市2023年交通数据（假设已上传为GEE资产）
var trans_2023 = ee.FeatureCollection('users/your_username/wuhan_trans_2023');

// 创建主支撑道路骨架线
var skeleton_geom = ee.Geometry.LineString(
    [[114.12, 30.49], [114.28, 30.58], [114.46, 30.70]]);
var skeleton_feature = ee.Feature(skeleton_geom, {name: 'support_skeleton'});

// 创建支撑缓冲区（约800米）
var support_buffer = skeleton_feature.buffer(0.008);
var support_fc = ee.FeatureCollection([support_buffer]);

// 创建研究范围多边形
var study_geom = ee.Geometry.Polygon(
    [[[114.08, 30.44], [114.08, 30.76], [114.52, 30.76], [114.52, 30.44], [114.08, 30.44]]]);
var study_feature = ee.Feature(study_geom, {name: 'study_area'});
var study_fc = ee.FeatureCollection([study_feature]);

// 创建中心区域多边形
var center_geom = ee.Geometry.Polygon(
    [[[114.18, 30.52], [114.18, 30.66], [114.40, 30.66], [114.40, 30.52], [114.18, 30.52]]]);
var center_feature = ee.Feature(center_geom, {name: 'center_zone'});
var center_fc = ee.FeatureCollection([center_feature]);

// 计算外围区域（研究范围减去中心区域）
var outer_zone = study_fc.difference(center_fc);

// 计算偏离主骨架区域（研究范围减去支撑缓冲区）
var off_support_zone = study_fc.difference(support_fc);

// 计算外围且偏离主骨架的区域
var outer_off_support_zone = outer_zone.intersection(off_support_zone);

// 筛选公交站点
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 研究范围内的公交站点
var bus_in_study = bus_stop.filterBounds(study_geom);

// 偏离主骨架的公交站点
var bus_outside_support = bus_stop.filterBounds(off_support_zone);

// 外围异常公交站点
var outer_anomaly_bus = bus_stop.filterBounds(outer_off_support_zone);

// 统计数量
var bus_total_count = bus_in_study.size();
var bus_outside_count = bus_outside_support.size();
var outer_anomaly_count = outer_anomaly_bus.size();

print('公交站点在研究范围内数量:', bus_total_count);
print('偏离主骨架的公交站点数量:', bus_outside_count);
print('外围异常公交站点数量:', outer_anomaly_count);

// 可视化
Map.centerObject(study_fc, 11);
Map.addLayer(skeleton_feature, {color: 'blue'}, '高等级道路骨架');
Map.addLayer(bus_in_study, {color: 'red'}, '研究范围内目标设施');
Map.addLayer(bus_outside_support, {color: 'orange'}, '偏离主骨架的设施');
Map.addLayer(outer_anomaly_bus, {color: 'purple'}, '外围异常设施');