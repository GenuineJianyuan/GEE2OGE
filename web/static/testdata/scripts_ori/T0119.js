// 创建线几何
var geometry1 = ee.Geometry.LineString([[35.1, 15.7], [36.3, 15.9], [37.5, 15.6]], 'EPSG:4326');
var feature1 = ee.Feature(geometry1, {a: 10});

var geometry2 = ee.Geometry.LineString([[35.2, 12.1], [36.4, 12.0], [37.6, 12.3]], 'EPSG:4326');
var feature2 = ee.Feature(geometry2, {a: 15});

// 创建要素集合
var featureCollection = ee.FeatureCollection([feature1, feature2]);

// 计算GeoHash编码（GEE没有内置GeoHash函数，使用自定义函数）
var geohash = function(feature) {
  var geom = feature.geometry();
  var coords = geom.coordinates();
  var geohashStr = '';
  // 简化版GeoHash实现（实际应用中需要完整的GeoHash算法）
  coords.forEach(function(coord) {
    geohashStr = geohashStr + coord.get(0).format('%.2f') + ',' + coord.get(1).format('%.2f') + ';';
  });
  return feature.set('geohash', geohashStr);
};

var result = featureCollection.map(geohash);

// 获取第一个要素的GeoHash结果
var first_geohash = result.aggregate_first('geohash');
print('第一个要素的GeoHash结果', first_geohash);

// 在地图上展示线要素
Map.addLayer(result, {color: '#FF0000'}, 'geoHash');
Map.setCenter(36.5, 14.0, 5);