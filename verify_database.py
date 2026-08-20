"""验证数据库内容"""
import sys
sys.path.insert(0, r'd:\docs\交投\文档\全球院工作\geeToOGE')
from db_dao import GeeOgeDao

dao = GeeOgeDao()

print("=" * 70)
print("数据库统计信息")
print("=" * 70)
stats = dao.get_statistics()
for k, v in stats.items():
    if isinstance(v, dict):
        print(f"\n{k}:")
        for k2, v2 in v.items():
            print(f"  {k2}: {v2}")
    else:
        print(f"{k}: {v}")

print("\n" + "=" * 70)
print("类映射示例（前 5 条）")
print("=" * 70)
mappings = dao.get_all_class_mappings()[:5]
for m in mappings:
    print(f"  {m['gee_class']} -> {m['oge_class']} (valid={m['is_valid']})")

print("\n" + "=" * 70)
print("查询示例：ee.Image.abs 的映射")
print("=" * 70)
result = dao.get_mapping_by_gee_name('ee.Image.abs')
if result:
    print(f"  GEE: {result['gee_api']['api_full_name']}")
    print(f"  OGE: {result['oge_api']['api_name'] if result['oge_api'] else 'N/A'}")
    print(f"  类型: {result['mapping_type']}")
    print(f"  置信度: {result['confidence']}")
else:
    print("  未找到")

print("\n" + "=" * 70)
print("查询示例：ee.List.map 的 Python 实现")
print("=" * 70)
result = dao.get_mapping_by_gee_name('ee.List.map')
if result:
    print(f"  GEE: {result['gee_api']['api_full_name']}")
    print(f"  类型: {result['mapping_type']}")
    if result['native_python_code']:
        # 只显示前 5 行
        lines = result['native_python_code'].splitlines()[:5]
        for line in lines:
            print(f"  {line}")
else:
    print("  未找到")

print("\n" + "=" * 70)
print("按映射类型统计")
print("=" * 70)
for mt in ['one_to_one', 'one_to_many', 'many_to_one', 'native_python', 'missing']:
    mappings = dao.get_mappings_by_type(mt)
    print(f"\n{mt} ({len(mappings)} 条):")
    for m in mappings[:3]:
        gee = m['gee_api']['api_full_name'] if m['gee_api'] else 'N/A'
        oge = m['oge_api']['api_name'] if m['oge_api'] else 'N/A'
        print(f"  {gee} -> {oge}")

dao.close()
