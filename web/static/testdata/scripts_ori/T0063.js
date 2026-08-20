// 加载武汉市道路数据（2015、2019、2023）
var fc_2015 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2015');
var fc_2019 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2019');
var fc_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2023');

// 设置地图中心
Map.setCenter(114.3, 30.6, 10);

// 计算各年份道路总长度（单位：米）
var all_len_2015 = fc_2015.map(function(f) { return f.set('length', f.geometry().length()); });
var all_len_2019 = fc_2019.map(function(f) { return f.set('length', f.geometry().length()); });
var all_len_2023 = fc_2023.map(function(f) { return f.set('length', f.geometry().length()); });

var total_len_2015 = all_len_2015.aggregate_sum('length');
var total_len_2019 = all_len_2019.aggregate_sum('length');
var total_len_2023 = all_len_2023.aggregate_sum('length');

// 筛选高速路（motorway）
var motorway_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'motorway'));

// 筛选主干路（primary）
var primary_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'primary'));

// 筛选次干路（secondary）
var secondary_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'secondary'));
var secondary_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'secondary'));
var secondary_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'secondary'));

// 计算各等级道路长度
var motorway_len_2015 = motorway_2015.map(function(f) { return f.set('length', f.geometry().length()); });
var motorway_len_2019 = motorway_2019.map(function(f) { return f.set('length', f.geometry().length()); });
var motorway_len_2023 = motorway_2023.map(function(f) { return f.set('length', f.geometry().length()); });

var primary_len_2015 = primary_2015.map(function(f) { return f.set('length', f.geometry().length()); });
var primary_len_2019 = primary_2019.map(function(f) { return f.set('length', f.geometry().length()); });
var primary_len_2023 = primary_2023.map(function(f) { return f.set('length', f.geometry().length()); });

var secondary_len_2015 = secondary_2015.map(function(f) { return f.set('length', f.geometry().length()); });
var secondary_len_2019 = secondary_2019.map(function(f) { return f.set('length', f.geometry().length()); });
var secondary_len_2023 = secondary_2023.map(function(f) { return f.set('length', f.geometry().length()); });

// 汇总各等级道路总长度
var motorway_sum_2015 = motorway_len_2015.aggregate_sum('length');
var motorway_sum_2019 = motorway_len_2019.aggregate_sum('length');
var motorway_sum_2023 = motorway_len_2023.aggregate_sum('length');

var primary_sum_2015 = primary_len_2015.aggregate_sum('length');
var primary_sum_2019 = primary_len_2019.aggregate_sum('length');
var primary_sum_2023 = primary_len_2023.aggregate_sum('length');

var secondary_sum_2015 = secondary_len_2015.aggregate_sum('length');
var secondary_sum_2019 = secondary_len_2019.aggregate_sum('length');
var secondary_sum_2023 = secondary_len_2023.aggregate_sum('length');

// 输出结果到控制台
print('total_road_length_2015:', total_len_2015);
print('total_road_length_2019:', total_len_2019);
print('total_road_length_2023:', total_len_2023);

print('motorway_length_2015:', motorway_sum_2015);
print('motorway_length_2019:', motorway_sum_2019);
print('motorway_length_2023:', motorway_sum_2023);

print('primary_length_2015:', primary_sum_2015);
print('primary_length_2019:', primary_sum_2019);
print('primary_length_2023:', primary_sum_2023);

print('secondary_length_2015:', secondary_sum_2015);
print('secondary_length_2019:', secondary_sum_2019);
print('secondary_length_2023:', secondary_sum_2023);