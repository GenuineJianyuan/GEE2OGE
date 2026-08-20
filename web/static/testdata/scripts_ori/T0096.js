// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_154031_20230906');

// 选择热红外波段 B10
var b10 = lc08.select('B10');

// 转换为浮点型
var b10_float = b10.toFloat();

// 计算亮度温度（BT）
var bt_b10 = b10_float.multiply(0.00341802).add(149.0);

// 转换为摄氏度
var lst_c = bt_b10.subtract(273.15);

// 可视化参数
var vis_params = {
  min: 0,
  max: 50,
  palette: [
    '#00008B', '#0000FF', '#00BFFF', '#40E0D0', '#90EE90', '#FFFF00',
    '#FFA500', '#FF4500', '#FF0000', '#8B0000', '#800080', '#FF00FF'
  ]
};

// 添加图层到地图
Map.addLayer(lst_c, vis_params, 'LST');

// 设置地图中心
Map.setCenter(69.3183884178, 41.7456513857, 8);