// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Select bands
var red = lc08.select('B4');
var nir = lc08.select('B5');
var blue = lc08.select('B2');

// Apply gains, offsets, and sun correction
var Gain2 = 2.0000E-05;
var Gain4 = 2.0000E-05;
var Gain5 = 2.0000E-05;
var Offset2 = -0.100000;
var Offset4 = -0.100000;
var Offset5 = -0.100000;
var sun_corr = 1.277985;

var B2 = blue.multiply(Gain2).add(Offset2).multiply(sun_corr);
var B4 = red.multiply(Gain4).add(Offset4).multiply(sun_corr);
var B5 = nir.multiply(Gain5).add(Offset5).multiply(sun_corr);

// EVI calculation
var G = 2.5;
var L = 1;
var C1 = 6;
var C2 = 7.5;

var numerator = B5.subtract(B4);
var red_scaled = B4.multiply(C1);
var blue_scaled = B2.multiply(C2);
var denominator = red_scaled.subtract(blue_scaled).add(B5).add(L);
var evi_ratio = numerator.divide(denominator);
var evi = evi_ratio.multiply(G);

// LAI estimation
var LAI = evi.multiply(3.618).subtract(0.118);

// Visualization parameters
var vis_params = {
    min: 0,
    max: 10,
    palette: ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000', '#800000']
};

// Add layer to map
Map.addLayer(LAI, vis_params, 'LAI');
Map.setCenter(114.28, 30.57, 7);