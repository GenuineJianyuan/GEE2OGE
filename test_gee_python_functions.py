"""GEE Python 函数实现的全面测试脚本"""
import sys
import os
sys.path.insert(0, r'd:\docs\交投\文档\全球院工作\geeToOGE')

from gee_python_functions import (
    GEE_PYTHON_FUNCTIONS,
    get_python_function,
    list_all_python_functions,
    get_function_info,
    generate_implementation_table,
    # 日期函数
    ee_date, ee_date_advance, ee_date_day_of_year,
    ee_date_difference, ee_date_format, ee_date_get,
    ee_date_get_relative, ee_date_parse, ee_date_subtract,
    ee_date_range,
    # 字典函数
    ee_dictionary, ee_dictionary_get, ee_dictionary_get_info,
    ee_dictionary_set, ee_dictionary_to_list,
    # 列表函数
    ee_list, ee_list_contains, ee_list_filter, ee_list_flatten,
    ee_list_get, ee_list_group, ee_list_join, ee_list_map,
    ee_list_remove, ee_list_repeat, ee_list_sequence,
    ee_list_size, ee_list_slice, ee_list_sort, ee_listzip,
    # 数值函数
    ee_number, ee_number_divide, ee_number_format,
    ee_number_gte, ee_number_lte, ee_number_multiply,
    # 字符串函数
    ee_string, ee_string_format,
    # 数组函数
    ee_array, ee_array_matrix_determinant, ee_array_matrix_inverse,
    ee_array_matrix_trace,
    # 循环函数
    ee_feature_collection_map, ee_feature_collection_iterate,
    # 其他
    gee_print,
)


def test_print():
    """测试 print"""
    print("【测试 print】")
    gee_print("Hello from GEE Python!")
    print("  ✓ print 正常")


def test_date_functions():
    """测试日期相关函数"""
    print("\n【测试 ee.Date 系列函数】")

    # ee.Date
    dt1 = ee_date('2023-01-15')
    assert dt1.year == 2023 and dt1.month == 1 and dt1.day == 15
    print(f"  ✓ ee.Date('2023-01-15') = {dt1}")

    dt2 = ee_date(1672531200000)  # 毫秒时间戳
    print(f"  ✓ ee.Date(1672531200000) = {dt2}")

    # ee.Date.advance
    dt3 = ee_date_advance(dt1, 5, 'day')
    assert dt3.day == 20
    print(f"  ✓ advance(5, 'day') = {dt3}")

    dt4 = ee_date_advance(dt1, -1, 'month')
    assert dt4.month == 12 and dt4.year == 2022
    print(f"  ✓ advance(-1, 'month') = {dt4}")

    # ee.Date.dayOfYear
    doy = ee_date_day_of_year('2023-01-01')
    assert doy == 1
    print(f"  ✓ dayOfYear('2023-01-01') = {doy}")

    doy2 = ee_date_day_of_year('2023-12-31')
    assert doy2 == 365
    print(f"  ✓ dayOfYear('2023-12-31') = {doy2}")

    # ee.Date.difference
    diff = ee_date_difference('2023-01-15', '2023-01-01', 'day')
    assert diff == 14.0
    print(f"  ✓ difference('2023-01-15', '2023-01-01', 'day') = {diff}")

    # ee.Date.format
    fmt = ee_date_format('2023-01-15', '%Y-%m-%d')
    assert fmt == '2023-01-15'
    print(f"  ✓ format('%Y-%m-%d') = '{fmt}'")

    # ee.Date.get
    year = ee_date_get('2023-01-15', 'year')
    assert year == 2023
    month = ee_date_get('2023-01-15', 'month')
    assert month == 1
    print(f"  ✓ get('year') = {year}, get('month') = {month}")

    # ee.Date.getRelative
    rel = ee_date_get_relative('2023-01-15', 'day', 'month')
    assert rel == 14  # 0-基
    print(f"  ✓ getRelative('day', 'month') = {rel}")

    # ee.Date.parse
    parsed = ee_date_parse('%Y-%m-%d', '2023-06-15')
    assert parsed.month == 6 and parsed.day == 15
    print(f"  ✓ parse('%Y-%m-%d', '2023-06-15') = {parsed}")

    # ee.Date.subtract
    sub = ee_date_subtract('2023-01-15', 5, 'day')
    assert sub.day == 10
    print(f"  ✓ subtract(5, 'day') = {sub}")

    # ee.DateRange
    dr = ee_date_range('2023-01-01', '2023-12-31')
    assert 'start' in dr and 'end' in dr
    print(f"  ✓ DateRange: start={dr['start']}, end={dr['end']}")

    # 只有 start 的 DateRange
    dr2 = ee_date_range('2023-01-01')
    print(f"  ✓ DateRange('2023-01-01'): end={dr2['end']}")

    print("  ✓ 所有日期函数测试通过")


