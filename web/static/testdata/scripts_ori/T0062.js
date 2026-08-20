// 加载武汉市2015、2019和2023年交通设施点数据
var fc_2015 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2015');
var fc_2019 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2019');
var fc_2023 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2023');

// 设置地图中心点
Map.setCenter(114.3, 30.6, 10);

// 筛选公交站（主流设施）
var main_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'bus_stop'));
var main_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'bus_stop'));
var main_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 筛选渡口（补充设施）
var secondary_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var secondary_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var secondary_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 筛选机场（边缘设施）
var edge_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'airport'));
var edge_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'airport'));
var edge_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'airport'));

// 统计各年份各类设施数量
var main_count_2015 = main_2015.size();
var main_count_2019 = main_2019.size();
var main_count_2023 = main_2023.size();

var secondary_count_2015 = secondary_2015.size();
var secondary_count_2019 = secondary_2019.size();
var secondary_count_2023 = secondary_2023.size();

var edge_count_2015 = edge_2015.size();
var edge_count_2019 = edge_2019.size();
var edge_count_2023 = edge_2023.size();

// 打印统计结果
print('主流设施-公交站 2015:', main_count_2015);
print('主流设施-公交站 2019:', main_count_2019);
print('主流设施-公交站 2023:', main_count_2023);

print('补充设施-渡口 2015:', secondary_count_2015);
print('补充设施-渡口 2019:', secondary_count_2019);
print('补充设施-渡口 2023:', secondary_count_2023);

print('边缘设施-机场 2015:', edge_count_2015);
print('边缘设施-机场 2019:', edge_count_2019);
print('边缘设施-机场 2023:', edge_count_2023);