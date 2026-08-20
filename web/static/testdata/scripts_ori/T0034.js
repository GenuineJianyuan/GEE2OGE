// 宜昌附近山地—丘陵区域基础地形层次分带
// 基于 ALOS PALSAR DEM 12.5m 数据

// 加载 DEM 数据（使用 GEE 中可用的 ALOS 数据集）
var dem1 = ee.Image('JAXA/ALOS/AW3D30_V1_1');
var dem2 = ee.Image('JAXA/ALOS/AW3D30_V1_1');

// 由于 GEE 中无法直接按图幅编号加载，这里使用研究区范围裁剪
var region = ee.Geometry.Rectangle([110.5, 30.0, 111.5, 31.0]);

// 获取研究区 DEM
var dem = dem1.clip(region);

// 计算坡度（度）
var slope = ee.Terrain.slope(dem);

// 定义无效值
var NaN_value = 0;

// 高程分级规则
var elev_rules = [
    {from: 0.0, to: 300.0, value: 1.0},
    {from: 300.0, to: 800.0, value: 2.0},
    {from: 800.0, to: 5000.0, value: 3.0}
];

// 高程重分类
var elev_class = ee.Image(1).where(dem.gt(0).and(dem.lte(300)), 1)
    .where(dem.gt(300).and(dem.lte(800)), 2)
    .where(dem.gt(800), 3)
    .updateMask(dem.gt(0));

// 坡度分级规则
var slope_rules = [
    {from: 0.0, to: 8.0, value: 1.0},
    {from: 8.0, to: 20.0, value: 2.0},
    {from: 20.0, to: 90.0, value: 3.0}
];

// 坡度重分类
var slope_class = ee.Image(1).where(slope.gt(0).and(slope.lte(8)), 1)
    .where(slope.gt(8).and(slope.lte(20)), 2)
    .where(slope.gt(20), 3)
    .updateMask(slope.gt(0));

// 高程分级结果乘以10
var elev_class_x10 = elev_class.multiply(10);

// 组合分类结果
var combined_class = elev_class_x10.add(slope_class);

// 地形层次分带规则
var terrain_rules = [
    {from: 10.5, to: 11.5, value: 1.0},   // 低位平缓区
    {from: 11.5, to: 13.5, value: 2.0},   // 过渡区
    {from: 20.5, to: 21.5, value: 2.0},   // 过渡区
    {from: 21.5, to: 23.5, value: 3.0},   // 中高位起伏区
    {from: 30.5, to: 31.5, value: 3.0},   // 中高位起伏区
    {from: 31.5, to: 33.5, value: 4.0}    // 高位陡峻区
];

// 地形层次分带
var terrain_band = ee.Image(0).where(combined_class.gt(10.5).and(combined_class.lte(11.5)), 1)
    .where(combined_class.gt(11.5).and(combined_class.lte(13.5)), 2)
    .where(combined_class.gt(20.5).and(combined_class.lte(21.5)), 2)
    .where(combined_class.gt(21.5).and(combined_class.lte(23.5)), 3)
    .where(combined_class.gt(30.5).and(combined_class.lte(31.5)), 3)
    .where(combined_class.gt(31.5).and(combined_class.lte(33.5)), 4)
    .updateMask(combined_class.gt(0));

// 平滑处理（使用多数滤波）
var terrain_band_smooth = terrain_band.reduceNeighborhood({
    reducer: ee.Reducer.mode(),
    kernel: ee.Kernel.circle(1)
});

// 可视化参数
var dem_vis = {
    min: 0,
    max: 2000,
    palette: ['#1a1a1a', '#4d4d4d', '#808080', '#b3b3b3', '#d9d9d9', '#f2f2f2']
};

var slope_vis = {
    min: 1,
    max: 3,
    palette: ['#d9f0d3', '#fdae61', '#d73027']
};

var terrain_vis = {
    min: 1,
    max: 4,
    palette: ['#d9f0d3', '#fee08b', '#f46d43', '#a50026']
};

// 添加图层到地图
Map.addLayer(dem, dem_vis, 'DEM参考图层');
Map.addLayer(slope_class, slope_vis, '坡度分级结果');
Map.addLayer(terrain_band_smooth, terrain_vis, '基础地形层次分带');

// 设置地图中心
Map.setCenter(111.0, 30.5, 9);