"""
分析未映射的 GEE 算子，并为可 Python 实现的算子创建映射
"""
import sqlite3
import json
import os

# 路径配置
PROJECT_ROOT = r'd:\docs\交投\文档\全球院工作\geeToOGE'
DB_PATH = os.path.join(PROJECT_ROOT, 'resource', 'gee_oge.db')
GEE_JSON_PATH = os.path.join(PROJECT_ROOT, 'resource', 'gee.json')

def get_mapped_gee_apis():
    """获取已映射的 GEE API 列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 从 operator_mapping 表获取已映射的 GEE API
    cursor.execute('''
        SELECT g.api_full_name 
        FROM operator_mapping m
        JOIN gee_api_info g ON m.gee_api_id = g.id
    ''')
    mapped = set(row[0] for row in cursor.fetchall())
    
    conn.close()
    return mapped

def get_all_gee_apis():
    """获取所有 GEE API 列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, api_full_name, class_name, method_name FROM gee_api_info')
    apis = {}
    for row in cursor.fetchall():
        api_id, api_name, class_name, method_name = row
        apis[api_name] = {
            'id': api_id,
            'class_name': class_name,
            'method_name': method_name
        }
    
    conn.close()
    return apis

def analyze_unmapped_apis():
    """分析未映射的 API"""
    mapped = get_mapped_gee_apis()
    all_apis = get_all_gee_apis()
    
    unmapped = {}
    for api_name, api_info in all_apis.items():
        if api_name not in mapped:
            unmapped[api_name] = api_info
    
    return unmapped

def classify_unmapped_apis(unmapped):
    """分类未映射的 API"""
    # Python原生可实现的API模式
    python_native_patterns = {
        # 数学运算
        'abs', 'min', 'max', 'sqrt', 'log', 'exp', 'pow', 'sin', 'cos', 'tan',
        'floor', 'ceil', 'round', 'abs',
        
        # 字符串操作
        'cat', 'substring', 'indexOf', 'replace', 'toUpperCase', 'toLowerCase', 'trim',
        'split', 'join', 'slice',
        
        # 列表/数组操作
        'length', 'size', 'get', 'set', 'contains', 'indexOf', 'reverse', 'sort',
        'slice', 'splice', 'push', 'pop', 'shift', 'unshift', 'concat', 'join',
        
        # 对象操作
        'keys', 'values', 'entries', 'hasOwnProperty',
        
        # 类型转换
        'Number', 'String', 'Boolean', 'parseInt', 'parseFloat', 'toString',
        
        # 比较和逻辑
        'equals', 'notEquals', 'lt', 'lte', 'gt', 'gte', 'and', 'or', 'not',
        
        # 条件判断
        'if', 'case', 'switch',
        
        # 循环和迭代
        'map', 'filter', 'reduce', 'forEach', 'some', 'every', 'find', 'findIndex',
        
        # 日期操作
        'Date', 'parse', 'format',
        
        # JSON
        'parse', 'stringify',
    }
    
    # 可以用 Python 标准库实现的 API
    python_stdlib_patterns = {
        # 数学 (math 模块)
        'acos', 'asin', 'atan', 'atan2', 'sinh', 'cosh', 'tanh',
        
        # 随机数 (random 模块)
        'random',
        
        # 日期时间 (datetime 模块)
        'getDate', 'getMonth', 'getFullYear', 'getHours', 'getMinutes', 'getSeconds',
        'setDate', 'setMonth', 'setFullYear', 'setHours', 'setMinutes', 'setSeconds',
        'toDateString', 'toTimeString', 'toISOString',
        
        # 正则表达式 (re 模块)
        'match', 'search', 'test',
        
        # 文件和路径 (os, pathlib 模块)
        'path', 'basename', 'dirname', 'extname', 'join', 'resolve',
    }
    
    # 无法或极难用 Python 实现的 API (需要 OGE 底层支持)
    not_implementable_patterns = {
        # 地图可视化（需要前端支持）
        'Map.addLayer', 'Map.setCenter', 'Map.clear', 'Map.centerObject',
        'ui.Panel', 'ui.Button', 'ui.Label', 'ui.Slider', 'ui.Select',
        
        # 并行计算调度（需要引擎支持）
        'ee.Algorithms', 'ee.Reducer', 'ee.Join', 'ee.Kernel',
        
        # 特定的 GEE 云端功能
        'Export.table.toAsset', 'Export.table.toCloudStorage', 'Export.table.toDrive',
        'Export.image.toAsset', 'Export.image.toCloudStorage', 'Export.image.toDrive',
        'Export.video.toCloudStorage', 'Export.video.toDrive',
        
        # 机器学习模型训练和预测
        'ee.Classifier', 'ee.Clusterer', 'ee.ConfusionMatrix',
        
        # 复杂的影像处理算法
        'ee.Algorithms.Terrain', 'ee.Algorithms.HillShadow',
        'ee.Algorithms.Landsat', 'ee.Algorithms.Sentinel',
    }
    
    classifications = {
        'python_native': {},  # Python 原生可替代
        'python_stdlib': {},  # Python 标准库可替代
        'not_implementable': {},  # 无法实现
        'needs_oge_api': {},  # 需要 OGE API
    }
    
    for api_name, api_info in unmapped.items():
        # 检查 API 名称中的关键部分
        api_lower = api_name.lower()
        
        # 检查是否是 Python 原生可替代的
        is_python_native = False
        for pattern in python_native_patterns:
            if pattern.lower() in api_lower:
                is_python_native = True
                break
        
        # 检查是否是无法实现的
        is_not_implementable = False
        for pattern in not_implementable_patterns:
            if pattern in api_name:
                is_not_implementable = True
                break
        
        # 检查是否是 Python 标准库可替代的
        is_python_stdlib = False
        for pattern in python_stdlib_patterns:
            if pattern.lower() in api_lower:
                is_python_stdlib = True
                break
        
        # 分类
        if is_not_implementable:
            classifications['not_implementable'][api_name] = api_info
        elif is_python_native:
            classifications['python_native'][api_name] = api_info
        elif is_python_stdlib:
            classifications['python_stdlib'][api_name] = api_info
        else:
            classifications['needs_oge_api'][api_name] = api_info
    
    return classifications

