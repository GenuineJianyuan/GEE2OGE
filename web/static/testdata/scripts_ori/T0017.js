// Load Landsat 9 Collection 2 Level-2 image
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// Select and scale surface reflectance bands
var original_image = lc09.select(['SR_B4', 'SR_B3', 'SR_B2'])
    .multiply(0.0000275)
    .add(-0.2);

// Extract NIR and Red bands for vegetation indices
var nir_band = lc09.select('SR_B5').multiply(0.0000275).add(-0.2);
var red_band = lc09.select('SR_B4').multiply(0.0000275).add(-0.2);

// Calculate NDVI (Normalized Difference Vegetation Index)
var ndvi_num = nir_band.subtract(red_band);
var ndvi_den = nir_band.add(red_band);
var ndvi = ndvi_num.divide(ndvi_den);

// Calculate SAVI (Soil Adjusted Vegetation Index) with L=0.5
var savi_den = ndvi_den.add(0.5);
var savi_base = ndvi_num.divide(savi_den);
var savi = savi_base.multiply(1.5);

// Apply focal median smoothing (3x3 window)
ndvi = ndvi.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

savi = savi.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// Visualization parameters
var original_vis = {
  min: 0.0,
  max: 0.3
};

var veg_vis = {
  min: 0,
  max: 0.8,
  palette: ['#d9c27a', '#b8d16b', '#7fbf7b', '#3a924a', '#005a32']
};

// Add layers to map
Map.addLayer(original_image, original_vis, 'original_image');
Map.addLayer(ndvi, veg_vis, 'ndvi');
Map.addLayer(savi, veg_vis, 'savi');

// Center map on Hubei eastern region
Map.setCenter(115.35899045035, 30.296925757799997, 11);