// Load Landsat 8 TOA reflectance image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
var lc08_float = lc08.toFloat();

// Select bands B6 (SWIR1) and B2 (Blue)
var b6 = lc08_float.select('B6');
var b2 = lc08_float.select('B2');

// Calculate SIWSI = (B6 - B2) / (B6 + B2)
var numerator_siwsi = b6.subtract(b2);
var denominator_siwsi = b6.add(b2);
var siwsi = numerator_siwsi.divide(denominator_siwsi);

// Calculate FMC = 130 * exp(-3.1784 * SIWSI)
var exp_input = siwsi.multiply(-3.1784);
var exp_term = exp_input.exp();
var fmc = exp_term.multiply(130.0);

// Visualization parameters
var fmc_vis_params = {
  min: 0,
  max: 100,
  palette: ["#7d4f9c", "#c72f4e", "#6bbd45", "#b859c0", "#c4a73d", "#6b77d6", "#d15d35", "#5dbaaf", "#d0417a", "#4c342e",
            "#3e7c4f", "#d04a97", "#c28d37", "#4a7bb5", "#9e3f2d", "#4e9e85", "#a855a0", "#7e7b32", "#a15050", "#8c4f7c"]
};

// Add layer to map
Map.addLayer(fmc, fmc_vis_params, 'Fuel Moisture Content (FMC)');

// Center map
Map.setCenter(114.28, 30.57, 9);