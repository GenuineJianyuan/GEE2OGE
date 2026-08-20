// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151003');

// Select bands and convert to float
var lc08_d = lc08.toFloat();

// Select required bands
var swir1 = lc08_d.select('B6');
var red = lc08_d.select('B4');
var nir = lc08_d.select('B5');
var blue = lc08_d.select('B2');

// Calculate Urban Index (UI)
var numerator = swir1.add(red);
var denominator = nir.add(blue);
var ui = numerator.divide(denominator);

// Visualization parameters
var vis_params = {
  min: 0,
  max: 3,
  palette: [
    '#3D5AFE',
    '#2979FF',
    '#00B0FF',
    '#00E5FF',
    '#2E004B',
    '#6A00A3',
    '#9C27B0',
    '#D500F9',
    '#1DE9B6',
    '#00C853',
    '#64DD17',
    '#AEEA00',
    '#FFD600',
    '#FFAB00'
  ]
};

// Add layer to map
Map.addLayer(ui, vis_params, 'Urban Index (UI)');

// Center map
Map.setCenter(114.28, 30.57, 9);