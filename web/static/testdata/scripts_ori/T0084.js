// 定义研究区范围（武汉沿江片区）
var study_geom = ee.Geometry.Polygon([
  [114.24, 30.52], [114.24, 30.59], [114.35, 30.59], [114.35, 30.52], [114.24, 30.52]
]);

// 定义支撑通道A（沿江主通道）
var support_a_geom = ee.Geometry.LineString([
  [114.245, 30.545], [114.29, 30.552], [114.34, 30.558]
]);
var support_a_buffer = support_a_geom.buffer(0.008);

// 定义支撑通道B（向内陆连接通道）
var support_b_geom = ee.Geometry.LineString([
  [114.275, 30.525], [114.29, 30.552], [114.315, 30.585]
]);
var support_b_buffer = support_b_geom.buffer(0.008);

// 定义关键节点（中华路1号码头）并建立排除带
var key_node = ee.Geometry.Point([114.2885828, 30.5512112]);
var exclusion_buffer = key_node.buffer(0.01);

// 计算各区域在研究范围内的部分
var support_a_in_study = support_a_buffer.intersection(study_geom);
var support_b_in_study = support_b_buffer.intersection(study_geom);
var exclusion_in_study = exclusion_buffer.intersection(study_geom);

// 计算双支撑同时满足的优先候选区基础
var priority_base = support_a_in_study.intersection(support_b_in_study);

// 计算仅满足单一支撑的备用候选区基础
var backup_a_base = support_a_in_study.difference(support_b_in_study);
var backup_b_base = support_b_in_study.difference(support_a_in_study);

// 从各区域中排除关键节点排除带
var priority_zone = priority_base.difference(exclusion_in_study);
var backup_a_zone = backup_a_base.difference(exclusion_in_study);
var backup_b_zone = backup_b_base.difference(exclusion_in_study);

// 计算不满足任一支撑条件的空白区
var blank_step = study_geom.difference(support_a_in_study);
var blank_zone = blank_step.difference(support_b_in_study);

// 合并备用候选区
var backup_zone_fc = ee.FeatureCollection([
  ee.Feature(backup_a_zone, {name: 'backup_a'}),
  ee.Feature(backup_b_zone, {name: 'backup_b'})
]);

// 可视化各区域
Map.addLayer(support_a_in_study, {color: '#FFCC00'}, '支撑约束区A');
Map.addLayer(support_b_in_study, {color: '#99CCFF'}, '支撑约束区B');
Map.addLayer(priority_zone, {color: '#66CC66'}, '优先候选区');
Map.addLayer(backup_zone_fc, {color: '#CCCCCC'}, '备用候选区');
Map.addLayer(blank_zone, {color: '#FF6666'}, '空白区');

// 设置地图中心
Map.setCenter(114.2886, 30.5512, 14);