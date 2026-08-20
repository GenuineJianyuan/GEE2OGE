// 加载火灾前 Landsat 8 影像 (2016年)
var lc08_pre = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_127037_20160618');
var lc08_pre_d = lc08_pre.toFloat();

// 加载火灾后 Landsat 8 影像 (2019年)
var lc08_post = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_127037_20190101');
var lc08_post_d = lc08_post.toFloat();

// 计算火灾前 NBR
var nbr_pre = lc08_pre_d.normalizedDifference(['B5', 'B6']);

// 计算火灾后 NBR
var nbr_post = lc08_post_d.normalizedDifference(['B5', 'B6']);

// 计算燃烧严重性指数 (CSI) = NBR_pre - NBR_post
var csi = nbr_pre.subtract(nbr_post);

// 可视化参数
var vis_params = {
  min: -0.45,
  max: 0.45,
  palette: ['#808080', '#949494', '#a9a9a9', '#bdbebd', '#d3d3d3', '#e9e9e9']
};

// 在地图上展示 CSI 结果
Map.addLayer(csi, vis_params, 'CSI');
Map.setCenter(108.89, 34.00, 7);