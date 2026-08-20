// Load the Landsat 9 Collection 2 Level-2 image
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// Select the original RGB bands
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2']);

// Select individual bands and convert to float
var green_band = lc09.select('SR_B3').toFloat();
var red_band = lc09.select('SR_B4').toFloat();
var nir_band = lc09.select('SR_B5').toFloat();
var swir1_band = lc09.select('SR_B6').toFloat();
var swir2_band = lc09.select('SR_B7').toFloat();

// Calculate NDVI
var ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band));

// Calculate NBR
var nbr = nir_band.subtract(swir2_band).divide(nir_band.add(swir2_band));

// Calculate NBR2
var nbr2 = swir1_band.subtract(swir2_band).divide(swir1_band.add(swir2_band));

// Calculate MNDWI
var mndwi = green_band.subtract(swir1_band).divide(green_band.add(swir1_band));

// First disturbance index: inverted NBR threshold
var nbr_inv = nbr.multiply(-100.0).add(17.0);
var candidate_nbr = nbr_inv.gt(0);

// Vegetation mask: NDVI > 0.22
var ndvi_scaled = ndvi.multiply(100.0);
var vegetation_mask = ndvi_scaled.gt(22);

// Water mask: MNDWI > 0.10
var mndwi_scaled = mndwi.multiply(100.0);
var water_mask = mndwi_scaled.gt(10);

// Non-water mask
var non_water_mask = water_mask.multiply(-1.0).add(1.0);

// Initial candidate: NBR anomaly AND vegetation AND non-water
var candidate_masked = candidate_nbr.multiply(vegetation_mask).multiply(non_water_mask);

// Second disturbance index: NBR2 anomaly
var nbr2_inv = nbr2.multiply(-100.0).add(8.0);
var candidate_nbr2 = nbr2_inv.gt(0);

// Priority raw: initial candidate AND NBR2 anomaly
var priority_raw = candidate_masked.multiply(candidate_nbr2);

// Apply focal median filter (3x3 window)
var priority_final = priority_raw.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// Visualization parameters
var original_vis = {};

var nbr_vis = {
  min: -0.2,
  max: 0.6,
  palette: ['#7f3b08', '#b35806', '#f1a340', '#fee0b6', '#d8daeb', '#998ec3', '#542788']
};

var nbr2_vis = {
  min: -0.2,
  max: 0.4,
  palette: ['#7f3b08', '#b35806', '#f1a340', '#fee0b6', '#d8daeb', '#998ec3', '#542788']
};

var mask_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#b2182b']
};

// Add layers to map
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(nbr, nbr_vis, 'nbr');
Map.addLayer(nbr2, nbr2_vis, 'nbr2');
Map.addLayer(candidate_masked, mask_vis, 'candidate_initial');
Map.addLayer(priority_final, mask_vis, 'priority_final');

// Center the map
Map.setCenter(115.35899045035, 30.296925757799997, 11);