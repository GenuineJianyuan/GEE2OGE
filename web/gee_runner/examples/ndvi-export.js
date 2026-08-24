// 将你在 Earth Engine Code Editor 中的核心处理逻辑放在这里。
const point = ee.Geometry.Point([116.4074, 39.9042]);
const image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(point)
  .filterDate('2025-06-01', '2025-06-30')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
  .median();

const ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
print('NDVI image', ndvi);

Export.image.toDrive({
  image: ndvi,
  description: 'beijing_ndvi_202506',
  folder: 'gee_exports',
  region: point.buffer(10000).bounds(),
  scale: 10,
  maxPixels: 1e10,
});
