// 加载 Landsat 8 影像
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// 选择 B3 波段
var temp = lc08.select('B3');

// 使用双线性插值重采样到 100 米分辨率
var idw = temp.resample('bilinear').reproject({
  crs: temp.projection(),
  scale: 100
});

// 可视化参数
var vis_params = {
  min: -1, 
  max: 1,
  palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']
};

// 在地图上显示结果
Map.addLayer(idw, vis_params, 'idw');

// 设置地图中心点
Map.setCenter(114.28, 30.57, 9);