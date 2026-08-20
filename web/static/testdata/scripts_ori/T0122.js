// 创建两个面几何
var geometry1 = ee.Geometry.Polygon([[[35, 10], [35, 15], [40, 15], [40, 10], [35, 10]]], 'EPSG:4326');
var feature1 = ee.Feature(geometry1, {a: 10});

var geometry2 = ee.Geometry.Polygon([[[36, 11], [36, 14], [39, 14], [39, 11], [36, 11]]], 'EPSG:4326');
var feature2 = ee.Feature(geometry2, {a: 15});

// 创建要素集合
var featureCollection = ee.FeatureCollection([feature1, feature2]);

// 合并要素（union）
var result = featureCollection.union(1);

// 在地图上展示合并前后的结果
Map.addLayer(featureCollection, {color: '#000000'}, 'featureCollection');
Map.addLayer(result, {color: '#FF0000'}, 'result');

// 设置地图中心
Map.setCenter(37, 12, 5);