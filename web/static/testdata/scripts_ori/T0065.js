// 加载武汉交通数据（2015、2019、2023）
var trans_2015 = ee.FeatureCollection('users/your_username/wuhan_trans_2015');
var trans_2019 = ee.FeatureCollection('users/your_username/wuhan_trans_2019');
var trans_2023 = ee.FeatureCollection('users/your_username/wuhan_trans_2023');

// 加载武汉道路数据（2015、2019、2023）
var road_2015 = ee.FeatureCollection('users/your_username/wuhan_road_2015');
var road_2019 = ee.FeatureCollection('users/your_username/wuhan_road_2019');
var road_2023 = ee.FeatureCollection('users/your_username/wuhan_road_2023');

// 设置地图中心
Map.setCenter(114.3, 30.6, 10);

// 筛选公交站
var bus_2015 = trans_2015.filter(ee.Filter.eq('fclass', 'bus_stop'));
var bus_2019 = trans_2019.filter(ee.Filter.eq('fclass', 'bus_stop'));
var bus_2023 = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 统计公交站数量
var bus_count_2015 = bus_2015.size();
var bus_count_2019 = bus_2019.size();
var bus_count_2023 = bus_2023.size();

// 筛选高速路
var motorway_2015 = road_2015.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2019 = road_2019.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2023 = road_2023.filter(ee.Filter.eq('fclass', 'motorway'));

// 筛选主干路
var primary_2015 = road_2015.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2019 = road_2019.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2023 = road_2023.filter(ee.Filter.eq('fclass', 'primary'));

// 合并高速路和主干路为道路骨架
var skeleton_2015 = motorway_2015.merge(primary_2015);
var skeleton_2019 = motorway_2019.merge(primary_2019);
var skeleton_2023 = motorway_2023.merge(primary_2023);

// 计算道路骨架长度
var skeleton_len_2015 = skeleton_2015.map(function(feature) {
  return feature.set('length', feature.geometry().length());
});
var skeleton_len_2019 = skeleton_2019.map(function(feature) {
  return feature.set('length', feature.geometry().length());
});
var skeleton_len_2023 = skeleton_2023.map(function(feature) {
  return feature.set('length', feature.geometry().length());
});

// 汇总道路骨架总长度
var skeleton_sum_2015 = skeleton_len_2015.reduceColumns(ee.Reducer.sum(), ['length']).get('sum');
var skeleton_sum_2019 = skeleton_len_2019.reduceColumns(ee.Reducer.sum(), ['length']).get('sum');
var skeleton_sum_2023 = skeleton_len_2023.reduceColumns(ee.Reducer.sum(), ['length']).get('sum');

// 输出结果
print('bus_stop_count_2015:', bus_count_2015);
print('bus_stop_count_2019:', bus_count_2019);
print('bus_stop_count_2023:', bus_count_2023);

print('road_skeleton_length_2015:', skeleton_sum_2015);
print('road_skeleton_length_2019:', skeleton_sum_2019);
print('road_skeleton_length_2023:', skeleton_sum_2023);