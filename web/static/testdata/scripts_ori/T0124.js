// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20150928');

// Convert to float
var lc08_d = lc08.toFloat();

// Calculate NDWI using Green (B3) and NIR (B5)
var ndwi = lc08_d.normalizedDifference(['B3', 'B5']);

// Visualization parameters
var vis_params = {min: -1, max: 1, palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']};

// Add layer to map
Map.addLayer(ndwi, vis_params, 'NDWI');

// Center map
Map.setCenter(114.28, 30.57, 9);

// Export NDWI image
Export.image.toDrive({
  image: ndwi,
  description: 'ndwi',
  scale: 30,
  maxPixels: 1e13
});