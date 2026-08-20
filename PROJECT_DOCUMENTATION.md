# GEE2OGE 迁移系统 - 框架文档

> 版本: v2.2  日期: 2026-08-03

---

## 一、系统定位

把 **GEE JavaScript 代码** 自动迁移为 **OGE Python 工作流代码**，核心能力来自三块：
- **知识库**：SQLite 统一存储的算子映射表
- **规则引擎**：6 步流水线
- **LLM 增强**：本地大模型 + 后处理修正

---

## 二、目录结构

```
geeToOGE/
├── web/                       # 前后端
│   ├── app.py                # Flask 后端（13 个 API）
│   ├── templates/index.html  # 前端单页应用
│   └── start.bat             # Windows 启动脚本
│
├── gee_to_ge_mapping.py      # 映射引擎（数据类 + 转换器）
├── case_study_pipeline.py    # 6 步流水线（结果导出到 docs/）
├── db_dao.py                 # 数据访问层（DB 路径默认指向 resource/gee_oge.db）
├── db_initializer.py         # 数据库初始化（从 resource/ 读取数据源）
├── llm_service.py            # LLM 服务
│
├── gee_python_functions.py   # Python 实现源文件（保留根目录：既是可导入模块也是源码资产）
├── gee_unmatched_functions.py# Python 实现源文件（保留根目录：既是可导入模块也是源码资产）
│
├── resource/                 # ⭐ 资源文件夹（数据源 + 建表脚本 + 数据库，统一管理）
│   ├── gee.json              # GEE API 元数据（数据源）
│   ├── oge.json              # OGE API 元数据（数据源）
│   ├── gee_to_oge_matches.xlsx # GEE→OGE 映射表（数据源）
│   ├── db_schema.sql         # 建表脚本
│   └── gee_oge.db            # ⭐ 统一数据库（所有实现都查这里）
│
└── docs/                     # 报告与中间产物（历史生成，非运行时依赖）
    ├── GEE_OGE完整实现状态报告.md
    ├── GEE_OGE映射审查报告.md
    ├── GEE_OGE映射修正报告_V2.md
    ├── case_study_result.json       # 流水线结果导出
    ├── oge_mappings_with_detail.json
    └── 其他 *_report.json / *_analysis.json
```

> **目录约定**：`resource/` 存放运行时依赖的资源文件（数据源、建表脚本、数据库）；`docs/` 存放历史生成的报告与中间产物（非运行时依赖）；`gee_python_functions.py` / `gee_unmatched_functions.py` 保留在根目录，因为它们既是被 `import` 的 Python 模块、又是初始化时读取源码的"源码资产"。
>
> **核心设计原则**：不管是 Python 原生实现还是 OGE API 实现，**所有 GEE API 的映射关系都统一存在 `resource/gee_oge.db` 的 `operator_mapping` 表中**。`gee_python_functions.py` / `gee_unmatched_functions.py` 只在数据库初始化时作为"源码资产"使用一次——通过 AST 解析把函数源码抽取出来写入 `operator_mapping.native_python_code` 字段。运行时只需要查数据库一个入口，无需再读这两个 .py 文件。

---

## 三、核心表结构（5 张表）

| 表名 | 作用 | 关键字段 |
|------|------|----------|
| `class_mapping` | GEE 类 ↔ OGE 类 | gee_class, oge_class, is_valid |
| `gee_api_info` | GEE API 元数据 | api_full_name, class_name, arg_types |
| `oge_api_info` | OGE API 元数据 | api_name, input_types, output_type, samplecode |
| `operator_mapping` ⭐ | **统一映射表（核心）** | gee_api_id, oge_api_id, **mapping_type**, combo_steps, native_python_code |
| `case_study_pipeline` | 流水线执行记录 | step1~step6, match_rate, feasibility |

### 3.1 operator_mapping 表的统一存储设计

这张表是整个系统的**唯一查询入口**，通过 `mapping_type` 字段区分 5 种实现方式：

| mapping_type | oge_api_id | native_python_code | combo_steps | 适用场景 |
|--------------|-----------|-------------------|-------------|----------|
| `one_to_one` | ✅ 指向 OGE API | NULL | NULL | GEE → 1 个 OGE 算子 |
| `one_to_many` | ✅ 第一个 OGE API | NULL | ✅ JSON 步骤 | GEE → N 个 OGE 算子组合 |
| `many_to_one` | ✅ 指向 OGE API | NULL | NULL | N 个 GEE → 1 个 OGE（需上下文推断） |
| `native_python` | NULL | ✅ Python 源码 | NULL | GEE → Python 原生实现 |
| `missing` | NULL | NULL | NULL | 无对应实现 |

**查询接口统一**：无论哪种实现，都通过同一个接口查询：
```python
mapping = dao.get_mapping_by_gee_name('ee.Date')       # → native_python
mapping = dao.get_mapping_by_gee_name('ee.Image.abs')  # → one_to_one
# 返回结构一致：{ gee_api, oge_api, mapping_type, native_python_code, combo_steps, ... }
```

---

## 四、映射类型（5 种）

