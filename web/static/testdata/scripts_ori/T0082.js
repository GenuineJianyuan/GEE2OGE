// 定义研究区（多边形）
var study_geom = ee.Geometry.Polygon([[[114.24, 30.52], [114.24, 30.58], [114.34, 30.58], [114.34, 30.52], [114.24, 30.52]]]);
var study_fc = ee.FeatureCollection([ee.Feature(study_geom, {name: 'study_area'})]);

// 定义主支撑通道骨架线并生成缓冲区
var skeleton_geom = ee.Geometry.LineString([[114.245, 30.545], [114.29, 30.552], [114.335, 30.558]]);
var skeleton_feature = ee.Feature(skeleton_geom, {name: 'support_skeleton'});
var support_buffer = skeleton_feature.buffer(0.008);
var support_fc = ee.FeatureCollection([support_buffer]);

// 定义附加保留区
var reserve_geom = ee.Geometry.Polygon([[[114.255, 30.538], [114.255, 30.572], [114.325, 30.572], [114.325, 30.538], [114.255, 30.538]]]);
var reserve_feature = ee.Feature(reserve_geom, {name: 'reserve_zone'});
var reserve_fc = ee.FeatureCollection([reserve_feature]);

// 定义关键节点（中华路1号码头）并生成排除缓冲区
var key_node_geom = ee.Geometry.Point([114.2885828, 30.5512112]);
var key_node_feature = ee.Feature(key_node_geom, {name: '中华路1号码头', fclass: 'ferry_terminal'});
var exclusion_buffer = key_node_feature.buffer(0.01);
var exclusion_fc = ee.FeatureCollection([exclusion_buffer]);

// 计算优先区：主支撑缓冲区 ∩ 附加保留区 - 排除缓冲区
var priority_base = support_fc.intersection(reserve_fc);
var priority_zone = priority_base.difference(exclusion_fc);

// 计算限制区：研究区 - 优先区 - 排除缓冲区
var restricted_tmp = study_fc.difference(priority_zone);
var restricted_zone = restricted_tmp.difference(exclusion_fc);

// 可视化各约束结果
Map.addLayer(support_fc, {color: '#FFCC00'}, '主支撑约束结果');
Map.addLayer(reserve_fc, {color: '#99CCFF'}, '附加保留约束结果');
Map.addLayer(exclusion_fc, {color: '#FF6666'}, '排除约束结果');

// 可视化最终分级结果
Map.addLayer(priority_zone, {color: '#66CC66'}, '优先区');
Map.addLayer(restricted_zone, {color: '#CCCCCC'}, '限制区');
Map.addLayer(exclusion_fc, {color: '#CC3333'}, '排除区');

// 设置地图中心
Map.setCenter(114.2886, 30.5512, 14);