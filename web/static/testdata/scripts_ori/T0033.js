// 加载 Landsat 9 Collection 2 Level 2 影像
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_L2SP_122039_20230306_20230308_02_T1');

// 选择地表温度波段
var st_b10 = lc09.select('ST_B10');

// 转换为浮点型
st_b10 = st_b10.toFloat();

// 应用缩放因子和偏移量计算开尔文温度
var lst_kelvin = st_b10.multiply(0.00341802).add(149.0);

// 转换为摄氏度
var lst_celsius = lst_kelvin.subtract(273.15);

// 计算与30°C的差值
var hot_delta = lst_celsius.subtract(30.0);

// 二值化：温度高于30°C的区域设为1，否则为0
var hot_mask = hot_delta.gt(0);

// 应用中值滤波平滑高温区域
hot_mask = hot_mask.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square(1)
});

// 地表温度可视化参数
var lst_vis = {
  min: 0,
  max: 32,
  palette: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#a50026']
};

// 高温区域可视化参数
var hot_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#b2182b']
};

// 添加图层到地图
Map.addLayer(lst_celsius, lst_vis, 'lst_celsius');
Map.addLayer(hot_mask, hot_vis, 'hot_mask');

// 设置地图中心
Map.setCenter(114.30, 30.57, 9);