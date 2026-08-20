// 加载 Landsat 8 影像（使用 GEE 中的 Landsat 8 Collection 2 Level 1 数据集）
var lc08 = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_124040_20161129');

// 加载辅助环境数据（使用 GEE 中对应的数据集，这里使用 MODIS 土地覆盖类型作为替代）
var auxiliaryData = ee.Image('MODIS/006/MCD12Q1/2016_01_01').select('LC_Type1');

// 计算 LSWI（归一化水体指数，使用 B5 和 B6 波段）
var imageLSWI = lc08.normalizedDifference(['B5', 'B6']);

// 计算 NDVI（归一化植被指数，使用 B5 和 B4 波段）
var imageNDVI = lc08.normalizedDifference(['B5', 'B4']);

// 估算 NPP（使用 GEE 中的 NPP 估算模型，这里使用 MODIS NPP 产品作为替代）
var imageNPP = ee.Image('MODIS/006/MOD17A3HGF/2016_01_01').select('Npp');

// 可视化参数
var vis_params = {
  min: 0,
  max: 255,
  palette: ['#99d8c9', '#66c2a4', '#41ae76', '#238b45', '#005824']
};

// 设置地图中心点
Map.setCenter(113.2, 28.5, 8);

// 在地图上展示 NPP 结果
Map.addLayer(imageNPP, vis_params, 'NPP');