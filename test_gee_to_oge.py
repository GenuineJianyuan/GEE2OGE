"""
GEE 到 OGE 映射转换模块测试脚本（含 gee.json 集成）。

本脚本用于测试 gee_to_ge_mapping.py 中的所有功能，
包括 Excel 解析、gee.json 集成、转换查询、搜索等功能。
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gee_to_ge_mapping import (
    GeeToOgeConverter,
    GeeApiInfo,
    GeeApiDetail,
    GeeArgumentInfo,
    OgeApiInfo,
    OgeMappingResult,
    ExcelParser,
    GeeJsonParser,
    create_converter,
    quick_convert,
    search_apis
)

# 文件路径（资源文件已统一移入 resource/ 目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "resource")
XLSX_PATH = os.path.join(RESOURCE_DIR, "gee_to_oge_matches.xlsx")
GEE_JSON_PATH = os.path.join(RESOURCE_DIR, "gee.json")


def test_excel_parser():
    """测试 Excel 解析器"""
    print("=" * 60)
    print("【测试 1】Excel 解析器")
    print("=" * 60)

    data = ExcelParser.parse_xlsx(XLSX_PATH)
    print(f"✓ 成功解析 Excel 文件")
    print(f"  - 总行数: {len(data)}")
    print(f"  - 第一行数据示例:")
    if data:
        print(f"    {data[0]}")
    print()


def test_gee_json_parser():
    """测试 gee.json 解析器"""
    print("=" * 60)
    print("【测试 2】gee.json 解析器")
    print("=" * 60)

    details = GeeJsonParser.parse_gee_json(GEE_JSON_PATH)
    print(f"✓ 成功解析 gee.json 文件")
    print(f"  - API 总数: {len(details)}")

    # 显示一些详细信息
    sample_keys = list(details.keys())[:3]
    for key in sample_keys:
        detail = details[key]
        print(f"\n  --- {detail.full_name} ---")
        print(f"    类名: {detail.class_name}")
        print(f"    方法名: {detail.method_name}")
        print(f"    返回值: {detail.returns}")
        print(f"    用法: {detail.usage}")
        print(f"    参数数量: {len(detail.arguments)}")
        for arg in detail.arguments:
            print(f"      - {arg.name}: {arg.type}")
    print()


def test_converter_without_json():
    """测试转换器（不加载 gee.json）"""
    print("=" * 60)
    print("【测试 3】转换器 - 仅 Excel 映射")
    print("=" * 60)

    converter = GeeToOgeConverter(XLSX_PATH)
    stats = converter.get_statistics()
    print(f"✓ 转换器初始化成功")
    print(f"  - 总映射数: {stats['total']}")
    print(f"  - 已匹配: {stats['matched']}")
    print(f"  - 未匹配: {stats['unmatched']}")
    print(f"  - 有详情: {stats['with_detail']}")
    print()


def test_converter_with_json():
    """测试转换器（同时加载 Excel 和 gee.json）"""
    print("=" * 60)
    print("【测试 4】转换器 - Excel + gee.json 集成")
    print("=" * 60)

    converter = GeeToOgeConverter(XLSX_PATH, GEE_JSON_PATH)
    stats = converter.get_statistics()
    print(f"✓ 转换器初始化成功（含 gee.json）")
    print(f"  - 总映射数: {stats['total']}")
    print(f"  - 已匹配: {stats['matched']}")
    print(f"  - 未匹配: {stats['unmatched']}")
    print(f"  - 有详情: {stats['with_detail']}")
    print()


def test_single_conversion_with_detail():
    """测试单个 API 转换（带详细信息）"""
    print("=" * 60)
    print("【测试 5】单个 API 转换（带详情）")
    print("=" * 60)

    converter = GeeToOgeConverter(XLSX_PATH, GEE_JSON_PATH)

    # 测试有详细信息的 API
    test_cases = [
        "ee.Image.abs",
        "ee.Image.reduceRegion",
        "ee.Algorithms.CannyEdgeDetector",
        "ee.Feature.buffer",
        "Map.centerObject",
    ]

    for api_name in test_cases:
        result = converter.convert(api_name)
        if result:
            oge_names = result.get_oge_full_names()
            print(f"✓ {api_name} -> {', '.join(oge_names) or 'N/A'}")
            if result.has_detail():
                detail = result.gee_detail
                print(f"    详情: usage='{detail.usage}', returns='{detail.returns}'")
                print(f"    参数: {detail.get_argument_names()}")
            else:
                print(f"    详情: 无")
        else:
            print(f"✗ {api_name} -> 未找到")
    print()


def test_search_by_argument():
    """测试按参数名搜索"""
    print("=" * 60)
    print("【测试 6】按参数名搜索")
    print("=" * 60)

    converter = GeeToOgeConverter(XLSX_PATH, GEE_JSON_PATH)

    test_args = ["image", "threshold", "geometry", "region", "scale"]

    for arg in test_args:
        results = converter.search_by_argument(arg)
        print(f"✓ 参数 '{arg}': {len(results)} 个 API 使用")
        if results:
            for r in results[:3]:
                print(f"    - {r.gee_api.canonical_name}")
            if len(results) > 3:
                print(f"    ... 还有 {len(results) - 3} 个")
    print()


def test_keyword_search_with_detail():
    """测试关键字搜索（含详细信息）"""
    print("=" * 60)
    print("【测试 7】关键字搜索（含详情）")
    print("=" * 60)

    converter = GeeToOgeConverter(XLSX_PATH, GEE_JSON_PATH)

    keywords = ["buffer", "CannyEdgeDetector", "reduceRegion"]

    for kw in keywords:
        results = converter.search_by_keyword(kw)
        print(f"✓ 关键字 '{kw}': 找到 {len(results)} 条匹配")
        for r in results[:2]:
            oge_names = r.get_oge_full_names()
            has_detail = " [有详情]" if r.has_detail() else ""
            print(f"    {r.gee_api.canonical_name}{has_detail} -> {', '.join(oge_names)}")
    print()


def test_data_classes():
    """测试数据类"""
    print("=" * 60)
    print("【测试 8】数据类功能")
    print("=" * 60)

    # 测试 GeeArgumentInfo
    arg = GeeArgumentInfo(name="image", type="Image", details="Input image", order=1)
    print(f"✓ GeeArgumentInfo: {arg.to_dict()}")

    # 测试 GeeApiDetail
    detail = GeeApiDetail(
        full_name="ee.Test.method",
        class_name="ee.Test",
        method_name="method",
        description="Test description",
        usage="ee.Test.method(param1)",
        returns="Image",
        arguments=[arg],
        url="https://example.com",
        organization_path="ee / ee.Test"
    )
    print(f"\n✓ GeeApiDetail:")
    print(f"    argument_names: {detail.get_argument_names()}")
    print(f"    required_arguments: {len(detail.get_required_arguments())}")
    print(f"    to_dict keys: {list(detail.to_dict().keys())}")

    # 测试 GeeApiInfo
    gee_info = GeeApiInfo(
        canonical_name="ee.Image.abs",
        api_names=["ee.Image.abs", "ee.Image.trig"],
        description_en="Computes absolute value.",
        description_zh="计算绝对值。"
    )
    print(f"\n✓ GeeApiInfo: has_alias={gee_info.has_alias()}, all_names={gee_info.get_all_names()}")

    # 测试 OgeApiInfo
    oge_info = OgeApiInfo.from_full_name("Coverage.abs")
    print(f"\n✓ OgeApiInfo: module={oge_info.module}, method={oge_info.method}")

    # 测试 OgeMappingResult
    result = OgeMappingResult(
        gee_api=gee_info,
        oge_apis=[oge_info],
        matched=True,
        gee_detail=detail
    )
    print(f"\n✓ OgeMappingResult:")
    print(f"    has_detail: {result.has_detail()}")
    print(f"    to_dict keys: {list(result.to_dict().keys())}")
    print()


def test_enrich():
    """测试后补充详细信息"""
    print("=" * 60)
    print("【测试 9】后补充详细信息")
    print("=" * 60)

    # 先只加载 Excel
    converter = GeeToOgeConverter(XLSX_PATH)
    stats_before = converter.get_statistics()
    print(f"加载 Excel 后: with_detail={stats_before['with_detail']}")

    # 再补充 gee.json
    enriched = converter.enrich_with_gee_json(GEE_JSON_PATH)
    stats_after = converter.get_statistics()
    print(f"补充 gee.json 后: with_detail={stats_after['with_detail']}")
    print(f"补充数量: {enriched}")
    print()


def test_arguments_mapping():
    """测试参数映射获取"""
    print("=" * 60)
    print("【测试 10】参数映射")
    print("=" * 60)

    converter = GeeToOgeConverter(XLSX_PATH, GEE_JSON_PATH)
    arg_mapping = converter.get_arguments_mapping()
    print(f"✓ 有参数映射的 API 数量: {len(arg_mapping)}")

    # 显示几个示例
    for i, (name, args) in enumerate(list(arg_mapping.items())[:3]):
        print(f"\n  {name}:")
        for arg in args:
            print(f"    - {arg['name']}: {arg['type']}")
    print()


def test_export():
    """测试导出功能"""
    print("=" * 60)
    print("【测试 11】导出 JSON（含详情）")
    print("=" * 60)

    converter = GeeToOgeConverter(XLSX_PATH, GEE_JSON_PATH)
    # 报告类产物统一输出到 docs/ 目录
    docs_dir = os.path.join(BASE_DIR, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, "oge_mappings_with_detail.json")
    converter.export_to_json(output_path, matched_only=True, include_detail=True)

    print(f"✓ 已导出到: {output_path}")

    # 读取验证
    import json
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  - 导出条数: {len(data)}")

    # 检查是否包含 detail
    has_detail_count = sum(1 for d in data if 'gee_detail' in d)
    print(f"  - 含详情条数: {has_detail_count}")

    # 显示一个示例的 detail 结构
    if data and 'gee_detail' in data[0]:
        print(f"  - 第一条详情字段: {list(data[0]['gee_detail'].keys())}")
    print()


def test_convenience_functions():
    """测试便捷函数"""
    print("=" * 60)
    print("【测试 12】便捷函数")
    print("=" * 60)

    # 测试 create_converter
    converter = create_converter(XLSX_PATH, GEE_JSON_PATH)
    stats = converter.get_statistics()
    print(f"✓ create_converter: {stats['total']} 条映射, {stats['with_detail']} 条有详情")

    # 测试 quick_convert (不含 detail)
    result = quick_convert(XLSX_PATH, "ee.Image.abs")
    if result:
        print(f"✓ quick_convert('ee.Image.abs'): {result.get_oge_full_names()}")

    # 测试 search_apis
    results = search_apis(XLSX_PATH, "buffer")
    print(f"✓ search_apis('buffer'): 找到 {len(results)} 条结果")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("GEE 到 OGE 映射转换模块 - 综合测试（含 gee.json 集成）")
    print("=" * 60 + "\n")

    # 确保文件存在
    if not os.path.exists(XLSX_PATH):
        print(f"错误: Excel 文件不存在: {XLSX_PATH}")
        sys.exit(1)
    if not os.path.exists(GEE_JSON_PATH):
        print(f"错误: gee.json 文件不存在: {GEE_JSON_PATH}")
        sys.exit(1)

    test_excel_parser()
    test_gee_json_parser()
    test_converter_without_json()
    test_converter_with_json()
    test_single_conversion_with_detail()
    test_search_by_argument()
    test_keyword_search_with_detail()
    test_data_classes()
    test_enrich()
    test_arguments_mapping()
    test_export()
    test_convenience_functions()

    print("=" * 60)
    print("所有测试完成！✓")
    print("=" * 60)


if __name__ == "__main__":
    main()