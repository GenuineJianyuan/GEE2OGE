// 加载武汉市2023年交通设施数据
var trans_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 创建走廊线几何
var corridor_geom = ee.Geometry.LineString(
  [[114.10, 30.45], [114.30, 30.58], [114.55, 30.72]]
);

// 创建走廊要素并设置属性
var corridor_feature = ee.Feature(corridor_geom, {name: 'main_corridor'});

// 创建缓冲区（约1公里）
var corridor_buffer = corridor_feature.buffer(1000);

// 创建走廊要素集合
var corridor_fc = ee.FeatureCollection([corridor_buffer]);

// 筛选公交站点
var bus_stop = trans_2023.filter(
  ee.Filter.eq('fclass', 'bus_stop')
);

// 筛选走廊范围内的公交站点
var bus_in_corridor = bus_stop.filterBounds(corridor_fc);

// 可视化设置
Map.addLayer(bus_in_corridor, {color: 'FF0000'}, '走廊内公交站点');
Map.setCenter(114.3, 30.6, 10);