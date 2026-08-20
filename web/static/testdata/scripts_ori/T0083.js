// 加载武汉市2023年道路数据（需先上传到GEE资产）
var road_2023 = ee.FeatureCollection('users/your_username/wuhan_road_2023');

// 定义研究区范围
var study_geom = ee.Geometry.Polygon([
  [114.24, 30.52], [114.24, 30.58], [114.34, 30.58], [114.34, 30.52], [114.24, 30.52]
]);
var study_fc = ee.FeatureCollection([ee.Feature(study_geom, {name: 'study_area'})]);

// 定义候选走廊线并生成缓冲区
var candidate_corridor_geom = ee.Geometry.LineString([
  [114.245, 30.545], [114.29, 30.552], [114.335, 30.558]
]);
var candidate_corridor_feature = ee.Feature(candidate_corridor_geom, {name: 'candidate_corridor'});
var candidate_buffer = candidate_corridor_feature.buffer(0.008);
var candidate_fc = ee.FeatureCollection([candidate_buffer]);

// 定义排除区
var exclude_geom = ee.Geometry.Polygon([
  [114.282, 30.544], [114.282, 30.560], [114.300, 30.560], [114.300, 30.544], [114.282, 30.544]
]);
var exclude_feature = ee.Feature(exclude_geom, {name: 'exclusion_zone'});
var exclude_fc = ee.FeatureCollection([exclude_feature]);

// 候选区与研究区求交
var candidate_zone_in_study = candidate_fc.intersection(study_fc);

// 可用候选区 = 候选区 - 排除区
var usable_candidate_zone = candidate_zone_in_study.difference(exclude_fc);

// 道路与研究区求交
var road_in_study = road_2023.intersection(study_fc);

// 候选道路段 = 道路 ∩ 可用候选区
var candidate_road_segment = road_in_study.intersection(usable_candidate_zone);

// 受限道路段 = 道路 ∩ 排除区
var restricted_road_segment = road_in_study.intersection(exclude_fc);

// 可视化
Map.centerObject(study_fc, 14);
Map.addLayer(candidate_zone_in_study, {color: '#FFCC00'}, '候选区');
Map.addLayer(exclude_fc, {color: '#FF6666'}, '排除区');
Map.addLayer(candidate_road_segment, {color: '#00AAFF'}, '候选道路段');
Map.addLayer(restricted_road_segment, {color: '#6600CC'}, '受限道路段');