def test_dictionary_functions():
    """测试字典相关函数"""
    print("\n【测试 ee.Dictionary 系列函数】")

    # ee.Dictionary
    d1 = ee_dictionary({'a': 1, 'b': 2})
    assert d1 == {'a': 1, 'b': 2}
    print(f"  ✓ ee.Dictionary(dict) = {d1}")

    d2 = ee_dictionary([['x', 10], ['y', 20]])
    assert d2 == {'x': 10, 'y': 20}
    print(f"  ✓ ee.Dictionary(list) = {d2}")

    d3 = ee_dictionary()
    assert d3 == {}
    print(f"  ✓ ee.Dictionary() = {d3}")

    # ee.Dictionary.get
    val = ee_dictionary_get(d1, 'a')
    assert val == 1
    val_def = ee_dictionary_get(d1, 'c', 'default')
    assert val_def == 'default'
    print(f"  ✓ get('a') = {val}, get('c', 'default') = '{val_def}'")

    # ee.Dictionary.getInfo
    info = ee_dictionary_get_info(d1)
    assert info == {'a': 1, 'b': 2}
    assert info is not d1
    print(f"  ✓ getInfo 返回副本")

    # ee.Dictionary.set
    d4 = ee_dictionary_set(d1, 'c', 3)
    assert d4 == {'a': 1, 'b': 2, 'c': 3}
    print(f"  ✓ set('c', 3) = {d4}")

    # ee.Dictionary.toList
    lst = ee_dictionary_to_list({'a': 1, 'b': 2})
    assert lst == [['a', 1], ['b', 2]]
    print(f"  ✓ toList() = {lst}")

    print("  ✓ 所有字典函数测试通过")