| 类型 | 含义 | 关键字段 |
|------|------|----------|
| `one_to_one` | 1 GEE → 1 OGE | oge_api_id |
| `one_to_many` | 1 GEE → N OGE 组合 | combo_steps (JSON) |
| `many_to_one` | N GEE → 1 OGE | 需上下文推断 |
| `native_python` | GEE → Python 实现 | native_python_code |
| `missing` | 无对应实现 | review_comment |

---

## 五、6 步流水线（算法接口）

每步只列出：**命名 / 输入 / 输出 / 示例**。

### Step 1: 语义抽象

- **命名**：`step1_semantic_abstraction(gee_code)`
- **输入**：GEE JavaScript 代码字符串
- **输出**：`Step1Result { task_goal, workflow_steps[], key_params, raw_snippets[] }`
- **示例**：
  ```
  输入: "// Winter NDVI\nvar img = ee.Image('...');\nvar ndvi = img.normalizedDifference(['B5','B4']);"
  输出: 
    task_goal = "Task decomposed into 2 steps: Winter NDVI; ..."
    workflow_steps = ["Winter NDVI", "Initialize"]
    raw_snippets = [{step_description:"Winter NDVI", code_snippet:"..."}]
  ```

### Step 2: API 需求识别

- **命名**：`step2_api_requirement(step1_result)`
- **输入**：Step1Result
- **输出**：`Step2Result { required_apis[][], all_apis[], api_count }`
- **示例**：
  ```
  输入: Step1Result (含 winterImage = ee.Image(...) 代码)
  输出:
    all_apis = ["ee.Image", "ee.Image.normalizedDifference"]
    api_count = 2
  ```

### Step 3: GEE→OGE API 匹配

- **命名**：`step3_api_matching(step2_result)`
- **输入**：Step2Result
- **输出**：`Step3Result { match_details[], match_rate, matched_count, missing_count, missing_apis[] }`
- **示例**：
  ```
  输入: all_apis = ["ee.Image.abs", "ee.UnknownAPI"]
  输出:
    match_rate = 0.5
    matched_count = 1, missing_count = 1
    match_details = [
      {gee_api:"ee.Image.abs", status:"matched", oge_api:"Coverage.abs"},
      {gee_api:"ee.UnknownAPI", status:"missing"}
    ]
  ```

### Step 4: 步骤级代码生成

- **命名**：`step4_ocode_codegen(step1, step2, step3)`
- **输入**：前三步结果
- **输出**：`Step4Result { step_codes[], feasibility_flags[] }`
- **示例**：
  ```
  输出:
    step_codes = [{
      step_index: 1,
      step_description: "Winter NDVI",
      gee_code: "var ndvi = img.normalizedDifference(['B5','B4']);",
      oge_code: "# ee.Image.normalizedDifference -> [COMBO] Coverage.subtract, Coverage.add, Coverage.divide\n# ..."
    }]
  ```

### Step 5: 可行性补全

- **命名**：`step5_feasibility_completion(step3, step4)`
- **输入**：Step3Result, Step4Result
- **输出**：`Step5Result { overall_feasible, blocking_apis[], non_blocking_gaps[], rescue_suggestions[] }`
- **示例**：
  ```
  输出:
    overall_feasible = true
    blocking_apis = []
    non_blocking_gaps = ["Map.addLayer"]
    rescue_suggestions = [{api:"Map.addLayer", suggestion:"UI 类算子缺失，用 print 替代"}]
  ```

### Step 6: 工作流重构

- **命名**：`step6_workflow_reconstruction(step4, step5, step1)`
- **输入**：Step4/5/1 结果
- **输出**：`Step6Result { oge_code, missing_report, feasibility }`
- **示例**：
  ```python
  # 输出 oge_code:
  import oge
  oge.initialize()
  service = oge.Service.initialize()
  # ----- Step 1: Winter NDVI -----
  coverage = service.getCoverage(coverageID="...", productID="...")
  result = service.getProcess("Coverage.subtract").execute(...)
  ```

### 统一入口

- **命名**：`run(gee_code)` 或 `run_pipeline(gee_code)`
- **输入**：GEE 代码字符串
- **输出**：`PipelineResult { step1~step6, match_rate, success, error }`

---

## 六、LLM 服务（算法接口）

### 6.1 LLM 可用性检测

- **命名**：`is_available()`
- **输入**：无
- **输出**：`bool`
- **示例**：`True`（当 `http://111.37.195.37:8015/v1/models` 返回 200）

### 6.2 LLM 语义分析

- **命名**：`analyze_gee_code(gee_code)`
- **输入**：GEE 代码字符串
- **输出**：`Dict { task_goal, api_calls[], variable_types{}, dataflow, suggestions[] }`
- **示例**：
  ```json
  {
    "task_goal": "计算 NDVI 并裁剪到矩形区域",
    "api_calls": ["ee.Image", "ee.Image.normalizedDifference", "ee.Geometry.Rectangle"],
    "variable_types": {"image": "ee.Image", "ndvi": "ee.Image"}
  }
  ```

### 6.3 LLM 代码生成

