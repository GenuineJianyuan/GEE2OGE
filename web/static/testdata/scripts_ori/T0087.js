// 加载 Landsat 8 影像
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_122039_20151002');

// 获取影像的投影/坐标参考系统信息
var crs = ls8.projection();

// 打印投影信息
print('投影/坐标参考系统信息:', crs);

// 将影像添加到地图上显示
Map.setCenter(114.30, 30.57, 9);
Map.addLayer(ls8, {bands: ['B4', 'B3', 'B2'], min: 0, max: 0.3}, 'Landsat 8 影像');