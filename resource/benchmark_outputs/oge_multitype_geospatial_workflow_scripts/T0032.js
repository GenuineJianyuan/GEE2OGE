// 读取 Landsat 9 Collection 2 Level-2 温度产品
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 1) 提取地表温度主结果层
var st_b10 = lc09.select(['ST_B10']);

// 2) 转换为浮点型
st_b10 = st_b10.toFloat();

// 3) 生成基础地表温度结果（摄氏度）
// Kelvin = DN * 0.00341802 + 149.0
// Celsius = Kelvin - 273.15
var lst_kelvin = st_b10.multiply(0.00341802).add(149.0);
var lst_celsius = lst_kelvin.subtract(273.15);

// 4) 对温度结果做相对热差异整理
// 以 15°C 为温和基准，仅保留偏热部分
var warm_delta = lst_celsius.subtract(15.0);
var warm_mask = warm_delta.gt(0);
warm_delta = warm_delta.multiply(warm_mask);

// 5) 生成更适合城郊对比的热差异强化结果
var heat_contrast = warm_delta.pow(2.0);

// 可视化参数
var lst_vis = {
  min: 0,
  max: 32,
  palette: ['313695', '74add1', 'e0f3f8', 'fee090', 'f46d43', 'a50026']
};

var contrast_vis = {
  min: 0,
  max: 225,
  palette: ['f7f7f7', 'fee08b', 'f46d43', 'd73027', '7f0000']
};

// 6) 将基础温度结果和热差异强化结果添加到地图
Map.addLayer(lst_celsius, lst_vis, 'lst_celsius');
Map.addLayer(heat_contrast, contrast_vis, 'heat_contrast');

// 设置地图中心
Map.setCenter(114.30, 30.57, 9);