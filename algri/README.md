# GEE → OGE 主要算法整理

本目录汇总本项目实际使用的主要算法，面向方案说明、代码审查和后续维护。算法按职责分为三类：迁移流程、API 识别与匹配、遥感原生实现。

| 文档 | 主要内容 | 对应实现 |
| --- | --- | --- |
| [01_迁移流程算法.md](01_迁移流程算法.md) | 六步迁移流程、可行性决策与工作流重构 | `case_study_pipeline.py` |
| [02_API识别与匹配算法.md](02_API识别与匹配算法.md) | 变量类型推断、正则识别、知识库匹配、LLM 补充 | `case_study_pipeline.py`、`db_dao.py`、`llm_service.py` |
| [03_遥感与空间分析算法.md](03_遥感与空间分析算法.md) | 邻域统计、连通域、Canny、地形因子、归约统计 | `gee_unmatched_functions.py` |

## 可直接复用的实现

除说明文档外，目录还包含去工程化后的原始算法实现：

| 文件 | 保留内容 | 已去除内容 |
| --- | --- | --- |
| `migration_algorithms.py` | 步骤拆分、参数提取、变量类型推断、API 识别、映射结果统计、可行性分类 | Flask、SQLite、LLM、缓存、记录保存 |
| `remote_sensing_algorithms.py` | 栅格数学、邻域统计、连通域、Canny、DEM 地形因子、精度计算 | API 注册表、数据库源码抽取、工程包装 |
| `example.py` | 无 Web/数据库/LLM 的最小调用示例 | — |

可在此目录下直接执行 `python example.py` 验证迁移核心算法；遥感算法中的部分函数需要按需安装 `scipy` 和 `scikit-image`。

## 算法关系

```text
GEE JavaScript
  → 语义分步与参数提取
  → 变量类型推断、API 调用识别
  → SQLite 映射检索（必要时由 LLM 语义匹配补充）
  → OGE / Python 代码模板生成
  → 缺失 API 可行性分类与工作流重构
  → OGE Python 工作流
```

说明：本目录是对现有工程实现的整理，不改变原有运行逻辑。遥感算法中标注“简化实现”的条目适合作为迁移兜底或原型验证；用于正式生产分析时，应结合像元分辨率、坐标系、NoData 和专业库参数进一步校准。
