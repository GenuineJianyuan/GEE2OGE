# 算法目录

本包仅包含可复用的纯算法。Web 端点、凭据、SQLite 文件、实验缓存和模型客户端均被有意排除。

| 类别 | 模块 | 核心算法 |
|---|---|---|
| 源码静态分析 | `core.analysis` | 步骤拆分、覆盖率校验、变量类型推断、链式调用 API 提取、关键参数提取 |
| 工作流重构 | `core.workflow` | 语句提取、变量引用分析、依赖图构建、拓扑排序、循环检测（Tarjan SCC）、层级计算 |
| 映射库与匹配 | `core.mapping` | 正/反向算子查找、组合匹配（贪婪策略）、批量匹配、匹配率计算、可行性分类 |
| 规则引擎转换 | `core.converter` | GEE→OGE 骨架生成、OGE→GEE 反向草稿、组合映射处理、映射上下文格式化 |
| 可行性与验证 | `core.validation` | 源码括号/引号平衡检查、映射覆盖率检查、工作流占位符检测、映射库一致性校验 |
| 代码预处理 | `core.preprocessing` | 归一化、JS/Python 注释清理、行数统计、导入提取、缩进去除 |
| 图相似度评估 | `core.evaluation` | AST 转图、正则回退、NMR/EMR/TS 核心指标、论文指标、多图合并、指标聚合 |
| 空间/遥感兜底 | `core.native_algorithms` | 归一化指数、栅格运算、邻域统计、连通域、边缘检测、地形产品、分类精度、辐射定标 |

## 映射库统计

当前核心映射库共 **125** 条记录，按类型分布：

| 映射类型 | 数量 | 说明 |
|---|---|---|
| `one_to_one` | 66 | 一个 GEE API 对应一个 OGE API |
| `many_to_one` | 32 | 多个 GEE API 组合对应一个 OGE API |
| `native_python` | 11 | GEE API 对应 Python 原生实现 |
| `gee_python` | 10 | GEE 客户端 API 对应 Python 标准库 |
| `one_to_many` | 3 | 一个 GEE API 对应多个 OGE API |
| `many_to_many` | 3 | 多个 GEE API 组合对应多个 OGE API |

## 四组实验策略

生产环境中的实验名称对应以下可复现的策略：

1. **GEE2OGE 方法**：语义步骤分解 + 权威映射查找（含组合匹配）+ 逐步骤代码生成 + 工作流重构。
2. **baseline1**：直接从完整源码 + 全部检测到的 API 映射生成。
3. **baseline2**：从步骤计划 + 逐步骤映射直接生成。
4. **baseline3**：从原始 GEE 源码 + 权威 OGE 规则直接生成，不经过步骤计划。

独立算法包实现了这些策略中的确定性分析、映射、验证和评估部分。
应用层可以在不修改算法接口的情况下，接入外部 LLM 服务。

## 核心评估指标

| 指标 | 全称 | 含义 |
|---|---|---|
| NMR | Node Match Rate | 节点匹配率，节点标签多重集合的 F1 值 |
| EMR | Edge Match Rate | 边匹配率，边标签多重集合的 F1 值 |
| TS | Topological Similarity | 拓扑相似度，NMR 与 EMR 的加权综合 × 规模惩罚因子 |
| LAM | Logical Accuracy Metric | 逻辑准确率，边召回率 |
| PA | Perfect Accuracy | 完全匹配率，节点与边完全一致为 1，否则为 0 |
| LD | Length Difference | 节点数差异绝对值 |

## 组合匹配算法说明

组合匹配用于处理「多个 GEE API 组合对应一个 OGE 算子」的情况（如 NDVI 的 select+subtract+divide → Coverage.NDVI）。

**匹配策略：**
1. 按组合大小降序排列：更大、更具体的组合优先匹配（如 TRI 指数有 7 个 API 的组合，优先级高于 3 个 API 的组合）
2. 相同大小按稀缺度升序：越稀缺的组合越先匹配，保证组合多样性
3. 每个组合一次性贪婪匹配尽可能多次
4. 同一个 API 可以参与多个组合（只要出现次数足够）
5. 剩余未被消耗的 API 再逐个匹配一对一/一对多/原生 Python 映射
