// 创建两个面要素
var geometry1 = ee.Geometry.Polygon([[[35, 10], [35, 15], [40, 15], [40, 10], [35, 10]]], 'EPSG:4326');
var feature1 = ee.Feature(geometry1, {a: 10});

var geometry2 = ee.Geometry.Polygon([[[36, 11], [36, 14], [39, 14], [39, 11], [36, 11]]], 'EPSG:4326');
var feature2 = ee.Feature(geometry2, {b: 10});

// 判断两个要素是否相交
var intersects = feature1.intersects(feature2, 'EPSG:4326');
print('intersects:', intersects);

// 在地图上显示两个要素
Map.addLayer(feature1, {color: '#000000'}, 'feature1');
Map.addLayer(feature2, {color: '#111111'}, 'feature2');
Map.setCenter(37, 12, 5);