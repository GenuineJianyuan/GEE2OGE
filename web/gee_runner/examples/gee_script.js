// Paste a Google Earth Engine Code Editor JavaScript script here.
// The runner converts it to the Python API internally before execution.
var point = ee.Geometry.Point([116.4074, 39.9042]);
var image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(point)
  .filterDate('2025-06-01', '2025-06-30')
  .median();

var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
print(ndvi);
