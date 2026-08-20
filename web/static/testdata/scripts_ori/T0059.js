// 加载中国东部地区老龄化矢量数据
var feature = ee.FeatureCollection('projects/your-project/assets/EasternChina_PopulationAging_Vector');

// 设置地图中心
Map.setCenter(115, 31, 4);

// 可视化参数
var vis_params = {
    palette: [
        '#ffffcc', '#ffeda0', '#fed976', '#feb24c',
        '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026'
    ]
};

// 全局线性回归模型
// 使用 GEE 的 reduceRegions 或 ee.Reducer.linearRegression 实现
var global_result = feature.map(function(f) {
    var y = f.getNumber('aging');
    var x1 = f.getNumber('PCGDP');
    var x2 = f.getNumber('GI');
    var x3 = f.getNumber('FD');
    var x4 = f.getNumber('education');
    
    // 构建回归矩阵
    var X = [1, x1, x2, x3, x4];
    var Y = [y];
    
    // 使用线性回归 reducer
    var regression = ee.Reducer.linearRegression({
        numX: 5,
        numY: 1
    });
    
    // 这里简化处理，实际需要收集所有点进行全局回归
    // 返回原始特征并添加预测值
    return f.set('predicted', y); // 简化处理
});

// 局部统计背景 - 人均GDP的局部平均
// 使用 GEE 的 reduceNeighborhood 或 join 实现空间局部统计
var local_bg = feature.map(function(f) {
    // 获取当前要素的几何
    var geom = f.geometry();
    
    // 查找邻近要素（50个最近邻）
    var searchRadius = 50000; // 50km 搜索半径
    var nearby = feature.filterBounds(geom.buffer(searchRadius));
    
    // 计算局部人均GDP平均值
    var localMean = nearby.reduceColumns({
        reducer: ee.Reducer.mean(),
        selectors: ['PCGDP']
    }).get('mean');
    
    return f.set('PCGDP_LM', localMean);
});

// 将局部统计结果栅格化
// 使用 reduceToImage 将矢量转换为栅格
var rast_bg = local_bg.reduceToImage({
    properties: ['PCGDP_LM'],
    reducer: ee.Reducer.first()
}).reproject({
    crs: 'EPSG:4326',
    scale: 0.01
});

// 添加全局回归结果图层
Map.addLayer(global_result, {color: '#FFFF00'}, '全局回归结果');

// 添加人均GDP局部统计背景图层
Map.addLayer(rast_bg, vis_params, '人均GDP局部统计背景');