// Load Landsat 8 TOA image
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Convert to float
lc08 = lc08.toFloat();

// Calculate NDWI (Green - NIR) / (Green + NIR)
var ndwi = lc08.normalizedDifference(['B3', 'B5']);
ndwi = ndwi.multiply(100.0);

// Binarization: threshold at 10 (equivalent to NDWI > 0.1)
var Ndwi_binarization = ndwi.gt(10);

// Apply focal median filter (3x3 square kernel)
var Ndwi_binarization_Median = Ndwi_binarization.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// Visualization parameters
var vis_params = {
  min: 0,
  max: 1,
  palette: ['black', '#87CEFA']
};

// Add water layer to map
Map.addLayer(Ndwi_binarization_Median, vis_params, 'water');

// Center map on the area of interest
Map.setCenter(114.28, 30.57, 9);