// 加载武汉市2023年道路和交通设施数据
var road_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_road_2023');
var trans_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 构造指定分析区（矩形多边形）
var study_geom = ee.Geometry.Polygon([
  [114.12, 30.50], [114.12, 30.74], [114.48, 30.74], [114.48, 30.50], [114.12, 30.50]
]);

// 创建分析区要素和要素集合
var study_feature = ee.Feature(study_geom, {name: 'study_area'});
var study_fc = ee.FeatureCollection([study_feature]);

// 提取分析区内的道路（使用intersection裁剪）
var road_in_area = road_2023.filterBounds(study_geom);

// 提取分析区内的交通设施（使用intersection裁剪）
var trans_in_area = trans_2023.filterBounds(study_geom);

// 在地图上展示三类结果
Map.addLayer(study_fc, {color: '#FFCC00'}, '指定分析区');
Map.addLayer(road_in_area, {color: '#0000FF'}, '分析区内道路');
Map.addLayer(trans_in_area, {color: '#FF0000'}, '分析区内交通设施');

// 设置地图中心点
Map.setCenter(114.3, 30.62, 11);