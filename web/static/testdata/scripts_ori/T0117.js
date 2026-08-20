// 创建两个面要素
var geometry1 = ee.Geometry.Polygon([[[35, 10], [35, 15], [40, 15], [40, 10], [35, 10]]], 'EPSG:4326');
var feature1 = ee.Feature(geometry1, {a: 10});

var geometry2 = ee.Geometry.Polygon([[[45, 10], [45, 15], [50, 15], [50, 10], [45, 10]]], 'EPSG:4326');
var feature2 = ee.Feature(geometry2, {a: 10});

// 计算两个要素之间的最短距离（以米为单位）
var distance = feature1.distance(feature2.geometry(), 1);

// 在地图上展示两个要素
Map.addLayer(feature1, {color: '#000000'}, 'polygon1');
Map.addLayer(feature2, {color: '#111111'}, 'polygon2');

// 输出距离到控制台
print('distance:', distance);

// 设置地图中心点
Map.setCenter(37, 12, 5);