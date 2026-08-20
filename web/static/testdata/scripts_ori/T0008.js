// 加载 Landsat 8 两景影像
var image_a = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123036_20160504');
var image_b = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123037_20160504');

// 选择绿色波段 (B3)
var band_a = image_a.select('B3');
var band_b = image_b.select('B3');

// 获取原始投影信息
var crs_a = band_a.projection();
var crs_b = band_b.projection();

// 重投影到 Web Mercator (EPSG:3857)，分辨率 30 米
var standard_a = band_a.reproject({
  crs: 'EPSG:3857',
  scale: 30
});

var standard_b = band_b.reproject({
  crs: 'EPSG:3857',
  scale: 30
});

// 可视化参数
var vis_params = {
  min: 0,
  max: 0.3,
  palette: ['#1f1f1f', '#5a5a5a', '#9a9a9a', '#d9d9d9', '#ffffff']
};

// 添加到地图
Map.addLayer(standard_a, vis_params, 'standard_a');
Map.addLayer(standard_b, vis_params, 'standard_b');

// 设置地图中心
Map.setCenter(114.74, 33.88, 8);

// 打印投影信息以便确认
print('CRS of band_a:', crs_a);
print('CRS of band_b:', crs_b);