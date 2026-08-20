// Load Landsat 8 TOA reflectance image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
var lc08_d = lc08.toFloat();

// Select SWIR (B6) and NIR (B5) bands
var swir = lc08_d.select('B6');
var nir = lc08_d.select('B5');

// Calculate Moisture Stress Index (MSI) = SWIR / NIR
var msi = swir.divide(nir);

// Visualization parameters
var vis_params = {
  min: -0.7,
  max: 1.8,
  palette: ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta']
};

// Add MSI layer to map
Map.addLayer(msi, vis_params, 'Moisture Stress Index (MSI)');

// Center map on the study area
Map.setCenter(114.28, 30.57, 9);