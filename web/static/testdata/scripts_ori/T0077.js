// 加载武汉市2023年渡口设施数据
var trans_2023 = ee.FeatureCollection('myData/wuhan_trans_2023');

// 筛选渡口终端设施
var ferry_terminal = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 构造代表主支撑道路方向的简化骨架线
var skeleton_coords = ee.List([
  [114.08, 30.46],
  [114.28, 30.58],
  [114.54, 30.71]
]);
var skeleton_geom = ee.Geometry.LineString(skeleton_coords);
var skeleton_feature = ee.Feature(skeleton_geom, {name: 'high_level_skeleton'});

// 建立邻近范围（缓冲区）
var near_buffer = skeleton_feature.buffer(0.01);
var near_buffer_fc = ee.FeatureCollection([near_buffer]);

// 筛查落在邻近范围内的关键设施
var ferry_near_skeleton = ferry_terminal.filterBounds(near_buffer.geometry());

// 统计数量
var ferry_total_count = ferry_terminal.size();
var ferry_near_count = ferry_near_skeleton.size();

// 输出统计结果
print('ferry_terminal_total_count:', ferry_total_count);
print('ferry_terminal_near_skeleton_count:', ferry_near_count);

// 可视化
Map.addLayer(skeleton_feature, {color: '#0000FF'}, '高等级道路骨架');
Map.addLayer(ferry_near_skeleton, {color: '#FF0000'}, '靠近骨架的关键设施');

// 设置地图中心
Map.setCenter(114.3, 30.6, 10);