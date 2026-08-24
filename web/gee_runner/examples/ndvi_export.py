// Landsat 8 绿度归一化植被指数 (GNDVI) 计算
var point = ee.Geometry.Point([114.28, 30.57]);

var lc08 = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA')
  .filterBounds(point)
  .filterDate('2015-09-15', '2015-10-15')
  .sort('CLOUD_COVER')
  .first();

// GNDVI = (NIR - Green) / (NIR + Green) (B5 与 B3)
var gndvi = lc08.normalizedDifference(['B5', 'B3']);

var vis_params = {
  min: -0.2, 
  max: 0.8, 
  palette: ['gold', 'yellow', 'green', 'lightblue']
};

Map.setCenter(114.28, 30.57, 9);
Map.addLayer(gndvi, vis_params, 'GNDVI');