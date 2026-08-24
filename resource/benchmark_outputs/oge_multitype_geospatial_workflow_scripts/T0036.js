// =========================
// 数据集与研究区准备
// =========================
// GEE 中没有与 ALOS_PALSAR_DEM12.5 完全一致的公开数据集，
// 此处使用 JAXA ALOS AW3D30 DSM（约 30 m）作为可用替代。
var demDataset = 'JAXA/ALOS/AW3D30/V4_1';

// =========================
// 1. 读取两景相邻 ALOS DEM
// =========================
var dem1 = ee.ImageCollection(demDataset)
  .filter(ee.Filter.eq('system:index', 'N030E110'))
  .select('DSM')
  .mosaic();

var dem2 = ee.ImageCollection(demDataset)
  .filter(ee.Filter.eq('system:index', 'N030E111'))
  .select('DSM')
  .mosaic();

// =========================
// 2. 合并并镶嵌
// =========================
var dem_collection = ee.ImageCollection.fromImages([dem1, dem2]);
var dem_mosaic = dem_collection.mosaic().rename('elevation');

// =========================
// 3. 计算局部起伏度（局部高差）
// 起伏度 = 邻域最大值 - 邻域最小值
// 保留原 OGE 代码实际使用的 circle radius=9（像元）
// =========================
var reliefKernel = ee.Kernel.circle({
  radius: 9,
  units: 'pixels',
  normalize: false
});

var focal_max = dem_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.max(),
  kernel: reliefKernel
});

var focal_min = dem_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.min(),
  kernel: reliefKernel
});

var local_relief = focal_max.subtract(focal_min).rename('local_relief');

// =========================
// 4. 计算粗糙度（TRI）
// 采用 GDAL 默认 Riley TRI 的等效近似：
// TRI = sqrt(sum((邻域高程 - 中心高程)^2))
// 使用 3 × 3 邻域，中心像元差值为 0，不影响计算结果。
// =========================
var triKernel = ee.Kernel.square({
  radius: 1,
  units: 'pixels',
  normalize: false
});

var neighborhood = dem_mosaic.neighborhoodToArray(triKernel);
var centerElevation = neighborhood.arrayGet([1, 1]);

var tri = neighborhood
  .subtract(centerElevation)
  .pow(2)
  .arrayReduce(ee.Reducer.sum(), [0, 1])
  .sqrt()
  .arrayGet([0, 0])
  .rename('TRI');

// =========================
// 5. 起伏度分级
// 1: 低起伏
// 2: 中起伏
// 3: 高起伏
// =========================
var relief_class = ee.Image(0)
  .updateMask(local_relief.mask())
  .where(local_relief.gte(0).and(local_relief.lt(40)), 1)
  .where(local_relief.gte(40).and(local_relief.lt(120)), 2)
  .where(local_relief.gte(120).and(local_relief.lt(5000)), 3)
  .updateMask(local_relief.gte(0).and(local_relief.lt(5000)))
  .rename('relief_class');

// =========================
// 6. TRI 分级
// 1: 低崎岖
// 2: 中崎岖
// 3: 高崎岖
// =========================
var tri_class = ee.Image(0)
  .updateMask(tri.mask())
  .where(tri.gte(0).and(tri.lt(5)), 1)
  .where(tri.gte(5).and(tri.lt(20)), 2)
  .where(tri.gte(20).and(tri.lt(2000)), 3)
  .updateMask(tri.gte(0).and(tri.lt(2000)))
  .rename('tri_class');

// =========================
// 7. 联合编码
// 联合编码 = 起伏等级 * 10 + TRI等级
// 得到 11,12,13,21,22,23,31,32,33
// =========================
var relief_code = relief_class.multiply(10).rename('relief_code');
var combined_class = relief_code.add(tri_class).rename('combined_class');

// =========================
// 8. 归并为最终复杂度等级
// 1: 低复杂度
// 2: 中复杂度
// 3: 高复杂度
// =========================
var complexity = ee.Image(0)
  .updateMask(combined_class.mask())
  .where(combined_class.eq(11), 1)
  .where(
    combined_class.eq(12)
      .or(combined_class.eq(13))
      .or(combined_class.eq(21))
      .or(combined_class.eq(22))
      .or(combined_class.eq(31)),
    2
  )
  .where(
    combined_class.eq(23)
      .or(combined_class.eq(32))
      .or(combined_class.eq(33)),
    3
  )
  .updateMask(combined_class.gte(11).and(combined_class.lte(33)))
  .rename('complexity');

// =========================
// 9. 对最终复杂度结果做轻量整理
// focalMode 适合分类结果去碎斑
// =========================
var complexity_smooth = complexity
  .focalMode(1, 'circle', 'pixels', 1)
  .rename('complexity_smooth');

// =========================
// 10. 可视化
// =========================
var relief_vis = {
  min: 1,
  max: 3,
  palette: [
    '#d9f0d3',
    '#fdae61',
    '#d73027'
  ]
};

var tri_vis = {
  min: 1,
  max: 3,
  palette: [
    '#edf8fb',
    '#b2e2e2',
    '#2c7fb8'
  ]
};

var complexity_vis = {
  min: 1,
  max: 3,
  palette: [
    '#d9f0d3',
    '#fdae61',
    '#d73027'
  ]
};

Map.addLayer(relief_class, relief_vis, '起伏度等级结果');
Map.addLayer(tri_class, tri_vis, '粗糙度等级结果');
Map.addLayer(complexity_smooth, complexity_vis, '地形复杂度等级图');

Map.setCenter(111.0, 30.5, 9);