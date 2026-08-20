# 02. API 识别与匹配算法

## 1. 全局变量类型推断

目的：把实例方法还原为完整的 GEE API 名，以便准确查表。例如 `ndvi.rename('NDVI')` 需要先知道 `ndvi` 是 `ee.Image`，才能识别为 `ee.Image.rename`。

### 推断规则

| 代码模式 | 推断结果 | 示例 |
| --- | --- | --- |
| `var x = ee.Class(...)` | `x: ee.Class` | `var img = ee.Image(id)` → `img: ee.Image` |
| `var x = ee.Geometry.Point(...)` | 取基础类型 | `x: ee.Geometry` |
| `var y = x;` | 继承已知类型 | `var copy = img;` → `copy: ee.Image` |
| `var y = x.method(...)` | 根据返回类型表推断 | `var ndvi = img.normalizedDifference(...)` → `ndvi: ee.Image` |

实现以正则表达式解析 GEE JavaScript，并维护“方法名 → 返回 GEE 类型”的表。当前覆盖影像运算、几何运算和部分要素操作；无法确定的动态返回类型不会强行推断。

## 2. API 调用提取

对每个步骤代码使用以下模式：

```text
ee.<Class>(...)                  # 构造函数
ee.<Class>.<method>(...)         # 静态/多级 API
Map.<method>(...)                # 地图操作
Export.<type>.<method>(...)      # 导出操作
<known_variable>.<method>(...)  # 类型驱动的实例调用
```

集合以 `set` 去重并排序，得到稳定的 `all_apis`。实例调用只在方法属于对应类型的白名单时才被记为 GEE API，避免把普通 JavaScript 方法误识别为 GEE API。

## 3. 映射知识库检索

映射表 `operator_mapping` 是运行时唯一入口。按 `gee_api_info.api_full_name` 精确查询，返回 GEE 元数据、OGE 元数据及映射实现。

| `mapping_type` | 含义 | 后续处理 |
| --- | --- | --- |
| `one_to_one` | 一个 GEE API 对应一个 OGE 算子 | 直接生成 OGE 调用 |
| `one_to_many` | 一个 GEE API 需多个 OGE 算子组合 | 读取 `combo_steps` 展开 |
| `many_to_one` | 多个 GEE 语义归并到一个 OGE 算子 | 结合上下文生成 |
| `native_python` | 无 OGE 算子但有 Python 实现 | 读取 `native_python_code` |
| `missing` | 尚无实现 | 进入可行性分析 |

## 4. LLM 语义匹配增强

当知识库未命中时，向 LLM 提供 GEE API 名及 OGE 元数据语境，要求返回目标 OGE 算子、置信度和推理。仅当 `matched=True` 且 `confidence ≥ 0.6` 时才临时将其记作已匹配。

该机制用于降低映射缺口，但不会自动写入数据库；数据库仍是人工审查后的稳定映射来源。

## 5. LLM 代码后处理规则

最终生成的 OGE 代码会经过规则校正，主要包括：

1. 去除重复初始化；
2. 统一 `oge.Service()` 初始化写法；
3. 修正把 `getCoverage` 等数据读取 API 错当作 `getProcess` 的调用；
4. 修正 `mapclient` 的调用方式；
5. 修正已知错误算子名、关键字参数和代码结构。

这种“知识库约束 + LLM 生成 + 规则后处理”的组合，兼顾了可解释性和复杂脚本转换的表达能力。

## 代码位置

- 类型推断与调用提取：`../../case_study_pipeline.py`
- 映射查询和匹配率：`../../db_dao.py`
- LLM 语义匹配和后处理：`../../llm_service.py`
