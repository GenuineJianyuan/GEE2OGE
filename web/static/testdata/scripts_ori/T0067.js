// 加载武汉市2015、2019和2023年交通设施数据
var trans_2015 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2015');
var trans_2019 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2019');
var trans_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 加载武汉市2015、2019和2023年道路数据
var road_2015 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2015');
var road_2019 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2019');
var road_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2023');

// 设置地图中心
Map.setCenter(114.3, 30.6, 10);

// 计算各年份交通设施类型数（节点体系扩展指标）
var node_types_2015 = trans_2015.distinct(['fclass']);
var node_types_2019 = trans_2019.distinct(['fclass']);
var node_types_2023 = trans_2023.distinct(['fclass']);

var node_type_count_2015 = node_types_2015.size();
var node_type_count_2019 = node_types_2019.size();
var node_type_count_2023 = node_types_2023.size();

// 筛选各年份高速公路（motorway）
var motorway_2015 = road_2015.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2019 = road_2019.filter(ee.Filter.eq('fclass', 'motorway'));
var motorway_2023 = road_2023.filter(ee.Filter.eq('fclass', 'motorway'));

// 筛选各年份主干路（primary）
var primary_2015 = road_2015.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2019 = road_2019.filter(ee.Filter.eq('fclass', 'primary'));
var primary_2023 = road_2023.filter(ee.Filter.eq('fclass', 'primary'));

// 合并高速公路和主干路，形成高等级道路骨架
var skeleton_2015 = motorway_2015.merge(primary_2015);
var skeleton_2019 = motorway_2019.merge(primary_2019);
var skeleton_2023 = motorway_2023.merge(primary_2023);

// 计算各年份高等级道路骨架总长度（通道体系扩展指标）
var skeleton_len_2015 = skeleton_2015.map(function(feature) {
  return feature.set('length', feature.geometry().length());
});
var skeleton_len_2019 = skeleton_2019.map(function(feature) {
  return feature.set('length', feature.geometry().length());
});
var skeleton_len_2023 = skeleton_2023.map(function(feature) {
  return feature.set('length', feature.geometry().length());
});

var skeleton_sum_2015 = skeleton_len_2015.aggregate_sum('length');
var skeleton_sum_2019 = skeleton_len_2019.aggregate_sum('length');
var skeleton_sum_2023 = skeleton_len_2023.aggregate_sum('length');

// 输出结果
print('node_type_count_2015:', node_type_count_2015);
print('node_type_count_2019:', node_type_count_2019);
print('node_type_count_2023:', node_type_count_2023);

print('high_level_road_length_2015:', skeleton_sum_2015);
print('high_level_road_length_2019:', skeleton_sum_2019);
print('high_level_road_length_2023:', skeleton_sum_2023);