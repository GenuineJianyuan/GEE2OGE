// 加载武汉市2023年交通设施数据
var trans_2023 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2023');

// 构造走廊线
var corridor_geom = ee.Geometry.LineString(
  [[114.10, 30.45], [114.30, 30.58], [114.55, 30.72]]
);

// 创建走廊缓冲区（约1公里）
var corridor_buffer = corridor_geom.buffer(1000); // 0.01度约等于1公里
var corridor_fc = ee.FeatureCollection([ee.Feature(corridor_buffer, {name: 'main_corridor'})]);

// 定义研究区范围
var study_geom = ee.Geometry.Polygon(
  [[[114.00, 30.35], [114.00, 30.82], [114.65, 30.82], [114.65, 30.35], [114.00, 30.35]]]
);
var study_fc = ee.FeatureCollection([ee.Feature(study_geom, {name: 'study_area'})]);

// 计算走廊外区域（研究区减去走廊缓冲区）
var outer_zone = study_fc.difference(corridor_fc);

// 筛选公交站和渡口设施
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));
var ferry_terminal = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 统计走廊内外的设施数量
var bus_in_corridor = bus_stop.filterBounds(corridor_buffer);
var bus_out_corridor = bus_stop.filterBounds(outer_zone.geometry());
var ferry_in_corridor = ferry_terminal.filterBounds(corridor_buffer);
var ferry_out_corridor = ferry_terminal.filterBounds(outer_zone.geometry());

// 获取数量统计
var bus_in_count = bus_in_corridor.size();
var bus_out_count = bus_out_corridor.size();
var ferry_in_count = ferry_in_corridor.size();
var ferry_out_count = ferry_out_corridor.size();

// 打印统计结果
print('公交站走廊内数量:', bus_in_count);
print('公交站走廊外数量:', bus_out_count);
print('渡口走廊内数量:', ferry_in_count);
print('渡口走廊外数量:', ferry_out_count);

// 地图可视化
Map.setCenter(114.3, 30.6, 10);
Map.addLayer(corridor_buffer, {color: 'red'}, '走廊缓冲区');
Map.addLayer(study_geom, {color: 'blue'}, '研究区');
Map.addLayer(bus_stop, {color: 'green'}, '公交站');
Map.addLayer(ferry_terminal, {color: 'orange'}, '渡口');