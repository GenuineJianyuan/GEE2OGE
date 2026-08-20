// 加载武汉市2023年交通设施数据
var trans_2023 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2023');

// 构造支撑骨架线
var skeleton_geom = ee.Geometry.LineString([
  [114.12, 30.49], 
  [114.28, 30.58], 
  [114.46, 30.70]
]);

var skeleton_feature = ee.Feature(skeleton_geom, {name: 'support_skeleton'});

// 创建三个距离缓冲区
var near_buffer = skeleton_feature.buffer(0.003);
var mid_total_buffer = skeleton_feature.buffer(0.008);
var far_total_buffer = skeleton_feature.buffer(0.015);

// 转换为FeatureCollection
var near_fc = ee.FeatureCollection([near_buffer]);
var mid_total_fc = ee.FeatureCollection([mid_total_buffer]);
var far_total_fc = ee.FeatureCollection([far_total_buffer]);

// 计算中距离和远距离的环形缓冲区
var mid_fc = mid_total_fc.difference(near_fc);
var far_fc = far_total_fc.difference(mid_total_fc);

// 筛选公交站点
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 筛选渡口设施
var ferry_terminal = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 统计各层级公交站点数量
var bus_near = bus_stop.filterBounds(near_fc);
var bus_mid = bus_stop.filterBounds(mid_fc);
var bus_far = bus_stop.filterBounds(far_fc);

var bus_near_count = bus_near.size();
var bus_mid_count = bus_mid.size();
var bus_far_count = bus_far.size();

// 统计各层级渡口设施数量
var ferry_near = ferry_terminal.filterBounds(near_fc);
var ferry_mid = ferry_terminal.filterBounds(mid_fc);
var ferry_far = ferry_terminal.filterBounds(far_fc);

var ferry_near_count = ferry_near.size();
var ferry_mid_count = ferry_mid.size();
var ferry_far_count = ferry_far.size();

// 打印统计结果
print('公交站点-近距离层级数量:', bus_near_count);
print('公交站点-中距离层级数量:', bus_mid_count);
print('公交站点-远距离层级数量:', bus_far_count);

print('渡口设施-近距离层级数量:', ferry_near_count);
print('渡口设施-中距离层级数量:', ferry_mid_count);
print('渡口设施-远距离层级数量:', ferry_far_count);

// 可视化
Map.centerObject(skeleton_feature, 11);

// 显示支撑骨架
Map.addLayer(skeleton_feature, {color: '#0000FF'}, '支撑骨架');

// 显示三个邻近层级
Map.addLayer(near_fc, {color: '#FFCC00'}, '近距离邻近带');
Map.addLayer(mid_fc, {color: '#FFA500'}, '中距离邻近带');
Map.addLayer(far_fc, {color: '#CCCCCC'}, '远距离邻近带');