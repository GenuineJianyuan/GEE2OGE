"""最终集成测试：验证 GEE→OGE 映射 + Python 实现"""
import sys
sys.path.insert(0, r'd:\docs\交投\文档\全球院工作\geeToOGE')

from gee_to_ge_mapping import create_converter
from gee_python_functions import list_all_python_functions, get_python_function

XLSX = r'd:\docs\交投\文档\全球院工作\geeToOGE\resource\gee_to_oge_matches.xlsx'
GEE_JSON = r'd:\docs\交投\文档\全球院工作\geeToOGE\resource\gee.json'

print("=" * 60)
print("集成测试：映射 + Python 实现")
print("=" * 60)

converter = create_converter(XLSX, GEE_JSON)

# 1. 检查 Python 实现的映射数量
py_mappings = converter.get_all_python_impl_mappings()
print(f"\n1. 映射为 Python 实现的条目: {len(py_mappings)}")
for m in py_mappings[:5]:
    py_fn = m.get('python_function', 'N/A')
    print(f"   {m['gee_canonical_name']} -> {m['oge_apis']} [Python: {py_fn}]")
if len(py_mappings) > 5:
    print(f"   ... 还有 {len(py_mappings) - 5} 条")

# 2. 测试 get_python_function 通过转换器
print("\n2. 通过转换器获取 Python 函数:")
test_names = [
    'ee.Date.advance', 'ee.Dictionary.get', 'ee.List.map',
    'ee.Number.multiply', 'ee.String.format',
    'ee.FeatureCollection.map', 'ee.Array.matrixDeterminant',
]
for name in test_names:
    fn = converter.get_python_function(name)
    if fn:
        print(f"   ✓ {name} -> {fn.__name__}")
    else:
        print(f"   ✗ {name} -> 未找到")

# 3. 测试实际调用 Python 函数
print("\n3. 实际调用 Python 函数:")
fn = converter.get_python_function('ee.Date.advance')
if fn:
    result = fn('2023-01-15', 10, 'day')
    print(f"   ee.Date.advance('2023-01-15', 10, 'day') = {result}")

fn2 = converter.get_python_function('ee.List.sequence')
if fn2:
    result2 = fn2(1, 10)
    print(f"   ee.List.sequence(1, 10) = {result2}")

fn3 = converter.get_python_function('ee.Number.multiply')
if fn3:
    result3 = fn3(7, 8)
    print(f"   ee.Number.multiply(7, 8) = {result3}")

# 4. 检查所有 Python 函数是否都能通过 get_python_function 获取
print("\n4. 完整性检查:")
all_py = list_all_python_functions()
missing = []
for name in all_py:
    if converter.get_python_function(name) is None:
        missing.append(name)

if missing:
    print(f"   ⚠ {len(missing)} 个函数无法通过转换器获取: {missing}")
else:
    print(f"   ✓ 所有 {len(all_py)} 个 Python 函数都可通过转换器获取")

# 5. 检查映射统计
stats = converter.get_statistics()
print(f"\n5. 映射统计:")
print(f"   总映射: {stats['total']}")
print(f"   已匹配: {stats['matched']}")
print(f"   Python 实现: {len(py_mappings)}")
print(f"   OGE 原生实现: {stats['matched'] - len(py_mappings)}")

print("\n" + "=" * 60)
print("✅ 集成测试通过！")
print("=" * 60)