def test_list_functions():
    """测试列表相关函数"""
    print("\n【测试 ee.List 系列函数】")

    # ee.List
    l1 = ee_list([1, 2, 3])
    assert l1 == [1, 2, 3]
    l2 = ee_list()
    assert l2 == []
    print(f"  ✓ ee.List 构造正常")

    # ee.List.contains
    assert ee_list_contains([1, 2, 3], 2) == True
    assert ee_list_contains([1, 2, 3], 4) == False
    print(f"  ✓ contains 正常")

    # ee.List.filter
    filtered = ee_list_filter([1, 2, 3, 4], lambda x: x > 2)
    assert filtered == [3, 4]
    print(f"  ✓ filter(x > 2) = {filtered}")

    # ee.List.flatten
    flat = ee_list_flatten([[1, 2], [3, [4, 5]]])
    assert flat == [1, 2, 3, 4, 5]
    print(f"  ✓ flatten = {flat}")

    # ee.List.get
    assert ee_list_get([10, 20, 30], 1) == 20
    assert ee_list_get([10, 20, 30], -1) == 30
    print(f"  ✓ get 正常")

    # ee.List.group
    grouped = ee_list_group(['a', 'b', 'a', 'c', 'b', 'a'])
    assert grouped == [['a', 3], ['b', 2], ['c', 1]]
    print(f"  ✓ group = {grouped}")

    # ee.List.join
    joined = ee_list_join(['a', 'b', 'c'], '-')
    assert joined == 'a-b-c'
    print(f"  ✓ join('-') = '{joined}'")

    # ee.List.map
    mapped = ee_list_map([1, 2, 3], lambda x: x * 2)
    assert mapped == [2, 4, 6]
    mapped_drop = ee_list_map([1, 2, None, 3], lambda x: x, drop_nulls=True)
    assert mapped_drop == [1, 2, 3]
    print(f"  ✓ map 和 dropNulls 正常")

    # ee.List.remove
    removed = ee_list_remove([1, 2, 3, 2], 2)
    assert removed == [1, 3, 2]
    print(f"  ✓ remove(2) = {removed}")

    # ee.List.repeat
    repeated = ee_list_repeat(0, 5)
    assert repeated == [0, 0, 0, 0, 0]
    print(f"  ✓ repeat(0, 5) = {repeated}")

    # ee.List.sequence
    seq1 = ee_list_sequence(1, 5)
    assert seq1 == [1, 2, 3, 4, 5]
    seq2 = ee_list_sequence(0, 10, 2)
    assert seq2 == [0, 2, 4, 6, 8, 10]
    seq3 = ee_list_sequence(0, count=5)
    assert seq3 == [0, 1, 2, 3, 4]
    print(f"  ✓ sequence 正常")

    # ee.List.size
    assert ee_list_size([1, 2, 3]) == 3
    print(f"  ✓ size = 3")

    # ee.List.slice
    sliced = ee_list_slice([0, 1, 2, 3, 4, 5], 2, 5)
    assert sliced == [2, 3, 4]
    sliced2 = ee_list_slice([0, 1, 2, 3, 4, 5], 1, None, 2)
    assert sliced2 == [1, 3, 5]
    print(f"  ✓ slice 正常")

    # ee.List.sort
    sorted_list = ee_list_sort([3, 1, 2])
    assert sorted_list == [1, 2, 3]
    print(f"  ✓ sort = {sorted_list}")

    # ee.List.zip
    zipped = ee_listzip([1, 2, 3], ['a', 'b', 'c'])
    assert zipped == [(1, 'a'), (2, 'b'), (3, 'c')]
    print(f"  ✓ zip = {zipped}")

    print("  ✓ 所有列表函数测试通过")


def test_number_functions():
    """测试数值相关函数"""
    print("\n【测试 ee.Number 系列函数】")

    # ee.Number
    assert ee_number(42) == 42
    assert ee_number(3.14) == 3.14
    assert ee_number('123') == 123
    print(f"  ✓ ee.Number 构造正常")

    # ee.Number.divide
    result = ee_number_divide(10, 3)
    assert abs(result - 3.3333333) < 0.0001
    print(f"  ✓ divide(10, 3) = {result}")

    # ee.Number.format
    formatted = ee_number_format(3.14159, '%.2f')
    assert formatted == '3.14'
    print(f"  ✓ format(3.14159, '%.2f') = '{formatted}'")

    # ee.Number.gte
    assert ee_number_gte(5, 3) == True
    assert ee_number_gte(3, 5) == False
    print(f"  ✓ gte 正常")

    # ee.Number.lte
    assert ee_number_lte(3, 5) == True
    assert ee_number_lte(5, 3) == False
    print(f"  ✓ lte 正常")

    # ee.Number.multiply
    assert ee_number_multiply(6, 7) == 42
    print(f"  ✓ multiply(6, 7) = 42")

    print("  ✓ 所有数值函数测试通过")


def test_string_functions():
    """测试字符串相关函数"""
    print("\n【测试 ee.String 系列函数】")

    # ee.String
    assert ee_string('hello') == 'hello'
    assert ee_string(123) == '123'
    print(f"  ✓ ee.String 构造正常")

    # ee.String.format
    formatted = ee_string_format('Hello {name}', name='World')
    assert formatted == 'Hello World'
    print(f"  ✓ format = '{formatted}'")

    print("  ✓ 所有字符串函数测试通过")


