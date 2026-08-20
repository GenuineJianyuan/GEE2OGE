// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
var lc08_d = lc08.toFloat();

// Select NIR and SWIR bands
var nir = lc08_d.select('B5');
var swir = lc08_d.select('B6');

// Calculate NBR (Normalized Burn Ratio)
var nbr = lc08_d.normalizedDifference(['B5', 'B6']);

// Visualization parameters
var vis_params = {min: -1, max: 1, palette: ['red', 'yellow', 'green']};

// Add NBR layer to map
Map.addLayer(nbr, vis_params, 'NBR');

// Center map on the area of interest
Map.setCenter(114.28, 30.57, 9);