// 加载 Landsat 8 影像
var ls8 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC81220392015275LGN00');

// 选择 B3 波段
var b3 = ls8.select('B3');

// 使用 3x3 方形核进行均值滤波
var a = b3.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square(1)
});

// 可视化参数
var vis_params = {
  min: -1,
  max: 1,
  palette: ['gold', 'yellow', 'brown', 'lightblue', 'blue']
};

// 添加图层到地图
Map.addLayer(a, vis_params, 'a');

// 设置地图中心
Map.setCenter(114.30, 30.57, 9);

// 导出结果（可选）
Export.image.toDrive({
  image: a,
  description: 'a',
  scale: 30,
  region: a.geometry()
});