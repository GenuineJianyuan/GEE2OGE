// 加载武汉市2015、2019、2023年道路数据
var fc_2015 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2015');
var fc_2019 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2019');
var fc_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2023');

// 设置地图中心
Map.setCenter(114.3, 30.6, 10);

// 计算各年份道路总长度（单位：米）
var all_len_2015 = fc_2015.map(function(f) {
  return f.set('length', f.geometry().length());
});
var all_len_2019 = fc_2019.map(function(f) {
  return f.set('length', f.geometry().length());
});
var all_len_2023 = fc_2023.map(function(f) {
  return f.set('length', f.geometry().length());
});

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

// 合并高速路和主干路为高等级道路
var high_level_2015 = motorway_2015.merge(primary_2015);
var high_level_2019 = motorway_2019.merge(primary_2019);
var high_level_2023 = motorway_2023.merge(primary_2023);

// 计算高等级道路长度
var high_level_len_2015 = high_level_2015.map(function(f) {
  return f.set('length', f.geometry().length());
});
var high_level_len_2019 = high_level_2019.map(function(f) {
  return f.set('length', f.geometry().length());
});
var high_level_len_2023 = high_level_2023.map(function(f) {
  return f.set('length', f.geometry().length());
});

var high_level_sum_2015 = high_level_len_2015.aggregate_sum('length');
var high_level_sum_2019 = high_level_len_2019.aggregate_sum('length');
var high_level_sum_2023 = high_level_len_2023.aggregate_sum('length');

// 输出结果到控制台
print('total_road_length_2015:', total_len_2015);
print('total_road_length_2019:', total_len_2019);
print('total_road_length_2023:', total_len_2023);

print('high_level_road_length_2015:', high_level_sum_2015);
print('high_level_road_length_2019:', high_level_sum_2019);
print('high_level_road_length_2023:', high_level_sum_2023);