// 加载 Landsat 9 Collection 2 Level-2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 选择地表温度波段
var st_b10 = lc09.select('ST_B10');

// 转换为浮点型
st_b10 = st_b10.toFloat();

// 应用缩放因子和偏移量转换为开尔文温度
var lst_kelvin = st_b10.multiply(0.00341802).add(149.0);

// 转换为摄氏度
var lst_celsius = lst_kelvin.subtract(273.15);

// 计算与15°C的温差（热异常部分）
var warm_delta = lst_celsius.subtract(15.0);

// 创建掩膜，只保留正值（温度高于15°C的区域）
var warm_mask = warm_delta.gt(0);
warm_delta = warm_delta.multiply(warm_mask);

// 对温差进行平方运算以增强热对比度
var heat_contrast = warm_delta.pow(2);

// 地表温度可视化参数
var lst_vis = {
  min: 0,
  max: 32,
  palette: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#a50026']
};

// 热对比度可视化参数
var contrast_vis = {
  min: 0,
  max: 225,
  palette: ['#f7f7f7', '#fee08b', '#f46d43', '#d73027', '#7f0000']
};

// 添加图层到地图
Map.addLayer(lst_celsius, lst_vis, 'lst_celsius');
Map.addLayer(heat_contrast, contrast_vis, 'heat_contrast');

// 设置地图中心点
Map.setCenter(114.30, 30.57, 9);