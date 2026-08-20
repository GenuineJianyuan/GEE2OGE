// Load Landsat 8 TOA reflectance image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
var lc08_float = lc08.toFloat();

// Select green band (B3)
var green = lc08_float.select('B3');

// Select NIR band (B5)
var nir = lc08_float.select('B5');

// Calculate NDSSI: (NIR - Green) / (NIR + Green)
var numerator = nir.subtract(green);
var denominator = nir.add(green);
var ndssi = numerator.divide(denominator);

// Visualization parameters
var vis_params = {
    min: -1,
    max: 1,
    palette: [
        '#0000FF',
        '#00FFFF',
        '#00FF00',
        '#FFFF00',
        '#FF0000',
        '#800000'
    ]
};

// Add NDSSI layer to map
Map.addLayer(ndssi, vis_params, 'NDSSI Map');

// Center map on the study area
Map.setCenter(114.28, 30.57, 7);