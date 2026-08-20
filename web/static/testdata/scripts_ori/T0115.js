// 创建线几何
var lineGeometry = ee.Geometry.LineString([[114.2, 30.3], [115.4, 30.8], [115.9, 31]]);

// 创建线要素
var line = ee.Feature(lineGeometry, {a: 10});

// 生成缓冲区（0.5度）
var buffer = line.buffer(0.5);

// 在地图上显示缓冲区（红色）
Map.addLayer(buffer, {color: '#FF0000'}, 'buffer');

// 在地图上显示线（黄色）
Map.addLayer(line, {color: '#FFFF00'}, 'line');

// 设置地图中心
Map.setCenter(115, 30.7, 5);