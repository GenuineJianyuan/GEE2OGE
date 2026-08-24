// 读取一景 Landsat 9 Collection 2 Level-2 温度产品
var lc09 = ee.Image('LANDSAT/LC09/C02/T1_L2/LC09_122039_20230306');

// 1) 提取地表温度主结果层
var st_b10 = lc09.select(['ST_B10']);

// 2) 转换为浮点型
st_b10 = st_b10.toFloat();

// 3) 生成基础地表温度结果（摄氏度）
// Kelvin = DN * 0.00341802 + 149.0
// Celsius = Kelvin - 273.15
var lst_kelvin = st_b10.multiply(0.00341802);
lst_kelvin = lst_kelvin.add(149.0);
var lst_celsius = lst_kelvin.subtract(273.15).rename('lst_celsius');

// 4) 对温度结果做较严格的高温阈值划分，生成初步高温区
// 使用 30°C 作为起始阈值：温度大于等于 30°C 的像元记为 1
var hot_delta = lst_celsius.subtract(30.0);
var hot_mask = hot_delta.gte(0).rename('hot_mask');

// 5) 对初步高温区做基础清理：1 像元半径的方形窗口中值滤波
hot_mask = hot_mask.reduceNeighborhood({
  reducer: ee.Reducer.median(),
  kernel: ee.Kernel.square({
    radius: 1,
    units: 'pixels',
    normalize: false
  })
}).rename('hot_mask');

// 可视化参数
var lst_vis = {
  min: 0,
  max: 32,
  palette: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#f46d43', '#a50026']
};

var hot_vis = {
  min: 0,
  max: 1,
  palette: ['#f5f5f5', '#b2182b']
};

// 6) 将基础温度结果和高温区结果添加到地图
Map.addLayer(lst_celsius, lst_vis, 'lst_celsius');
Map.addLayer(hot_mask, hot_vis, 'hot_mask');

// 设置地图中心
Map.setCenter(114.30, 30.57, 9);