// 加载武汉交通数据（2015、2019、2023）
var trans_2015 = ee.FeatureCollection('users/your_username/wuhan_trans_2015');
var trans_2019 = ee.FeatureCollection('users/your_username/wuhan_trans_2019');
var trans_2023 = ee.FeatureCollection('users/your_username/wuhan_trans_2023');

var road_2015 = ee.FeatureCollection('users/your_username/wuhan_road_2015');
var road_2019 = ee.FeatureCollection('users/your_username/wuhan_road_2019');
var road_2023 = ee.FeatureCollection('users/your_username/wuhan_road_2023');

Map.setCenter(114.3, 30.6, 10);

// 筛选关键交通节点（渡口和机场）
var ferry_2015 = trans_2015.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var ferry_2019 = trans_2019.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var ferry_2023 = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

var airport_2015 = trans_2015.filter(ee.Filter.eq('fclass', 'airport'));
var airport_2019 = trans_2019.filter(ee.Filter.eq('fclass', 'airport'));
var airport_2023 = trans_2023.filter(ee.Filter.eq('fclass', 'airport'));

// 合并关键节点
var key_nodes_2015 = ferry_2015.merge(airport_2015);
var key_nodes_2019 = ferry_2019.merge(airport_2019);
var key_nodes_2023 = ferry_2023.merge(airport_2023);

// 统计关键节点数量
var key_node_count_2015 = key_nodes_2015.size();
var key_node_count_2019 = key_nodes_2019.size();
var key_node_count_2023 = key_nodes_2023.size();

// 计算所有道路总长度
var all_len_2015 = road_2015.map(function(f) {
  return f.set('length', f.geometry().length());
});
var all_len_2019 = road_2019.map(function(f) {
  return f.set('length', f.geometry().length());
});
var all_len_2023 = road_2023.map(function(f) {
  return f.set('length', f.geometry().length());
});

var total_road_length_2015 = all_len_2015.aggregate_sum('length');
var total_road_length_2019 = all_len_2019.aggregate_sum('length');
var total_road_length_2023 = all_len_2023.aggregate_sum('length');

// 筛选高等级道路（高速路和主干路）
var motorway_2015 = road_2015.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2019 = road_2019.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2023 = road_2023.filter(ee.Filter.eq('fclass', 'motorway'));

var primary_2015 = road_2015.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2019 = road_2019.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2023 = road_2023.filter(ee.Filter.eq('fclass', 'primary'));

// 合并高等级道路骨架
var skeleton_2015 = motorway_2015.merge(primary_2015);
var skeleton_2019 = motorway_2019.merge(primary_2019);
var skeleton_2023 = motorway_2023.merge(primary_2023);

// 计算高等级道路骨架长度
var skeleton_len_2015 = skeleton_2015.map(function(f) {
  return f.set('length', f.geometry().length());
});
var skeleton_len_2019 = skeleton_2019.map(function(f) {
  return f.set('length', f.geometry().length());
});
var skeleton_len_2023 = skeleton_2023.map(function(f) {
  return f.set('length', f.geometry().length());
});

var skeleton_sum_2015 = skeleton_len_2015.aggregate_sum('length');
var skeleton_sum_2019 = skeleton_len_2019.aggregate_sum('length');
var skeleton_sum_2023 = skeleton_len_2023.aggregate_sum('length');

// 输出统计结果
print('key_node_count_2015:', key_node_count_2015);
print('key_node_count_2019:', key_node_count_2019);
print('key_node_count_2023:', key_node_count_2023);

print('high_level_road_length_2015:', skeleton_sum_2015);
print('high_level_road_length_2019:', skeleton_sum_2019);
print('high_level_road_length_2023:', skeleton_sum_2023);

print('total_road_length_2015:', total_road_length_2015);
print('total_road_length_2019:', total_road_length_2019);
print('total_road_length_2023:', total_road_length_2023);