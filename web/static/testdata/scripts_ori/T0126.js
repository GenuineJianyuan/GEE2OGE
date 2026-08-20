// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151003');

// Select bands B5 and B4
var b5 = lc08.select('B5');
var b4 = lc08.select('B4');

// Calculate OSAVI: (B5 - B4) / (B5 + B4 + 0.16)
var r1 = b5.subtract(b4);
var r2 = b5.add(b4);
var r3 = r2.add(0.16);
var OSAVI = r1.divide(r3);

// Visualization parameters
var vis_params = {
  min: -1, 
  max: 1, 
  palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']
};

// Add layer to map
Map.addLayer(OSAVI, vis_params, 'OSAVI');

// Center map
Map.setCenter(114.28, 30.57, 9);