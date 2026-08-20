// Load the DEM data from GEE
var dem = ee.Image('NASA/ASTER_GED/AG100_V003');

// Calculate aspect using GEE Terrain module
var aspect = ee.Terrain.aspect(dem);

// Visualization parameters
var vis_params = {
  min: -1,
  max: 1,
  palette: ['#808080', '#949494', '#a9a9a9', '#bdbebd', '#d3d3d3', '#e9e9e9']
};

// Add layer to map
Map.addLayer(aspect, vis_params, 'terrAspect');

// Center the map
Map.setCenter(56.25, 28.40, 11);

// Export the aspect image
Export.image.toDrive({
  image: aspect,
  description: 'terrAspect',
  scale: 30,
  maxPixels: 1e13
});