// Load Landsat 9 Collection 2 Level-2 image
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_L2SP_122039_20230306_20230308_02_T1');

// Select RGB bands for true color display
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// Select NIR and Red bands for NDVI calculation
var nir_band = lc09.select(['SR_B5']).toFloat();
var red_band = lc09.select(['SR_B4']).toFloat();

// Calculate NDVI
var numerator = nir_band.subtract(red_band);
var denominator = nir_band.add(red_band);
var ndvi = numerator.divide(denominator);

// Visualization parameters
var original_vis = {
  min: 0,
  max: 30000
};

var ndvi_vis = {
  min: 0,
  max: 0.8,
  palette: ['#d9c27a', '#b8d16b', '#7fbf7b', '#3a924a', '#005a32']
};

// Add layers to map
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndvi, ndvi_vis, 'ndvi');

// Center map on Hubei Eastern region
Map.setCenter(115.35899045035, 30.296925757799997, 11);