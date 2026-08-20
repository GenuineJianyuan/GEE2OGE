// Load Landsat 8 TOA reflectance image
var image = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_125039_20150414');

// Select bands and convert to float
var cov_f = image.toFloat();

var nir = cov_f.select('B5');
var swir1 = cov_f.select('B6');
var red = cov_f.select('B4');

// Calculate NDVI
var ndvi_num = nir.subtract(red);
var ndvi_den = nir.add(red);
var ndvi_den_eps = ndvi_den.add(1e-6);
var ndvi = ndvi_num.divide(ndvi_den_eps);

// Calculate NDMI
var ndmi_num = nir.subtract(swir1);
var ndmi_den = nir.add(swir1);
var ndmi_den_eps = ndmi_den.add(1e-6);
var ndmi = ndmi_num.divide(ndmi_den_eps);

// Calculate FMC (Fuel Moisture Content)
var ndmi_x80 = ndmi.multiply(80.0);
var ndvi_x40 = ndvi.multiply(40.0);
var sum_ = ndmi_x80.add(ndvi_x40);
var fmc = sum_.add(10.0);

// Visualization parameters
var fmcVis = {
  min: 0, max: 300,
  palette: ['#8B0000', '#FF0000', '#FFA500', '#FFFF00', '#ADFF2F', '#00FF00', '#00CED1', '#0000FF']
};

var ndviVis = {
  min: -1, max: 1,
  palette: ['#0000FF', '#FFFFFF', '#00FF00']
};

var ndmiVis = {
  min: -1, max: 1,
  palette: ['#0000FF', '#FFFFFF', '#FF00FF']
};

// Add layers to map
Map.addLayer(fmc, fmcVis, 'FMC');
Map.addLayer(ndvi, ndviVis, 'NDVI_check');
Map.addLayer(ndmi, ndmiVis, 'NDMI_check');

// Center map
Map.setCenter(110.116692, 31.908943, 8);