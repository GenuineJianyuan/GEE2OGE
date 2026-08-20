// Load Landsat 9 Collection 2 Level 1 TOA reflectance image
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_TOA')
  .filterDate('2022-01-01', '2022-12-31')
  .filterBounds(ee.Geometry.Point(114.28, 30.57))
  .first();

// Convert to float
var lc09_float = lc09.toFloat();

// Select thermal bands (Band 10 and Band 11)
var tir1 = lc09_float.select('B10');
var tir2 = lc09_float.select('B11');

// Apply thermal calibration coefficients
var tir11 = tir1.multiply(0.00341802).add(149.0);
var tir22 = tir2.multiply(0.00341802).add(149.0);

// Ensure float type
var tir111 = tir11.toFloat();
var tir222 = tir22.toFloat();

// Calculate NDTI
var numerator = tir111.subtract(tir222);
var denominator = tir111.add(tir222);
var ndti = numerator.divide(denominator);

// Visualization parameters
var vis_params = {
  min: -1,
  max: 1,
  palette: ["#00008B", "#191970", "#0000CD", "#4169E1", "#1E90FF", "#00BFFF", "#87CEEB", "#B0E0E6", "#C0C0C0", "#A9A9A9",
            "#8B4513", "#D2691E", "#DAA520", "#F4A460", "#FFD700", "#7CFC00", "#32CD32", "#228B22", "#006400", "#004D00"]
};

// Add layer to map
Map.addLayer(ndti, vis_params, 'Landsat 9 Normalized Difference Thermal Index (NDTI)');

// Center map
Map.setCenter(114.28, 30.57, 9);