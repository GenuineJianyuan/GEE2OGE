// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LANDSAT_LC09_122039_20230306');

// 选择地表温度波段
var st_b10 = lc09.select('ST_B10');

// 转换为浮点型
st_b10 = st_b10.toFloat();

// 应用缩放因子和偏移量转换为开尔文温度
var lst_kelvin = st_b10.multiply(0.00341802).add(149.0);

// 转换为摄氏度
var lst_celsius = lst_kelvin.subtract(273.15);

// 开尔文温度可视化参数
var kelvin_vis = {
  min: 270,
  max: 305,
  palette: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#a50026']
};

// 摄氏度可视化参数
var celsius_vis = {
  min: 0,
  max: 32,
  palette: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#a50026']
};

// 添加开尔文温度图层
Map.addLayer(lst_kelvin, kelvin_vis, 'lst_kelvin');

// 添加摄氏度温度图层
Map.addLayer(lst_celsius, celsius_vis, 'lst_celsius');

// 设置地图中心点和缩放级别
Map.setCenter(114.30, 30.57, 9);