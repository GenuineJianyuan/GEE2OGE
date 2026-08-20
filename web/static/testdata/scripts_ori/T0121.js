// 创建要素集合
var features = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Polygon([[[35, 10], [35, 15], [40, 15], [40, 10], [35, 10]]]), {a: '10'}),
  ee.Feature(ee.Geometry.Polygon([[[38, 10], [38, 15], [43, 15], [43, 10], [38, 10]]]), {a: '20'}),
  ee.Feature(ee.Geometry.Polygon([[[36, 11], [36, 14], [39, 14], [39, 11], [36, 11]]]), {a: '30'}),
  ee.Feature(ee.Geometry.Polygon([[[34, 12], [34, 14], [37, 14], [37, 12], [34, 12]]]), {a: '40'})
]);

// 统计属性 'a' 的不同取值数量
var countDistinct = features.aggregate_count_distinct('a');
print('count_distinct:', countDistinct);

// 在地图上展示要素集合
Map.addLayer(features, {color: '#0000ff'}, 'featureCollection');
Map.setCenter(37, 12, 5);