// 加载三景 Landsat 8 影像（使用 C02 级别 TOA 数据）
var image_1 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123035_20160504');
var image_2 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123036_20160504');
var image_3 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123037_20160504');

// 选择 B3 波段（绿色波段）
var band_1 = image_1.select('B3');
var band_2 = image_2.select('B3');
var band_3 = image_3.select('B3');

// 合并为 ImageCollection
var coverage_collection = ee.ImageCollection([band_1, band_2, band_3]);

// 使用均值合成生成原始拼接影像
var original_mosaic = coverage_collection.mosaic();

// 重投影到 Web Mercator (EPSG:3857)，分辨率 60 米
var standard_mosaic = original_mosaic.reproject({
  crs: 'EPSG:3857',
  scale: 60
});

// 应用中值滤波（圆形核，半径 1 像素）
var final_mosaic = standard_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.circle(1)
});

// 可视化参数（灰度渐变）
var vis_params = {
  min: 0,
  max: 0.3,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 添加图层到地图
Map.addLayer(original_mosaic, vis_params, 'original_mosaic');
Map.addLayer(final_mosaic, vis_params, 'standardized_mosaic');

// 设置地图中心（豫东地区）
Map.setCenter(114.95, 34.60, 8);