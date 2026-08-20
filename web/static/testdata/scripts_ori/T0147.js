// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
var lc08_d = lc08.toFloat();

// Select bands
var red = lc08_d.select('B4');
var green = lc08_d.select('B3');
var nir = lc08_d.select('B5');
var blue = lc08_d.select('B2');

// Calculate BAEI = (Red + Green) / (NIR + Blue)
var numerator = red.add(green);
var denominator = nir.add(blue);
var baei = numerator.divide(denominator);

// Visualization parameters
var vis_params = {
  min: 0,
  max: 5,
  palette: ['#00008B', '#191970', '#0000CD', '#4169E1', '#1E90FF', '#00BFFF', '#87CEEB', '#B0E0E6', '#C0C0C0', '#A9A9A9', '#8B4513', '#D2691E', '#DAA520', '#F4A460', '#FFD700', '#7CFC00', '#32CD32', '#228B22', '#006400', '#004D00']
};

// Add layer to map
Map.addLayer(baei, vis_params, 'BAEI');

// Center map
Map.setCenter(114.28, 30.57, 9);