// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// 转换为浮点型
var lc08_d = lc08.toFloat();

// 选择 SWIR 和 NIR 波段
var swir = lc08_d.select('B6');
var nir = lc08_d.select('B5');

// 计算 NDBI
var numerator = swir.subtract(nir);
var denominator = swir.add(nir);
var ndbi = numerator.divide(denominator);

// 可视化参数
var vis_params = {
  min: -1,
  max: 0.2,
  palette: ['blue', 'lightblue', 'green', 'red']
};

// 添加图层到地图
Map.addLayer(ndbi, vis_params, 'NDBI');

// 设置地图中心
Map.setCenter(114.28, 30.57, 9);