// Load Landsat 8 TOA image
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// Select B3 band
var b3 = ls8.select('B3');

// Apply focal mean (smoothing) with square kernel of radius 1
var a = b3.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// Visualization parameters
var vis_params = {
  min: -1,
  max: 1,
  palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']
};

// Add layer to map
Map.addLayer(a, vis_params, 'Smoothed B3');

// Center map
Map.setCenter(114.30, 30.57, 9);