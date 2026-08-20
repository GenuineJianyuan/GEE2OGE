// 加载武汉市2015、2019、2023年交通设施点数据
var fc_2015 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2015');
var fc_2019 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2019');
var fc_2023 = ee.FeatureCollection('projects/your-project-id/assets/wuhan_trans_2023');

// 设置地图中心
Map.setCenter(114.3, 30.6, 10);

// 计算各年设施总量
var total_2015 = fc_2015.size();
var total_2019 = fc_2019.size();
var total_2023 = fc_2023.size();

// 筛选公交站
var bus_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'bus_stop'));
var bus_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'bus_stop'));
var bus_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'bus_stop'));

// 筛选机场
var airport_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'airport'));
var airport_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'airport'));
var airport_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'airport'));

// 筛选渡口
var ferry_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var ferry_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var ferry_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 计算各类设施数量
var bus_count_2015 = bus_2015.size();
var bus_count_2019 = bus_2019.size();
var bus_count_2023 = bus_2023.size();

var airport_count_2015 = airport_2015.size();
var airport_count_2019 = airport_2019.size();
var airport_count_2023 = airport_2023.size();

var ferry_count_2015 = ferry_2015.size();
var ferry_count_2019 = ferry_2019.size();
var ferry_count_2023 = ferry_2023.size();

// 打印结果
print('total_facilities_2015:', total_2015);
print('total_facilities_2019:', total_2019);
print('total_facilities_2023:', total_2023);

print('bus_stop_count_2015:', bus_count_2015);
print('bus_stop_count_2019:', bus_count_2019);
print('bus_stop_count_2023:', bus_count_2023);

print('airport_count_2015:', airport_count_2015);
print('airport_count_2019:', airport_count_2019);
print('airport_count_2023:', airport_count_2023);

print('ferry_terminal_count_2015:', ferry_count_2015);
print('ferry_terminal_count_2019:', ferry_count_2019);
print('ferry_terminal_count_2023:', ferry_count_2023);