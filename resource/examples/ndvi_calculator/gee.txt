// Winter
var winterImage = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_119038_20230104');

// Summer
var summerImage = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_119038_20220728');

// Winter bands
var winterRed = winterImage.select('B4');
var winterGreen = winterImage.select('B3');
var winterNir = winterImage.select('B5');
var winterSwir1 = winterImage.select('B6');

// Winter NDVI
var winterNdviNumerator = winterNir.subtract(winterRed); 
var winterNdviDenominator = winterNir.add(winterRed);  
var winterNdvi = winterNdviNumerator.divide(winterNdviDenominator).rename('Winter_NDVI');

// Winter GNDVI
var winterGndviNumerator = winterNir.subtract(winterGreen);
var winterGndviDenominator = winterNir.add(winterGreen);
var winterGndvi = winterGndviNumerator.divide(winterGndviDenominator).rename('Winter_GNDVI');

// Winter NDMI
var winterNdmiNumerator = winterNir.subtract(winterSwir1);
var winterNdmiDenominator = winterNir.add(winterSwir1);
var winterNdmi = winterNdmiNumerator.divide(winterNdmiDenominator).rename('Winter_NDMI');

// Summer bands
var summerRed = summerImage.select('B4');
var summerGreen = summerImage.select('B3');
var summerNir = summerImage.select('B5');
var summerSwir1 = summerImage.select('B6');

// Summer NDVI
var summerNdviNumerator = summerNir.subtract(summerRed);
var summerNdviDenominator = summerNir.add(summerRed);
var summerNdvi = summerNdviNumerator.divide(summerNdviDenominator).rename('Summer_NDVI');

// Summer GNDVI
var summerGndviNumerator = summerNir.subtract(summerGreen);
var summerGndviDenominator = summerNir.add(summerGreen);
var summerGndvi = summerGndviNumerator.divide(summerGndviDenominator).rename('Summer_GNDVI');

// Summer NDMI
var summerNdmiNumerator = summerNir.subtract(summerSwir1);
var summerNdmiDenominator = summerNir.add(summerSwir1);
var summerNdmi = summerNdmiNumerator.divide(summerNdmiDenominator).rename('Summer_NDMI');

// Style
var vis = {
  min: -1,
  max: 1,
  palette: ['blue', 'lightblue', 'green', 'yellow', 'red']
};

var ndmiVis = {
  min: -1,
  max: 1,
  palette: ['brown', 'yellow', 'lightgreen', 'green', 'darkgreen']
};

// Layers
Map.addLayer(winterNdvi, vis, 'Winter NDVI');
Map.addLayer(summerNdvi, vis, 'Summer NDVI');

Map.addLayer(winterGndvi, vis, 'Winter GNDVI');
Map.addLayer(summerGndvi, vis, 'Summer GNDVI');

Map.addLayer(winterNdmi, ndmiVis, 'Winter NDMI');
Map.addLayer(summerNdmi, ndmiVis, 'Summer NDMI');

// Center
Map.setCenter(120.5, 32.0, 9);
