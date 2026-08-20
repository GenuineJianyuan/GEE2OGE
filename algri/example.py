"""algri 模块最小使用示例：不需要启动 Web、数据库或 LLM。"""

from migration_algorithms import analyze_gee_code
from remote_sensing_algorithms import canny_edge_detector, unit_scale


GEE_CODE = """
// 读取并计算 NDVI
var image = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_001001_20200101');
var ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI');
Map.addLayer(ndvi, {}, 'NDVI');
"""

# 按需从自己的知识库提供映射。这里仅演示简化映射。
MAPPINGS = {
    'ee.Image': {'mapping_type': 'one_to_one', 'oge_api': 'Coverage.load'},
    'ee.Image.normalizedDifference': {'mapping_type': 'one_to_many'},
    'ee.Image.rename': {'mapping_type': 'native_python'},
}


if __name__ == '__main__':
    result = analyze_gee_code(GEE_CODE, MAPPINGS)
    print(result['all_apis'])
    print(result['matching']['match_rate'])

    # 遥感算法可独立调用。
    # scaled = unit_scale(np.array([[0, 50, 100]]), 0, 100)
    # edges = canny_edge_detector(scaled)
