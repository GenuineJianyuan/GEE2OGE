// 创建两条线要素并筛选
var coords1 = ee.List([[35.1, 15.7], [36.3, 15.9], [37.5, 15.6]]);
var geometry1 = ee.Geometry.LineString(coords1, 'EPSG:4326');
var feature1 = ee.Feature(geometry1, {a: 10});

var coords2 = ee.List([[35.2, 12.1], [36.4, 12.0], [37.6, 12.3]]);
var geometry2 = ee.Geometry.LineString(coords2, 'EPSG:4326');
var feature2 = ee.Feature(geometry2, {a: 15});

var featureCollection = ee.FeatureCollection([feature1, feature2]);
var result = featureCollection.filter(ee.Filter.greaterThan('a', 11));

Map.addLayer(result, {color: '#FF0000'}, 'result');
Map.setCenter(36.5, 14.0, 5);