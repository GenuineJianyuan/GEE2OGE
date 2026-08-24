// 读取一景 Landsat 9 Collection 2 Level-2 温度产品
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 1) 提取地表温度主结果层
var st_b10 = lc09.select(['ST_B10']);

// 2) 转换为浮点型
st_b10 = st_b10.toFloat();

// 3) 生成更直观的地表温度表达图
// Landsat Collection 2 Level-2 Surface Temperature:
// Kelvin = DN * 0.00341802 + 149.0
// Celsius = Kelvin - 273.15
var lst_kelvin = st_b10.multiply(0.00341802).add(149.0);
var lst_celsius = lst_kelvin.subtract(273.15);

// 可视化参数
var kelvin_vis = {
  min: 270,
  max: 305,
  palette: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#a50026']
};

var celsius_vis = {
  min: 0,
  max: 32,
  palette: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#a50026']
};

// 4) 展示温度结果与温度表达图
Map.addLayer(lst_kelvin, kelvin_vis, 'lst_kelvin');
Map.addLayer(lst_celsius, celsius_vis, 'lst_celsius');

// 设置地图中心
Map.setCenter(114.30, 30.57, 9);