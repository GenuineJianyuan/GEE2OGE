// =========================
// 1. 读取两景 DEM（使用 NASADEM 30 m 数据替代 GEE 中不可直接访问的 ASTER GDEM 瓦片）
// =========================
var dem1_geometry = ee.Geometry.Rectangle([114, 30, 115, 31]);
var dem2_geometry = ee.Geometry.Rectangle([115, 30, 116, 31]);

var dem1 = ee.ImageCollection('NASA/NASADEM_HGT/001')
  .filterBounds(dem1_geometry)
  .select('elevation')
  .mosaic()
  .clip(dem1_geometry);

var dem2 = ee.ImageCollection('NASA/NASADEM_HGT/001')
  .filterBounds(dem2_geometry)
  .select('elevation')
  .mosaic()
  .clip(dem2_geometry);

// =========================
// 2. 合并并镶嵌
// =========================
var dem_collection = ee.ImageCollection.fromImages([dem1, dem2]);

var dem_mosaic = dem_collection
  .mosaic()
  .rename('elevation');

// =========================
// 3. 计算局部相对高程
// 相对位置 = 中心像元高程 - 邻域平均高程
// =========================
var kernel9 = ee.Kernel.circle({
  radius: 9,
  units: 'pixels',
  normalize: false
});

var kernel2 = ee.Kernel.circle({
  radius: 2,
  units: 'pixels',
  normalize: false
});

var dem_local_mean = dem_mosaic.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: kernel9
});

var relative_position = dem_mosaic.subtract(dem_local_mean)
  .rename('relative_position');

// 轻量平滑，减少局部噪声
var relative_position_smooth = relative_position.reduceNeighborhood({
  reducer: ee.Reducer.mean(),
  kernel: kernel2
}).rename('relative_position_smooth');

// =========================
// 4. 计算坡度（单位：度）
// =========================
var slope = ee.Terrain.slope(dem_mosaic)
  .rename('slope');

// =========================
// 5. 相对位置分型
// 1：谷地候选；2：中性位置；3：山脊候选
// =========================
var position_class = ee.Image(2)
  .updateMask(relative_position_smooth.mask())
  .where(relative_position_smooth.lt(-10), 1)
  .where(relative_position_smooth.gt(10), 3)
  .rename('position_class');

// =========================
// 6. 坡度分组
// 1：平缓区；2：坡面区
// =========================
var slope_class = ee.Image(1)
  .updateMask(slope.mask())
  .where(slope.gte(6), 2)
  .rename('slope_class');

// =========================
// 7. 联合编码
// 相对位置类别 × 10 + 坡度类别
// =========================
var position_code = position_class.multiply(10)
  .rename('position_code');

var combined_class = position_code.add(slope_class)
  .rename('combined_class');

// =========================
// 8. 地貌单元归并
// 1：谷地带；2：坡面带；3：山脊带；4：平坦过渡区
// =========================
var landform = ee.Image(0)
  .updateMask(combined_class.mask())
  .where(combined_class.eq(11), 1)
  .where(combined_class.eq(12), 1)
  .where(combined_class.eq(21), 4)
  .where(combined_class.eq(22), 2)
  .where(combined_class.eq(31), 3)
  .where(combined_class.eq(32), 3)
  .updateMask(combined_class.gte(11).and(combined_class.lte(32)))
  .rename('landform');

// =========================
// 9. 轻量去碎斑
// =========================
var kernel1 = ee.Kernel.circle({
  radius: 1,
  units: 'pixels',
  normalize: false
});

var landform_smooth = landform.reduceNeighborhood({
  reducer: ee.Reducer.mode(),
  kernel: kernel1
}).rename('landform_smooth');

// =========================
// 10. 可视化
// =========================
var position_vis = {
  min: 1,
  max: 3,
  palette: ['#2b83ba', '#f7f7f7', '#d7191c']
};

var slope_vis = {
  min: 1,
  max: 2,
  palette: ['#d9f0d3', '#fdae61']
};

var landform_vis = {
  min: 1,
  max: 4,
  palette: ['#2b83ba', '#fdae61', '#d7191c', '#cccccc']
};

Map.addLayer(position_class, position_vis, '相对位置类型结果');
Map.addLayer(slope_class, slope_vis, '坡度分组结果');
Map.addLayer(landform_smooth, landform_vis, '山脊-坡面-谷地基础粗分');

Map.setCenter(115.0, 30.5, 8);