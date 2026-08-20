// 加载道路网络数据（使用 GEE 中的道路数据替代）
var roads = ee.FeatureCollection('TIGER/2016/Roads');

// 定义起点和终点坐标
var startCoords = ee.Geometry.Point([114.337475, 30.558570]);
var endCoords = ee.Geometry.Point([114.328842, 30.542172]);

// 创建起点和终点要素
var start = ee.Feature(startCoords, {name: 'start'});
var end = ee.Feature(endCoords, {name: 'end'});

// 由于 GEE 没有直接的最短路径分析功能，
// 这里使用缓冲区分析和距离计算作为替代方案

// 创建起点和终点的缓冲区（用于可视化）
var startBuffer = start.buffer(100);
var endBuffer = end.buffer(100);

// 计算道路网络到起点和终点的距离
var distanceToStart = roads.map(function(feature) {
  var dist = feature.distance(startCoords);
  return feature.set('dist_to_start', dist);
});

var distanceToEnd = distanceToStart.map(function(feature) {
  var dist = feature.distance(endCoords);
  return feature.set('dist_to_end', dist);
});

// 选择距离起点和终点都较近的道路（模拟最短路径）
var shortestPath = distanceToEnd.filter(ee.Filter.lt('dist_to_start', 1000))
                                .filter(ee.Filter.lt('dist_to_end', 1000));

// 计算道路长度（作为路径成本）
var roadsWithLength = shortestPath.map(function(feature) {
  var length = feature.length();
  return feature.set('length', length);
});

// 可视化参数
var visParams = {
  color: 'FF0000',
  width: 2
};

// 添加图层到地图
Map.centerObject(ee.Geometry.Point([114.33, 30.55]), 13);

// 显示起点和终点
Map.addLayer(startBuffer, {color: '000000'}, '起点');
Map.addLayer(endBuffer, {color: '000000'}, '终点');

// 显示道路网络
Map.addLayer(roads, {color: 'CCCCCC'}, '道路网络');

// 显示模拟的最短路径（黄色）
Map.addLayer(roadsWithLength.style({color: 'FFCC33'}), {}, '最短路径');

// 显示模拟的最快路径（粉色）- 这里假设速度限制为50km/h
var fastestPath = roadsWithLength.map(function(feature) {
  var speed = 50; // 假设速度限制为50km/h
  var time = feature.get('length').divide(speed);
  return feature.set('time', time);
});
Map.addLayer(fastestPath.style({color: 'FF99CC'}), {}, '最快路径');

// 显示考虑速度限制的路径（绿色）- 这里使用不同的速度限制
var speedLimitPath = roadsWithLength.map(function(feature) {
  var speed = 30; // 假设速度限制为30km/h
  var time = feature.get('length').divide(speed);
  return feature.set('time', time);
});
Map.addLayer(speedLimitPath.style({color: '33CC66'}), {}, '考虑速度限制路径');