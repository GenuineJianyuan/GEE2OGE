#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 OGE 代码生成的后处理逻辑

验证 _post_process_oge_code 方法是否能正确修正 LLM 生成的错误代码。
"""

import sys
sys.path.insert(0, '.')

from llm_service import LLMService

def test_remove_duplicate_initialization():
    """测试移除重复的初始化代码"""
    service = LLMService()
    
    # 模拟 LLM 生成的有重复初始化的代码
    code = '''# ============================================================
# GEE → OGE 自动迁移生成的工作流
# ============================================================

import oge
oge.initialize()
service = oge.Service()

# ----- Step 1: Winter -----
import oge
oge.initialize()
service = oge.Service()

result = service.getProcess("Coverage.selectBands").execute(cov, ["B4"])

# ----- Step 2: Summer -----
import oge
oge.initialize()
service = oge.Service()

result = service.getProcess("Coverage.selectBands").execute(cov, ["B3"])
'''
    
    result = service._post_process_oge_code(code)
    print("=== 测试1: 移除重复初始化 ===")
    print(result)
    print()
    
    # 验证只有一组初始化
    init_count = result.count('import oge')
    assert init_count == 1, f"应该只有1个import oge，实际有{init_count}个"
    print("✅ 测试1通过")
    print()


def test_fix_wrong_process_calls():
    """测试修正错误的 process 调用"""
    service = LLMService()
    
    # 模拟 LLM 生成的错误代码
    code = '''import oge
oge.initialize()
service = oge.Service()

# 错误: service.getProcess("service.getCoverage").execute(...)
result = service.getProcess("service.getCoverage").execute("LC08_L1TP_119038_20230104_20230111_02_T1", "LC08_C02_L1")

# 正确: service.getProcess("Coverage.selectBands").execute(...)
result = service.getProcess("Coverage.selectBands").execute(cov, ["B4"])
'''
    
    result = service._post_process_oge_code(code)
    print("=== 测试2: 修正错误的 process 调用 ===")
    print(result)
    print()
    
    # 验证 getCoverage 被正确转换
    assert 'service.getCoverage(coverageID=' in result, "getCoverage应该被正确转换"
    assert 'service.getProcess("Coverage.selectBands")' in result, "正确的调用应该保留"
    print("✅ 测试2通过")
    print()


def test_fix_mapclient_calls():
    """测试修正 mapclient 调用"""
    service = LLMService()
    
    # 模拟 LLM 生成的错误代码
    code = '''import oge
oge.initialize()
service = oge.Service()

# 错误: service.getProcess("oge.mapclient.centerMap").execute(...)
result = service.getProcess("oge.mapclient.centerMap").execute(120.5, 32.0, 9)

# 错误: service.getProcess("getMap").execute(...)
result = service.getProcess("getMap").execute(...)

# 正确: .styles().getMap()
winterNdvi.styles(vis_params).getMap("Winter NDVI")
'''
    
    result = service._post_process_oge_code(code)
    print("=== 测试3: 修正 mapclient 调用 ===")
    print(result)
    print()
    
    # 验证 centerMap 被正确转换
    assert 'oge.mapclient.centerMap(120.5, 32.0, 9)' in result, "centerMap应该被正确转换"
    # 验证 getMap 错误调用被移除（检查代码行中是否还有这个调用，排除注释）
    result_lines = [l for l in result.split('\n') if not l.strip().startswith('#')]
    assert not any('service.getProcess("getMap")' in l for l in result_lines), "错误的getMap调用应该被移除"
    # 验证正确的 getMap 调用保留
    assert '.getMap("Winter NDVI")' in result, "正确的getMap调用应该保留"
    print("✅ 测试3通过")
    print()


def test_clean_code_structure():
    """测试清理代码结构"""
    service = LLMService()
    
    # 模拟 LLM 生成的有多余空行和注释的代码
    code = '''import oge
oge.initialize()
service = oge.Service()


# ----- Step 1: Winter -----


# 读取数据
winterImage = service.getCoverage(
    coverageID="LC08_L1TP_119038_20230104_20230111_02_T1",
    productID="LC08_C02_L1"
)


# ----- Step 2: Summer -----


# 读取数据
summerImage = service.getCoverage(
    coverageID="TODO_SUMMER_COVERAGE_ID",
    productID="LC08_C02_L1"
)
'''
    
    result = service._post_process_oge_code(code)
    print("=== 测试4: 清理代码结构 ===")
    print(result)
    print()
    
    # 验证步骤标记被移除
    assert '# ----- Step' not in result, "步骤标记应该被移除"
    # 验证没有连续多个空行
    assert '\n\n\n' not in result, "不应该有连续3个以上的空行"
    print("✅ 测试4通过")
    print()


def test_full_pipeline():
    """测试完整的后处理流程"""
    service = LLMService()
    
    # 模拟 LLM 生成的典型错误代码
    code = '''# ============================================================
# GEE → OGE 自动迁移生成的工作流
# ============================================================

import oge

# 初始化
oge.initialize()
service = oge.Service()

# ----- Step 1: Winter -----
import oge
oge.initialize()
service = oge.Service()

result = service.getProcess("service.getCoverage").execute("LC08_L1TP_119038_20230104_20230111_02_T1", "LC08_C02_L1")

# ----- Step 2: Summer -----
import oge
oge.initialize()
service = oge.Service()

result = service.getProcess("service.getCoverage").execute("TODO_SUMMER", "LC08_C02_L1")

# ----- Step 3: Winter bands -----
import oge
oge.initialize()
service = oge.Service()

result = service.getProcess("Coverage.selectBands").execute(winterImage, ["B4"])

# ----- Step 4: Style -----


# ----- Step 5: Layers -----
import oge
oge.initialize()
service = oge.Service()

result = service.getProcess("getMap").execute(...)
# 可视化输出
oge.mapclient.centerMap(120.5, 32.0, 9)

# ----- Step 6: Center -----
import oge
oge.initialize()
service = oge.Service()

result = service.getProcess("oge.mapclient.centerMap").execute(120.5, 32.0, 9)
# 可视化输出
oge.mapclient.centerMap(120.5, 32.0, 9)
'''
    
    result = service._post_process_oge_code(code)
    print("=== 测试5: 完整后处理流程 ===")
    print(result)
    print()
    
    # 验证只有一组初始化
    init_count = result.count('import oge')
    assert init_count == 1, f"应该只有1个import oge，实际有{init_count}个"
    
    # 验证 getCoverage 被正确转换
    assert 'service.getCoverage(coverageID=' in result, "getCoverage应该被正确转换"
    
    # 验证 centerMap 被正确转换
    assert 'oge.mapclient.centerMap(120.5, 32.0, 9)' in result, "centerMap应该被正确转换"
    
    # 验证 getMap 错误调用被移除（检查代码行中是否还有这个调用，排除注释）
    result_lines = [l for l in result.split('\n') if not l.strip().startswith('#')]
    assert not any('service.getProcess("getMap")' in l for l in result_lines), "错误的getMap调用应该被移除"
    
    # 验证步骤标记被移除
    assert '# ----- Step' not in result, "步骤标记应该被移除"
    
    print("✅ 测试5通过")
    print()
    print("=" * 50)
    print("🎉 所有测试通过！")
    print("=" * 50)


if __name__ == '__main__':
    test_remove_duplicate_initialization()
    test_fix_wrong_process_calls()
    test_fix_mapclient_calls()
    test_clean_code_structure()
    test_full_pipeline()