def generate_python_mapping(api_name, api_info, classification_type):
    """生成 Python 映射记录"""
    mapping = {
        'gee_api': api_name,
        'gee_api_id': api_info.get('id'),
        'oge_api': None,
        'oge_api_id': None,
        'mapping_type': 'python_native' if classification_type in ['python_native', 'python_stdlib'] else 'needs_implementation',
        'confidence': 1.0 if classification_type == 'python_native' else 0.8,
        'combo_steps': None,
        'notes': f'[后实现] 可用Python原生实现',
        'example_code': '',
        'created_at': '2024-01-01',
        'updated_at': '2024-01-01',
    }
    
    # 根据分类生成示例代码
    if classification_type == 'python_native':
        mapping['example_code'] = generate_python_native_example(api_name, api_info)
    elif classification_type == 'python_stdlib':
        mapping['example_code'] = generate_python_stdlib_example(api_name, api_info)
    
    return mapping

def generate_python_native_example(api_name, api_info):
    """生成 Python 原生实现示例"""
    # 根据常见的 API 模式生成示例
    examples = {
        'abs': '# Python原生实现\nresult = abs(value)',
        'min': '# Python原生实现\nresult = min(a, b)',
        'max': '# Python原生实现\nresult = max(a, b)',
        'sqrt': '# Python原生实现\nresult = value ** 0.5',
        'log': '# Python原生实现\nimport math\nresult = math.log(value)',
        'sin': '# Python原生实现\nimport math\nresult = math.sin(value)',
        'cos': '# Python原生实现\nimport math\nresult = math.cos(value)',
        'length': '# Python原生实现\nresult = len(collection)',
        'size': '# Python原生实现\nresult = len(collection)',
        'cat': '# Python原生实现\nresult = str1 + str2',
        'substring': '# Python原生实现\nresult = string[start:end]',
        'contains': '# Python原生实现\nresult = item in collection',
    }
    
    for key, example in examples.items():
        if key in api_name.lower():
            return example
    
    return '# Python原生实现\n# 待补充具体实现'

def generate_python_stdlib_example(api_name, api_info):
    """生成 Python 标准库实现示例"""
    examples = {
        'random': '# Python标准库实现\nimport random\nresult = random.random()',
        'Date': '# Python标准库实现\nfrom datetime import datetime\nresult = datetime.now()',
        'parse': '# Python标准库实现\nimport json\nresult = json.loads(json_string)',
    }
    
    for key, example in examples.items():
        if key in api_name:
            return example
    
    return '# Python标准库实现\n# 待补充具体实现'

def insert_python_mappings(mappings):
    """插入映射记录到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    for mapping in mappings:
        try:
            # 插入到 operator_mapping 表
            # 使用 review_comment 存储 notes，native_python_code 存储 example_code
            cursor.execute('''
                INSERT INTO operator_mapping 
                (gee_api_id, oge_api_id, mapping_type, combo_steps, native_python_code, confidence, verification_status, review_comment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                mapping['gee_api_id'],
                mapping['oge_api_id'],
                mapping['mapping_type'],
                mapping.get('combo_steps', None),
                mapping['example_code'],
                mapping['confidence'],
                'pending',  # verification_status
                mapping['notes']  # review_comment
            ))
            inserted += 1
        except sqlite3.IntegrityError as e:
            print(f'跳过已存在的映射: {mapping["gee_api"]} - {e}')
    
    conn.commit()
    conn.close()
    
    return inserted

def main():
    """主函数"""
    print('=== 分析未映射的 GEE API ===')
    
    # 获取未映射的 API
    unmapped = analyze_unmapped_apis()
    print(f'未映射的 API 总数: {len(unmapped)}')
    
    # 分类
    classifications = classify_unmapped_apis(unmapped)
    
    print('\n=== 分类统计 ===')
    for category, apis in classifications.items():
        print(f'{category}: {len(apis)} 个')
    
    # 生成映射记录
    print('\n=== 生成 Python 映射记录 ===')
    mappings = []
    
    # 为 python_native 和 python_stdlib 分类生成映射
    for category in ['python_native', 'python_stdlib']:
        for api_name, api_info in classifications[category].items():
            mapping = generate_python_mapping(api_name, api_info, category)
            mappings.append(mapping)
    
    print(f'生成了 {len(mappings)} 条映射记录')
    
    # 插入数据库
    if mappings:
        print('\n=== 插入数据库 ===')
        inserted = insert_python_mappings(mappings)
        print(f'成功插入 {inserted} 条记录')
    
    # 输出无法实现的 API 列表（供参考）
    print('\n=== 无法实现的 API (跳过) ===')
    for api_name in list(classifications['not_implementable'].keys())[:10]:
        print(f'  - {api_name}')
    if len(classifications['not_implementable']) > 10:
        print(f'  ... 还有 {len(classifications["not_implementable"]) - 10} 个')
    
    print('\n=== 完成 ===')

if __name__ == '__main__':
    main()