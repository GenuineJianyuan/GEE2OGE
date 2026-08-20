// Load Landsat 8 TOA image
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// Select the green band (B3)
var target_band = ls8.select('B3');

// Apply focal mean (smoothing) with a square kernel of radius 1
var smooth_band = target_band.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// Create a Prewitt kernel for edge detection
var kernel = ee.Kernel.prewitt({magnitude: 1.0, normalize: true});

// Apply convolution for edge enhancement
var enhanced_band = smooth_band.convolve(kernel);

// Apply focal median with a circle kernel of radius 1 to reduce noise
var final_band = enhanced_band.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// Visualization parameters (grayscale palette)
var vis_params = {
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// Add layers to the map
Map.addLayer(target_band, vis_params, 'target_band');
Map.addLayer(smooth_band, vis_params, 'smooth_band');
Map.addLayer(enhanced_band, vis_params, 'enhanced_band');
Map.addLayer(final_band, vis_params, 'final_band');

// Center the map on Wuhan northeastern area
Map.setCenter(114.30, 30.61, 10);