def test_array_functions():
    """测试数组相关函数"""
    print("\n【测试 ee.Array 系列函数】")

    # ee.Array
    arr = ee_array([1, 2, 3])
    assert arr == [1, 2, 3]
    arr2 = ee_array([[1, 2], [3, 4]])
    assert arr2 == [[1, 2], [3, 4]]
    arr3 = ee_array([1, 2, 3], pixel_type='int')
    assert all(isinstance(v, int) for v in arr3)
    print(f"  ✓ ee.Array 构造正常")

    # matrixDeterminant
    det = ee_array_matrix_determinant([[1, 2], [3, 4]])
    assert abs(det - (-2.0)) < 0.0001
    print(f"  ✓ matrixDeterminant([[1,2],[3,4]]) = {det}")

    # matrixInverse
    inv = ee_array_matrix_inverse([[4, 7], [2, 6]])
    assert abs(inv[0][0] - 0.6) < 0.0001
    assert abs(inv[0][1] - (-0.7)) < 0.0001
    assert abs(inv[1][0] - (-0.2)) < 0.0001
    assert abs(inv[1][1] - 0.4) < 0.0001
    print(f"  ✓ matrixInverse 正常")

    # matrixTrace
    trace = ee_array_matrix_trace([[1, 2], [3, 4]])
    assert trace == 5.0
    print(f"  ✓ matrixTrace = {trace}")

    print("  ✓ 所有数组函数测试通过")


def test_loop_functions():
    """测试循环相关函数"""
    print("\n【测试循环函数】")

    # ee.FeatureCollection.map
    features = [{'name': 'a', 'val': 1}, {'name': 'b', 'val': 2}]
    mapped = ee_feature_collection_map(features, lambda f: f['val'] * 10)
    assert mapped == [10, 20]
    print(f"  ✓ map = {mapped}")

    # dropNulls
    mapped_null = ee_feature_collection_map([1, 2, None, 3], lambda x: x, drop_nulls=True)
    assert mapped_null == [1, 2, 3]
    print(f"  ✓ map(dropNulls=True) = {mapped_null}")

    # ee.FeatureCollection.iterate
    items = [1, 2, 3, 4]
    total = ee_feature_collection_iterate(items, lambda x, y: x + y, 0)
    assert total == 10
    print(f"  ✓ iterate(sum) = {total}")

    product = ee_feature_collection_iterate(items, lambda x, y: x * y, 1)
    assert product == 24
    print(f"  ✓ iterate(product) = {product}")

    print("  ✓ 所有循环函数测试通过")


def test_registry():
    """测试函数注册表"""
    print("\n【测试函数注册表】")

    # 检查函数数量
    all_funcs = list_all_python_functions()
    print(f"  ✓ 已注册 {len(all_funcs)} 个 GEE → Python 函数")

    # 检查特定函数可以通过名称获取
    fn = get_python_function('ee.Date.advance')
    assert fn is not None
    print(f"  ✓ get_python_function('ee.Date.advance') 成功获取函数")

    # 检查不存在的函数
    fn_missing = get_python_function('ee.NonExistent')
    assert fn_missing is None
    print(f"  ✓ get_python_function('ee.NonExistent') 返回 None")

    # 获取函数信息
    info = get_function_info('ee.Date.advance')
    assert info is not None
    assert info['python_function'] == 'ee_date_advance'
    print(f"  ✓ get_function_info 正常返回")

    # 生成对照表
    table = generate_implementation_table()
    assert 'ee.Date' in table
    assert 'ee_list_map' in table
    print(f"  ✓ generate_implementation_table 生成 {len(table.split(chr(10)))} 行")

    print("  ✓ 所有注册表测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("GEE Python 函数实现 - 全面测试")
    print("=" * 60)

    test_print()
    test_date_functions()
    test_dictionary_functions()
    test_list_functions()
    test_number_functions()
    test_string_functions()
    test_array_functions()
    test_loop_functions()
    test_registry()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！共实现 {} 个 GEE → Python 函数".format(len(GEE_PYTHON_FUNCTIONS)))
    print("=" * 60)


if __name__ == "__main__":
    main()