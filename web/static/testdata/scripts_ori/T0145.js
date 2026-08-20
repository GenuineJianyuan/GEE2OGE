// 加载 Sentinel-2 影像（使用 GEE 中对应的数据集和日期）
var s2 = ee.Image('COPERNICUS/S2_SR/20230805T030531_20230805T031026_T50RKV');

// 选择近红外波段（B08）和红边波段（B05）
var nir = s2.select('B8');
var red_edge = s2.select('B5');

// 转换为浮点型（GEE 中影像默认已是浮点型，此步骤可省略）
nir = nir.toFloat();
red_edge = red_edge.toFloat();

// 计算 NDVIre = (NIR - RedEdge) / (NIR + RedEdge)
var numerator = nir.subtract(red_edge);
var denominator = nir.add(red_edge);
var ndvire = numerator.divide(denominator);

// 地图展示
Map.setCenter(114.082827, 30.889395, 10);
Map.addLayer(ndvire, {min: 0, max: 0.8, palette: ['yellow', 'green']}, 'NDVIre');