// 定义研究区几何（武汉沿江片区）
var study_geom = ee.Geometry.Polygon([
  [114.24, 30.52], [114.24, 30.58], [114.34, 30.58], [114.34, 30.52], [114.24, 30.52]
]);

// 创建研究区要素和要素集合
var study_feature = ee.Feature(study_geom, {name: 'study_area'});
var study_fc = ee.FeatureCollection([study_feature]);

// 定义主支撑通道骨架线
var skeleton_geom = ee.Geometry.LineString([
  [114.245, 30.545], [114.29, 30.552], [114.335, 30.558]
]);
var skeleton_feature = ee.Feature(skeleton_geom, {name: 'support_skeleton'});

// 创建主骨架邻近带（缓冲区）
var support_buffer = skeleton_feature.buffer(0.008);
var support_fc = ee.FeatureCollection([support_buffer]);

// 定义关键节点（中华路1号码头）
var key_node_geom = ee.Geometry.Point([114.2885828, 30.5512112]);
var key_node_feature = ee.Feature(key_node_geom, {name: '中华路1号码头', fclass: 'ferry_terminal'});

// 创建关键节点排除带（缓冲区）
var exclusion_buffer = key_node_feature.buffer(0.01);
var exclusion_fc = ee.FeatureCollection([exclusion_buffer]);

// 将缓冲区与研究区求交，确保在范围内
var support_zone_in_study = support_fc.intersection(study_fc);
var exclusion_zone_in_study = exclusion_fc.intersection(study_fc);

// 计算最终保留候选带（主骨架邻近带减去排除带）
var candidate_zone = support_zone_in_study.difference(exclusion_zone_in_study);

// 可视化设置
Map.setCenter(114.2886, 30.5512, 14);

// 添加图层到地图
Map.addLayer(support_zone_in_study, {color: '#FFCC00'}, '主骨架邻近带');
Map.addLayer(exclusion_zone_in_study, {color: '#FF6666'}, '关键节点排除带');
Map.addLayer(candidate_zone, {color: '#66CC66'}, '保留候选带');