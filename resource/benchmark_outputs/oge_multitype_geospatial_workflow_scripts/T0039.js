// =========================
// 数据准备：请将两景 ASTER GDEM 上传为 GEE Assets，
// 并将以下资产路径替换为实际路径。
// 每个影像应包含一个高程波段（此处使用第 0 波段）。
// =========================

// =========================
// 1. 读取两景 ASTER DEM
// =========================
var dem1 = ee.Image('users/your_username/ASTGTM_N30E114')
  .select(0)
  .rename('elevation');

var dem2 = ee.Image('users/your_username/ASTGTM_N30E115')
  .select(0)
  .rename('elevation');

// =========================
// 2. 合并并镶嵌
// 宜昌附近位于 UTM 50N；统一到约 30 m 分辨率，
// 以便坡度和像元邻域计算使用米制空间参考。
// =========================
var dem_collection = ee.ImageCollection.fromImages([dem1, dem2]);

var dem_mosaic = dem_collection
  .mosaic()
  .reproject({
    crs: 'EPSG:32650',
    scale: 30
  });

// =========================
// 3. 构建局部相对高程位置指标
// 相对位置 = 原始 DEM - 邻域平均高程
// =========================
var dem_local_mean = dem_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle({
    radius: 9,
    units: 'pixels',
    normalize: false
  }),
  skipMasked: true
});

var relative_position = dem_mosaic.subtract(dem_local_mean)
  .rename('relative_position');

// 轻量平滑 relative_position，减少零散噪声。
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: ee.Kernel.circle({
    radius: 2,
    units: 'pixels',
    normalize: false
  }),
  skipMasked: true
}).rename('relative_position_smooth');

// =========================
// 4. 计算坡度（单位：度）
// =========================
var slope = ee.Terrain.slope(dem_mosaic).rename('slope');

// =========================
// 5. 相对位置分型
// 1: 谷地候选（<-10 m）
// 2: 中性（-10 至 10 m）
// 3: 山脊候选（>10 m）
// =========================
var position_class = relative_position_smooth.expression(
  '(rp < -10) ? 1 : ((rp <= 10) ? 2 : 3)',
  {rp: relative_position_smooth}
).rename('position_class').toByte();

// =========================
// 6. 坡度分组
// 1: 平缓区（<= 6°）
// 2: 坡面区（> 6°）
// =========================
var slope_class = slope.expression(
  '(s <= 6) ? 1 : 2',
  {s: slope}
).rename('slope_class').toByte();

// =========================
// 7. 联合编码
// 联合编码 = 相对位置类别 * 10 + 坡度类别
// 得到 11, 12, 21, 22, 31, 32
// =========================
var position_code = position_class.multiply(10);

var combined_class = position_code.add(slope_class)
  .rename('combined_class');

// =========================
// 8. 粗分基础地貌单元
// 1: 谷地带
// 2: 坡面带
// 3: 山脊带
// 4: 平坦过渡区
// =========================
var landform = combined_class.remap(
  [11, 12, 21, 22, 31, 32],
  [1,  1,  4,  2,  3,  3],
  0
).rename('landform').toByte();

// =========================
// 9. 轻量去碎斑
// =========================
var landform_smooth = landform.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: ee.Kernel.circle({
    radius: 1,
    units: 'pixels',
    normalize: false
  }),
  skipMasked: true
}).rename('landform_smooth').toByte();

// =========================
// 10. 可视化
// =========================
var position_vis = {
  min: 1,
  max: 3,
  palette: [
    '#2b83ba',  // 谷地候选
    '#f7f7f7',  // 中性
    '#d7191c'   // 山脊候选
  ]
};

var slope_vis = {
  min: 1,
  max: 2,
  palette: [
    '#d9f0d3',  // 平缓区
    '#fdae61'   // 坡面区
  ]
};

var landform_vis = {
  min: 1,
  max: 4,
  palette: [
    '#2b83ba',  // 谷地带
    '#fdae61',  // 坡面带
    '#d7191c',  // 山脊带
    '#cccccc'   // 平坦过渡区
  ]
};

Map.addLayer(position_class, position_vis, '相对位置类型结果');
Map.addLayer(slope_class, slope_vis, '坡度分组结果');
Map.addLayer(landform_smooth, landform_vis, '山脊-坡面-谷地基础粗分');

Map.setCenter(115.0, 30.5, 8);