- **命名**：`generate_oge_code(gee_code, mapping_context)`
- **输入**：GEE 代码 + 映射上下文文本
- **输出**：`Dict { oge_code, explanations[], warnings[], feasibility }`
- **示例**：
  ```python
  # 输出 oge_code:
  import oge
  oge.initialize()
  service = oge.Service.initialize()
  geom = service.getProcess("Geometry.Point").execute([-119.56, 37.67], "EPSG:4326")
  feature = service.getProcess("Feature.loadFromGeometry").execute(geom, {'prop': 10})
  ```

### 6.4 后处理自动修正

- **命名**：`_post_process_oge_code(code)`
- **输入**：LLM 生成的 OGE 代码字符串
- **输出**：修正后的代码字符串
- **示例**：
  ```
  输入: service = oge.Service()
  输出: service = oge.Service.initialize()
  
  输入: geom = oge.Geometry.Point([-119.56, 37.67])
  输出: geom = service.getProcess("Geometry.Point").execute([-119.56, 37.67], "EPSG:4326")
  ```

---

## 七、映射上下文构建（算法接口）

### 7.1 映射上下文构建

- **命名**：`_build_mapping_context(dao, gee_code)`（位于 `web/app.py`）
- **输入**：DAO 实例 + GEE 代码
- **输出**：结构化映射表文本（供 LLM Prompt 使用）
- **示例**：
  ```
  ## ee.Geometry.Point
  - GEE 描述: Constructs a Geometry with a single point.
  - 映射类型: 一对一 (one_to_one)
  - OGE API: Geometry.Point
  - OGE 输入类型: List, String
  - OGE 示例代码: service.getProcess("Geometry.Point").execute([lng, lat], "EPSG:4326")
  
  ## 补充说明：FeatureCollection 构建
  - 当从 Feature 列表构建时，使用 FeatureCollection.loadFromFeatureList
  ```

### 7.2 变量类型推断

- **命名**：`_infer_variable_types(code)`（位于 `case_study_pipeline.py`）
- **输入**：代码字符串
- **输出**：`Dict[str, str]`（变量名 → GEE 类名）
- **示例**：
  ```
  输入: "var img = ee.Image('...');\nvar ndvi = img.normalizedDifference(['B5','B4']);"
  输出: {"img": "ee.Image", "ndvi": "ee.Image"}
  ```

---

## 八、数据导入（算法接口）

### 8.1 伪 OGE 映射识别

- **命名**：`_is_pseudo_oge_name(oge_api_name)`
- **输入**：OGE API 名称字符串
- **输出**：`bool`
- **示例**：
  ```
  输入: "Python List"        → 输出: True
  输入: "Coverage.abs"       → 输出: False
  输入: "print"              → 输出: True
  ```

### 8.2 映射类型判定

- **命名**：`_determine_mapping_type(oge_apis, native_python=False)`
- **输入**：OGE API 名称列表 + 是否 Python 实现标志
- **输出**：映射类型字符串
- **示例**：
  ```
  输入: (["Coverage.abs"], False)         → 输出: "one_to_one"
  输入: (["A.b", "A.c"], False)            → 输出: "one_to_many"
  输入: ([], False)                        → 输出: "missing"
  输入: ([], True)                         → 输出: "native_python"
  ```

### 8.3 Python 函数源码提取

- **命名**：`_extract_function_source(file_path, func_name)`
- **输入**：Python 文件路径 + 函数名
- **输出**：函数完整源代码字符串
- **示例**：
  ```
  输入: ("gee_python_functions.py", "gee_print")
  输出: "def gee_print(*args, **kwargs):\n    print(*args, **kwargs)"
  ```

---

## 九、Web API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| GET | `/api/llm-status` | LLM 可用性 |
| POST | `/api/convert` | 规则引擎转换 |
| POST | `/api/convert-llm` | LLM 增强转换 |
| GET | `/api/mappings` | 映射列表（分页） |
| GET | `/api/mapping/<name>` | 单个映射详情 |
| GET | `/api/history` | 历史记录列表 |
| GET | `/api/history/<id>` | 单条历史详情 |
| GET | `/api/stats` | 统计信息 |
| GET | `/api/classes` | 类映射 |
| GET | `/api/gee-apis` | GEE API 列表 |
| GET | `/api/oge-apis` | OGE API 列表 |
| GET | `/api/native-python` | Python 实现列表 |

---

## 十、数据流总览

```
用户输入 GEE 代码
        │
        ▼
┌───────────────────┐
│  /api/convert-llm │
└─────────┬─────────┘
          │
   ┌──────┴───────┐
   ▼              ▼
规则引擎         LLM 服务
(6 步流水线)    (语义分析+代码生成)
   │              │
   │              ▼
   │         后处理修正
   │              │
   └──────┬───────┘
          ▼
   合并结果（LLM 代码优先）
          │
          ▼
   保存到 case_study_pipeline 表
          │
          ▼
   返回前端展示
```

---

## 十一、启动方式

```bash
# 1. 初始化数据库（首次）
python db_initializer.py

# 2. 启动 Web 服务
cd web
python app.py
# 访问 http://127.0.0.1:5001
```
