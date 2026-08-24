// 定义海南岛及周边处理范围
var bbox = ee.Geometry.Rectangle([108.5, 18.1, 111.0, 20.1]);

// GEE 中没有可直接对应的 ASTER_GDEM_DEM30 多景 DEM 集合，
// 此处使用约 30 m 分辨率的 NASADEM 作为等效 DEM 数据源。
var dem_collection = ee.ImageCollection.fromImages([
  ee.Image('NASA/NASADEM_HGT/001').select('elevation')
]).filterBounds(bbox);

// 1) DEM 合成，形成连续 DEM 表面。
// 原 OGE mosaic 的 "mean" 参数表示重叠区域取均值，
// 因此这里使用 ImageCollection.mean() 保留该统计逻辑。
var dem = dem_collection.mean().clip(bbox);

// 2) 对连续 DEM 做基础平滑：1 像元半径的方形邻域均值
var dem_base = dem.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.square({
    radius: 1,
    units: 'pixels',
    normalize: false
  }),
  skipMasked: true
});

// 3) 基于平滑后的 DEM 生成山体阴影。
// 保留 OGE 中传入的两个参数值：方位角 1°、太阳高度角 1°。
var hillshade = ee.Terrain.hillshade(dem_base, 1, 1);

// 可视化参数
var dem_vis = {
  min: 0,
  max: 1800,
  palette: ['#274e13', '#5b8a3c', '#b7b26a', '#d9c59a', '#f5f5f5']
};

var shade_vis = {
  min: 0,
  max: 255,
  palette: ['#1f1f1f', '#555555', '#8a8a8a', '#c0c0c0', '#f2f2f2']
};

// 输出结果：处理后的连续 DEM 与阴影结果对照展示
Map.addLayer(dem_base, dem_vis, 'dem_base');
Map.addLayer(hillshade, shade_vis, 'hillshade');

// 设置地图中心
Map.setCenter(109.7, 19.1, 9);