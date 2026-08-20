// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
var lc08_d = lc08.toFloat();

// Select green, red, and blue bands
var green = lc08_d.select('B3');
var red = lc08_d.select('B4');
var blue = lc08_d.select('B2');

// Calculate VARI numerator: green - red
var numerator = green.subtract(red);

// Calculate VARI denominator: green + red - blue
var denominator = green.add(red).subtract(blue);

// Add small epsilon to avoid division by zero
denominator = denominator.add(1e-7);

// Calculate VARI
var vari = numerator.divide(denominator);

// Visualization parameters
var vis_params = {
  min: -1,
  max: 1,
  palette: ['#00008B', '#191970', '#0000CD', '#4169E1', '#1E90FF', '#00BFFF', '#87CEEB', '#B0E0E6', '#C0C0C0', '#A9A9A9', '#1E3F8B', '#1560BD', '#DAA520', '#F4A460', '#FFD700', '#7CFC00', '#32CD32', '#228B22', '#006400', '#004D00']
};

// Add VARI layer to map
Map.addLayer(vari, vis_params, 'VARI');

// Center map
Map.setCenter(114.28, 30.57, 9);