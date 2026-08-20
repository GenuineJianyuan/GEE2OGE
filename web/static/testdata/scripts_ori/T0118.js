// 创建多点几何
var geometry = ee.Geometry.MultiPoint([[35, 10], [35, 15], [40, 15]]);

// 从几何创建要素并添加属性
var feature = ee.Feature(geometry, {a: 10});

// 计算凸包
var convexHull = feature.convexHull();

// 在地图上显示原始点
Map.addLayer(feature, {color: '#FFFF00'}, 'feature');

// 在地图上显示凸包
Map.addLayer(convexHull, {color: '#000000'}, 'convexHull');

// 设置地图中心
Map.setCenter(38, 13, 5);