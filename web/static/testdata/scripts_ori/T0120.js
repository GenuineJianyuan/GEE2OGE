// 创建要素集合
var features = [
  ee.Feature(ee.Geometry.Polygon([[[35, 10], [35, 15], [40, 15], [40, 10], [35, 10]]]), {a: '10'}),
  ee.Feature(ee.Geometry.Polygon([[[38, 10], [38, 15], [43, 15], [43, 10], [38, 10]]]), {a: '20'}),
  ee.Feature(ee.Geometry.Polygon([[[36, 11], [36, 14], [39, 14], [39, 11], [36, 11]]]), {a: '30'}),
  ee.Feature(ee.Geometry.Polygon([[[34, 12], [34, 14], [37, 14], [37, 12], [34, 12]]]), {a: '40'})
];

// 创建要素集合
var featureCollection = ee.FeatureCollection(features);

// 统计要素数量
var count = featureCollection.size();

// 输出结果到控制台
print('要素数量:', count);

// 设置地图中心点
Map.setCenter(37, 12, 5);