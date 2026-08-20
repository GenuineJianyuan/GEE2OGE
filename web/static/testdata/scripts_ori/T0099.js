// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
var lc08_float = lc08.toFloat();

// Select NIR and SWIR bands
var nir = lc08_float.select('B5');
var swir = lc08_float.select('B6');

// Calculate NDMI
var numerator = nir.subtract(swir);
var denominator = nir.add(swir);
var ndmi = numerator.divide(denominator);

// Visualization parameters
var vis_params = {
    min: -1,
    max: 1,
    palette: ['#00008B', '#191970', '#0000CD', '#4169E1', '#1E90FF', '#00BFFF', '#87CEEB', '#B0E0E6', '#C0C0C0', '#A9A9A9',
              '#8B4513', '#D2691E', '#DAA520', '#F4A460', '#FFD700', '#7CFC00', '#32CD32', '#228B22', '#006400', '#004D00']
};

// Add NDMI layer to map
Map.addLayer(ndmi, vis_params, 'NDMI');

// Center map
Map.setCenter(114.28, 30.57, 9);