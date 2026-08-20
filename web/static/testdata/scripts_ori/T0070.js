// 加载武汉市2023年交通设施数据
var trans_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 构造走廊线
var corridor_geom = ee.Geometry.LineString(
  [[114.10, 30.45], [114.30, 30.58], [114.55, 30.72]]
);

// 创建走廊要素
var corridor_feature = ee.Feature(corridor_geom, {name: 'main_corridor'});

// 创建三个缓冲层级（单位：度）
var near_buffer = corridor_feature.buffer(0.005);
var mid_buffer = corridor_feature.buffer(0.01);
var outer_buffer = corridor_feature.buffer(0.02);

// 转换为要素集合
var near_fc = ee.FeatureCollection([near_buffer]);
var mid_fc = ee.FeatureCollection([mid_buffer]);
var outer_fc = ee.FeatureCollection([outer_buffer]);

// 计算中距离带（中缓冲减去近缓冲）
var mid_band = mid_fc.difference(near_fc);
// 计算外缘带（外缓冲减去中缓冲）
var outer_band = outer_fc.difference(mid_fc);

// 筛选公交站
var bus_stop = trans_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));
// 筛选渡口
var ferry_terminal = trans_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 统计各层级公交站数量
var bus_near = bus_stop.filterBounds(near_fc);
var bus_mid = bus_stop.filterBounds(mid_band);
var bus_outer = bus_stop.filterBounds(outer_band);

// 统计各层级渡口数量
var ferry_near = ferry_terminal.filterBounds(near_fc);
var ferry_mid = ferry_terminal.filterBounds(mid_band);
var ferry_outer = ferry_terminal.filterBounds(outer_band);

// 获取数量
var bus_near_count = bus_near.size();
var bus_mid_count = bus_mid.size();
var bus_outer_count = bus_outer.size();

var ferry_near_count = ferry_near.size();
var ferry_mid_count = ferry_mid.size();
var ferry_outer_count = ferry_outer.size();

// 打印结果
print('公交站-近带数量:', bus_near_count);
print('公交站-中带数量:', bus_mid_count);
print('公交站-外带数量:', bus_outer_count);

print('渡口-近带数量:', ferry_near_count);
print('渡口-中带数量:', ferry_mid_count);
print('渡口-外带数量:', ferry_outer_count);

// 地图显示
Map.setCenter(114.3, 30.6, 10);
Map.addLayer(corridor_feature, {color: 'red'}, '主走廊');
Map.addLayer(near_fc, {color: 'yellow'}, '近带');
Map.addLayer(mid_band, {color: 'orange'}, '中带');
Map.addLayer(outer_band, {color: 'purple'}, '外带');
Map.addLayer(bus_stop, {color: 'blue'}, '公交站');
Map.addLayer(ferry_terminal, {color: 'green'}, '渡口');