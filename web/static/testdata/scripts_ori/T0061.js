// 加载武汉市2015、2019和2023年交通设施点数据
var fc_2015 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2015');
var fc_2019 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2019');
var fc_2023 = ee.FeatureCollection('projects/your-project/assets/wuhan_trans_2023');

// 设置地图中心点
Map.setCenter(114.3, 30.6, 10);

// 获取每年的不同设施类型
var distinct_2015 = fc_2015.distinct(['fclass']);
var distinct_2019 = fc_2019.distinct(['fclass']);
var distinct_2023 = fc_2023.distinct(['fclass']);

// 统计每年的设施类型总数
var type_count_2015 = distinct_2015.size();
var type_count_2019 = distinct_2019.size();
var type_count_2023 = distinct_2023.size();

// 筛选机场设施
var airport_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'airport'));
var airport_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'airport'));
var airport_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'airport'));

// 筛选渡口设施
var ferry_2015 = fc_2015.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var ferry_2019 = fc_2019.filter(ee.Filter.eq('fclass', 'ferry_terminal'));
var ferry_2023 = fc_2023.filter(ee.Filter.eq('fclass', 'ferry_terminal'));

// 统计机场数量
var airport_count_2015 = airport_2015.size();
var airport_count_2019 = airport_2019.size();
var airport_count_2023 = airport_2023.size();

// 统计渡口数量
var ferry_count_2015 = ferry_2015.size();
var ferry_count_2019 = ferry_2019.size();
var ferry_count_2023 = ferry_2023.size();

// 输出结果到控制台
print('facility_type_count_2015:', type_count_2015);
print('facility_type_count_2019:', type_count_2019);
print('facility_type_count_2023:', type_count_2023);

print('airport_count_2015:', airport_count_2015);
print('airport_count_2019:', airport_count_2019);
print('airport_count_2023:', airport_count_2023);

print('ferry_terminal_count_2015:', ferry_count_2015);
print('ferry_terminal_count_2019:', ferry_count_2019);
print('ferry_terminal_count_2023:', ferry_count_2023);