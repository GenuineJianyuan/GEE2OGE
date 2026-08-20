// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// 转换为浮点数
var lc08_f = lc08.toFloat();

// 选择绿波段和近红外波段
var green = lc08_f.select('B3');
var nir = lc08_f.select('B5');

// 计算比值 (NIR/Green)
var ratio = nir.divide(green);

// CIgreen = NIR/Green - 1
var cigreen = ratio.subtract(1.0);

// 叶绿素浓度 = CIgreen * 50 + 5
var chl = cigreen.multiply(50.0).add(5.0);

// 可视化参数
var vis_params = {
    min: 0,
    max: 100,
    palette: [
        '#000000', '#1a9850', '#66bd63', '#d9ef8b',
        '#fee08b', '#f46d43', '#d73027', '#a50026'
    ]
};

// 添加图层到地图
Map.addLayer(chl, vis_params, '叶绿素浓度反演（CIgreen模型）');

// 设置地图中心
Map.setCenter(114.28, 30.57, 8);