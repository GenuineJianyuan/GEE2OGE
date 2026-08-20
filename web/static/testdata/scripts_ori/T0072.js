// 加载武汉市2023年交通设施数据
var trans_2023 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2023');

// 构造走廊A线
var corridor_a_geom = ee.Geometry.LineString(
    [[114.08, 30.48], [114.28, 30.58], [114.52, 30.72]]);

// 构造走廊B线
var corridor_b_geom = ee.Geometry.LineString(
    [[114.02, 30.67], [114.28, 30.60], [114.56, 30.50]]);

// 创建走廊要素
var corridor_a_feature = ee.Feature(corridor_a_geom, {name: 'corridor_a'});
var corridor_b_feature = ee.Feature(corridor_b_geom, {name: 'corridor_b'});

// 创建缓冲区（约1公里）
var corridor_a_buffer = corridor_a_feature.buffer(1000);
var corridor_b_buffer = corridor_b_feature.buffer(1000);

// 创建要素集合
var corridor_a_fc = ee.FeatureCollection([corridor_a_buffer]);
var corridor_b_fc = ee.FeatureCollection([corridor_b_buffer]);

// 计算共享区域（交集）
var shared_zone = corridor_a_fc.intersection(corridor_b_fc);

// 计算走廊A独立区域（差集）
var corridor_a_only = corridor_a_fc.difference(corridor_b_fc);

// 计算走廊B独立区域（差集）
var corridor_b_only = corridor_b_fc.difference(corridor_a_fc);

// 筛选公交站
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 筛选渡口
var ferry_terminal = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 统计公交站数量
var bus_shared = bus_stop.filterBounds(shared_zone);
var bus_a_only = bus_stop.filterBounds(corridor_a_only);
var bus_b_only = bus_stop.filterBounds(corridor_b_only);

// 统计渡口数量
var ferry_shared = ferry_terminal.filterBounds(shared_zone);
var ferry_a_only = ferry_terminal.filterBounds(corridor_a_only);
var ferry_b_only = ferry_terminal.filterBounds(corridor_b_only);

// 获取数量
var bus_shared_count = bus_shared.size();
var bus_a_only_count = bus_a_only.size();
var bus_b_only_count = bus_b_only.size();

var ferry_shared_count = ferry_shared.size();
var ferry_a_only_count = ferry_a_only.size();
var ferry_b_only_count = ferry_b_only.size();

// 打印结果
print('公交站-共享区数量:', bus_shared_count);
print('公交站-走廊A独立区数量:', bus_a_only_count);
print('公交站-走廊B独立区数量:', bus_b_only_count);

print('渡口-共享区数量:', ferry_shared_count);
print('渡口-走廊A独立区数量:', ferry_a_only_count);
print('渡口-走廊B独立区数量:', ferry_b_only_count);

// 地图显示
Map.setCenter(114.3, 30.6, 10);
Map.addLayer(corridor_a_buffer, {color: 'blue'}, '走廊A缓冲区');
Map.addLayer(corridor_b_buffer, {color: 'red'}, '走廊B缓冲区');
Map.addLayer(shared_zone, {color: 'purple'}, '共享区域');
Map.addLayer(bus_stop, {color: 'green'}, '公交站');
Map.addLayer(ferry_terminal, {color: 'orange'}, '渡口');