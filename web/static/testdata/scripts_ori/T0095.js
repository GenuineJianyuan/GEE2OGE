// Load Landsat 9 Level-2 image
var lc09_l2 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_L2SP_122039_20241002_20241003_02_T1');

// Convert to float and apply scaling factors
var lc09_float = lc09_l2.toFloat();
var lc09_scaled = lc09_float.multiply(0.0000275);
var lc09_ref = lc09_scaled.subtract(0.2);

// Select NIR and Red bands
var nir = lc09_ref.select('SR_B5');
var red = lc09_ref.select('SR_B4');

// Calculate SAVI
var numerator = nir.subtract(red);
var nir_plus_red = nir.add(red);
var denominator = nir_plus_red.add(0.5);
var base = numerator.divide(denominator);
var savi = base.multiply(1.5);

// Visualization parameters
var vis_params = {
    min: -0.2,
    max: 0.6,
    palette: [
        '#3366CC',
        '#8B4513',
        '#D2691E',
        '#F4A460',
        '#F0E68C',
        '#ADFF2F',
        '#32CD32',
        '#006400'
    ]
};

// Add SAVI layer to map
Map.addLayer(savi, vis_params, 'SAVI_Soil_Adjusted');

// Center map on the area of interest
Map.setCenter(115.37146575130001, 30.297077919000003, 11);