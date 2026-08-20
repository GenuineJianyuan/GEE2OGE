# GEE → OGE 转换平台 API 接口文档

> 版本 v1.0 | 基础路径: http://127.0.0.1:5001 | 共 30 个接口

---

## 🔗 API 调用顺序与关系

### 流程图总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层                                          │
│                        GET /              GET /test                              │
└──────────────────────────┬──────────────────────────┬────────────────────────────┘
                           │                          │
                           ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ① 代码转换主流程                                         │
│                                                                                 │
│  ┌──────────────┐    ┌───────────────────┐    ┌──────────────────────┐          │
│  │llm-status    │───▶│ convert-llm       │───▶│ result-cache (保存)   │          │
│  │(检查LLM)     │    │ 或 convert        │    │ history (自动入库)    │          │
│  └──────────────┘    └───────────────────┘    └──────────────────────┘          │
│                             │                                                  │
│                             ▼                                                  │
│                    ┌──────────────────────┐                                    │
│                    │ 知识库查询 (可选)     │                                    │
│                    │ mappings / mapping... │                                    │
│                    └──────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ② 案例使用流程                                          │
│                                                                                 │
│  GET /api/examples ──▶ GET /api/examples/{id} ──▶ POST /api/convert-llm         │
│     (案例列表)            (加载案例详情)            (用案例代码做转换)              │
│                                                                                 │
│  POST /api/examples ──▶ GET /api/examples (刷新列表)                            │
│     (添加新案例)                                                            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ③ 知识库查询流程                                         │
│                                                                                 │
│  mappings ──▶ mapping/{name} ──▶ oge-api-detail ──▶ native-python               │
│  (映射列表)    (单个映射详情)      (OGE API详情)     (Python实现)                │
│                                                                                 │
│  gee-apis ──▶ gee-samplecodes ──▶ gee-samplecode/{name}                         │
│  (GEE API列表)  (有示例的API)       (示例代码详情)                                │
│                                                                                 │
│  mapping-library ──▶ mapping/{name}                                             │
│  (关联库全视图)      (单个映射详情)                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ④ 测试记录流程                                          │
│                                                                                 │
│  POST /api/test-records ──▶ GET /api/test-records ──▶ GET /api/test-records/{id}  │
│     (保存测试记录)          (查询记录列表)             (查看记录详情)                │
│                                                                                 │
│  GET /api/test-records/stats ──▶ DELETE /api/test-records/{id}                   │
│     (统计信息)                      (删除单条)                                    │
│                                                                                 │
│  POST /api/test-records/clear (清空所有)                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### ① 代码转换主流程

这是最核心的 API 组合，用户提交 GEE 代码并获取 OGE 转换结果。

#### 推荐调用顺序

```
步骤 1: 检查 LLM 可用性
  GET /api/llm-status
       │
       ▼ (available = true)
步骤 2: 提交转换请求
  POST /api/convert-llm
  (如果 LLM 不可用，改用 POST /api/convert)
       │
       ▼ (转换完成)
步骤 3: 保存结果缓存（可选，前端自动执行）
  POST /api/result-cache
       │
       ▼
步骤 4: 查询/使用历史记录
  GET /api/classes          (历史列表)
  GET /api/history/{id}     (历史详情)
```

#### 详细时序图

```
客户端                      服务器                     LLM服务
  │                         │                          │
  │ GET /api/llm-status     │                          │
  │────────────────────────▶│                          │
  │                         │  is_available()          │
  │                         │─────────────────────────▶│
  │                         │  true                    │
  │                         │◀─────────────────────────│
  │  {available: true}      │                          │
  │◀────────────────────────│                          │
  │                         │                          │
  │ POST /api/convert-llm   │                          │
  │  {gee_code: "..."}      │                          │
  │────────────────────────▶│                          │
  │                         │                          │
  │                         │  ┌─ 规则引擎 pipeline.run()
  │                         │  │   step1: analyze_gee_code()
  │                         │  │   step2-step6: 规则匹配
  │                         │  │
  │                         │  ├─ LLM 增强
  │                         │  │   generate_oge_code()
  │                         │  │   (含 step3 语义匹配)
  │                         │  │   (含 step5 Python实现建议)
  │                         │  │
  │                         │  └─ 保存到数据库
  │                         │                          │
  │  {result: {...},        │                          │
  │   llm_oge_code: "...",  │                          │
  │   record_id: 1}         │                          │
  │◀────────────────────────│                          │
  │                         │                          │
  │ POST /api/result-cache  │                          │
  │  {cache: {...}}         │                          │
  │────────────────────────▶│                          │
  │  {success: true}        │                          │
  │◀────────────────────────│                          │
```

#### 关键依赖关系

| 前置条件 | 接口 | 原因 |
|---------|------|------|
| LLM 可用 | `convert-llm` | 需要 LLM 做语义分析和代码生成 |
| GEE 代码非空 | `convert` / `convert-llm` | 两个接口都校验 `gee_code` |
| 规则引擎数据 | `convert` / `convert-llm` | 依赖数据库中的映射知识库 |

---

### ② 案例使用流程

用户浏览已有案例，选择后直接加载代码进行转换。

#### 调用顺序

```
步骤 1: 获取案例列表
  GET /api/examples
       │
       ▼
步骤 2: 选择一个案例，获取详情
  GET /api/examples/{case_id}
       │
       ▼ (前端自动填充表单)
步骤 3: 使用案例中的 GEE 代码进行转换
  POST /api/convert-llm
       │
       ▼
步骤 4: (可选) 添加自己的案例
  POST /api/examples
       │
       ▼ (案例列表自动刷新)
  GET /api/examples
```

#### 详细时序图

```
客户端                      服务器
  │                         │
  │ GET /api/examples      │
  │────────────────────────▶│
  │  {examples: [           │
  │    {id: "ndvi",         │
  │     name: "NDVI计算"}   │
  │  ]}                     │
  │◀────────────────────────│
  │                         │
  │ 用户点击案例             │
  │ GET /api/examples/ndvi │
  │────────────────────────▶│
  │  {example: {            │
  │    gee_code: "...",     │
  │    oge_code: "..."      │
  │  }}                     │
  │◀────────────────────────│
  │                         │
  │ 前端自动填充表单         │
  │ POST /api/convert-llm   │
  │  {gee_code: "..."}      │
  │────────────────────────▶│
  │  {转换结果}             │
  │◀────────────────────────│
  │                         │
  │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
  │ 新增案例流程             │
  │                         │
  │ POST /api/examples     │
  │  {name, gee_code, ...}  │
  │────────────────────────▶│
  │  {example: {id: "..."} }│
  │◀────────────────────────│
  │                         │
  │ GET /api/examples      │ ← 刷新列表
  │────────────────────────▶│
  │  {examples: [...]}      │
  │◀────────────────────────│
```

---

### ③ 知识库查询流程

开发者或用户浏览 GEE ↔ OGE 映射关系，用于了解 API 对应关系。

#### 三条并行查询路径

```
路径 A: 映射详情查询
  GET /api/mappings (筛选列表)
       │
       ▼
  GET /api/mapping/{gee_name} (单个映射详情)
       │
       ▼
  GET /api/oge-api-detail (OGE API 详细信息)

路径 B: 纯 GEE API 浏览
  GET /api/gee-apis (GEE API 列表)
       │
       ▼
  GET /api/gee-samplecodes (有示例的 API)
       │
       ▼
  GET /api/gee-samplecode/{name} (示例代码详情)

路径 C: 关联库全视图
  GET /api/mapping-library (全量映射视图)
       │
       ▼ (按 mapped/unmapped 过滤)
  GET /api/mapping/{gee_name} (单个详情)
       │
       ▼ (如果 mapped = native_python)
  GET /api/native-python (Python 原生实现)
```

#### 数据依赖关系

```
gee_api_info 表          operator_mapping 表        oge_api_info 表
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ ee.Image    │───────▶│ one_to_one  │────────▶│ Coverage    │
│ ee.Number   │───────▶│ native_python│────────▶│ (Python实现) │
└─────────────┘         └─────────────┘         └─────────────┘
       ▲                      ▲                        ▲
       │                      │                        │
       └──────────────────────┴────────────────────────┘
                       由以下 API 查询：
                       - /api/mappings
                       - /api/mapping-library
                       - /api/gee-apis
                       - /api/oge-apis
```

---

### ④ 测试记录流程

测试人员记录接口调用情况，用于质量分析。

#### 调用顺序

```
步骤 1: 执行 API 调用后保存记录
  POST /api/test-records
       │
       ▼
步骤 2: 查看记录列表
  GET /api/test-records
       │
       ▼ (点击某条记录)
步骤 3: 查看记录详情
  GET /api/test-records/{id}
       │
       ▼
步骤 4: 查看统计信息
  GET /api/test-records/stats
       │
       ▼ (清理数据)
步骤 5a: 删除单条
  DELETE /api/test-records/{id}
  
步骤 5b: 清空所有
  POST /api/test-records/clear
```

---

### 接口间数据流转

```
                    ┌─────────────────────┐
                    │   GEE 源代码输入     │
                    └───────────┬─────────┘
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
          ┌──────────┐   ┌──────────────┐   ┌──────────┐
          │案例 API  │   │ 转换 API     │   │知识库 API│
          │examples  │   │convert-llm   │   │mappings  │
          └────┬─────┘   └──────┬───────┘   └────┬─────┘
               │                │                │
               │                ▼                │
               │        ┌──────────────┐         │
               │        │ 结果缓存 API │         │
               │        │result-cache  │         │
               │        └──────┬───────┘         │
               │               │                 │
               ▼               ▼                 ▼
          ┌─────────────────────────────────────────┐
          │           历史记录 API                 │
          │   /api/classes + /api/history/{id}    │
          └──────────────────┬──────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   测试记录 API    │
                    │ test-records/*   │
                    └──────────────────┘
```

---

### 典型使用场景

#### 场景 1: 快速转换一个 GEE 脚本

```bash
# 1. 检查 LLM
curl http://localhost:5001/api/llm-status

# 2. 提交转换
curl -X POST http://localhost:5001/api/convert-llm \
  -H "Content-Type: application/json" \
  -d '{"gee_code": "var image = ee.Image(...);", "case_name": "test"}'

# 3. 查看结果中的 llm_oge_code 字段
```

#### 场景 2: 浏览已有案例并复用

```bash
# 1. 获取案例列表
curl http://localhost:5001/api/examples

# 2. 加载某个案例
curl http://localhost:5001/api/examples/ndvi_calculator

# 3. 用案例的 gee_code 做转换
```

#### 场景 3: 查看 GEE API 对应的 OGE 实现

```bash
# 1. 搜索 GEE API
curl "http://localhost:5001/api/gee-apis?keyword=filter&class=FeatureCollection"

# 2. 查看映射详情
curl "http://localhost:5001/api/mapping/ee.Filter.date"

# 3. 如果是 native_python 类型
curl "http://localhost:5001/api/native-python?keyword=Number"
```

#### 场景 4: 批量测试 API 并统计

```bash
# 1. 执行 API 调用后保存测试记录
curl -X POST http://localhost:5001/api/test-records \
  -d '{"api_id":"convert-llm",...}'

# 2. 查看统计
curl http://localhost:5001/api/test-records/stats

# 3. 按接口筛选
curl "http://localhost:5001/api/test-records?api_id=convert-llm&success=true"
```

---

## 📋 接口目录

### 📄 页面路由
- [GET /](#get-) - 主页
- [GET /test](#get-test) - API 测试页面

### 🔄 代码转换
- [GET /api/llm-status](#get-apillm-status) - 检测 LLM 服务可用性
- [POST /api/convert](#post-apiconvert) - GEE→OGE 转换（规则引擎版）
- [POST /api/convert-llm](#post-apiconvert-llm) - GEE→OGE 转换（LLM 增强版）

### 💾 结果缓存
- [GET /api/result-cache](#get-apiresult-cache) - 获取所有结果缓存
- [POST /api/result-cache](#post-apiresult-cache) - 保存结果缓存
- [DELETE /api/result-cache](#delete-apiresult-cache) - 清空结果缓存

### 🗺️ 算子映射库
- [GET /api/mappings](#get-apimappings) - 查询算子映射知识库
- [GET /api/mapping/{gee_name}](#get-apimappinggeek_name) - 查询单个映射详情
- [GET /api/mapping-library](#get-apimapping-library) - 查询 GEE-OGE 关联映射库

### 📚 API 知识库
- [GET /api/gee-apis](#get-apigee-apis) - 查询 GEE API 列表
- [GET /api/oge-apis](#get-apioge-apis) - 查询 OGE API 列表
- [GET /api/oge-api-detail](#get-apioge-api-detail) - 查询单个 OGE API 详情
- [GET /api/native-python](#get-apinative-python) - 查询 Python 原生实现

### 📝 示例代码
- [GET /api/gee-samplecodes](#get-apigee-samplecodes) - 查询 GEE 示例代码列表
- [GET /api/gee-samplecode/{name}](#get-apigee-samplecodename) - 查询单个示例代码详情

### 📖 案例管理
- [GET /api/examples](#get-apiexamples) - 获取案例列表
- [GET /api/examples/{case_id}](#get-apiexamplescase_id) - 获取案例详情
- [POST /api/examples](#post-apiexamples) - 添加新案例
- [PUT /api/examples/{case_id}](#put-apiexamplescase_id) - 修改案例
- [DELETE /api/examples/{case_id}](#delete-apiexamplescase_id) - 删除案例
- [POST /api/examples/analyze](#post-apiexamplesanalyze) - AI 智能检测案例元数据

### 🧪 测试记录
- [GET /api/test-records](#get-apitest-records) - 查询测试记录列表
- [POST /api/test-records](#post-apitest-records) - 保存测试记录
- [GET /api/test-records/{id}](#get-apitest-recordsid) - 查询测试记录详情
- [DELETE /api/test-records/{id}](#delete-apitest-recordsid) - 删除测试记录
- [POST /api/test-records/clear](#post-apitest-recordsclear) - 清空所有测试记录
- [GET /api/test-records/stats](#get-apitest-recordsstats) - 测试记录统计

### 🎯 Benchmark 测试集
- [GET /api/benchmark-cases](#get-apibenchmark-cases) - 获取 benchmark 测试集案例列表
- [GET /api/benchmark-case/{case_id}](#get-apibenchmark-casecase_id) - 获取单个 benchmark 案例详情

### 🔄 反向转换
- [POST /api/oge-to-gee](#post-apioge-to-gee) - OGE 代码反向转换为 GEE 代码

### 📊 统计
- [GET /api/classes](#get-apiclasses) - 查询历史转换记录
- [GET /api/history/{id}](#get-apihistoryid) - 查询历史记录详情
- [GET /api/stats](#get-apistats) - 知识库统计信息

---

## 📄 页面路由

### GET /

**描述**：返回主页模板，包含代码转换、知识库、历史记录等功能模块。

**请求参数**：无

**响应**：
```
Content-Type: text/html
返回 HTML 页面
```

---

### GET /test

**描述**：返回接口测试页面，用于调试和验证所有 API 功能。

**请求参数**：无

**响应**：
```
Content-Type: text/html
返回 HTML 页面
```

---

## 🔄 代码转换

### GET /api/llm-status

**描述**：检测本地 LLM 服务是否可用，返回模型信息和连接地址。

**请求参数**：无

**成功响应示例**：
```json
{
  "success": true,
  "available": true,
  "model": "qwen2.5:7b",
  "base_url": "http://localhost:11434/v1"
}
```

**失败响应示例**：
```json
{
  "success": false,
  "error": "连接超时",
  "available": false
}
```

---

### POST /api/convert

**描述**：使用规则引擎将 GEE JavaScript 代码转换为 OGE Python 代码，不依赖 LLM。

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `gee_code` | string | **必填** | GEE JavaScript 源代码 |
| `case_name` | string | 可选 | 案例名称，默认"未命名案例" |

**请求示例**：
```json
{
  "gee_code": "var image = ee.Image('LANDSAT/LC08/C02/T1_TOA');\nMap.addLayer(image);",
  "case_name": "Landsat影像加载"
}
```

**响应示例**：
```json
{
  "success": true,
  "engine": "rule_based",
  "record_id": 1,
  "result": {
    "step1": {
      "task_goal": "加载并显示Landsat影像",
      "workflow_steps": ["加载影像", "添加到地图"]
    },
    "step6": {
      "oge_code": "import oge\noge.initialize()\nservice = oge.Service()\nservice.getCoverage(...)\n..."
    }
  }
}
```

---

### POST /api/convert-llm ⭐推荐

**描述**：使用规则引擎 + LLM 增强的方式转换代码。

**处理流程**：
1. 规则引擎执行 6 步流水线
2. LLM 分析代码意图、变量类型和步骤拆分
3. LLM 生成完整 OGE Python 代码
4. LLM 对缺失 API 做语义匹配和 Python 实现建议

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `gee_code` | string | **必填** | GEE JavaScript 源代码 |
| `case_name` | string | 可选 | 案例名称 |

**请求示例**：
```json
{
  "gee_code": "var collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_TOA')\n  .filterDate('2023-01-01', '2023-12-31')\n  .filterBounds(ee.Geometry.Point([-119.56, 37.67]));\n\nvar ndvi = collection.map(function(image) {\n  var ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI');\n  return image.addBands(ndvi);\n});\n\nvar maxNdvi = ndvi.select('NDVI').max();\nMap.addLayer(maxNdvi, {min: 0, max: 1}, 'Max NDVI');\nMap.setCenter(-119.56, 37.67, 10);",
  "case_name": "NDVI年度最大值"
}
```

**响应示例**：
```json
{
  "success": true,
  "engine": "llm_enhanced",
  "llm_available": true,
  "record_id": 1,
  "result": {
    "step1": {
      "task_goal": "计算2023年Landsat8影像的最大NDVI并可视化",
      "workflow_steps": [
        "加载并过滤Landsat8影像集合",
        "为每景影像计算NDVI",
        "计算年度NDVI最大值",
        "添加图层到地图",
        "设置地图中心点"
      ],
      "key_params": {
        "time_range": "2023-01-01 to 2023-12-31",
        "data_source": "LANDSAT/LC08/C02/T1_TOA"
      }
    },
    "step3": {
      "match_rate": 1.0,
      "matched_count": 5,
      "missing_count": 0
    },
    "step6": {
      "oge_code": "import oge\noge.initialize()\nservice = oge.Service()\nservice.getCoverageCollection(...)\n...",
      "llm_generated": true
    },
    "llm_oge_code": "import oge\noge.initialize()\nservice = oge.Service()\n...",
    "llm_enhancements": ["LLM 任务目标: 计算2023年Landsat8影像的最大NDVI"]
  }
}
```

---

## 💾 结果缓存

### GET /api/result-cache

**描述**：获取所有保存的转换结果缓存。

**请求参数**：无

**响应示例**：
```json
{
  "success": true,
  "cache": {
    "key_1": {
      "gee_code": "var image = ee.Image(...)",
      "oge_code": "import oge\n...",
      "created_at": "2024-01-01T10:00:00"
    }
  }
}
```

---

### POST /api/result-cache

**描述**：整体覆盖保存结果缓存。

**请求体示例**：
```json
{
  "key_1": {
    "gee_code": "var image = ee.Image(...)",
    "oge_code": "import oge\n..."
  }
}
```

**响应示例**：
```json
{ "success": true }
```

---

### DELETE /api/result-cache

**描述**：删除所有结果缓存文件。

**请求参数**：无

**响应示例**：
```json
{ "success": true }
```

---

## 🗺️ 算子映射库

### GET /api/mappings

**描述**：查询 GEE→OGE 算子映射知识库，支持类型、关键词、类名过滤和分页。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `type` | string | 可选 | 映射类型：`all`/`one_to_one`/`one_to_many`/`many_to_one`/`native_python` |
| `keyword` | string | 可选 | 按 API 名或描述搜索 |
| `class` | string | 可选 | 按 GEE 类名过滤 |
| `page` | int | 可选 | 页码，默认 1 |
| `per_page` | int | 可选 | 每页条数，默认 50，上限 200 |

**请求示例**：
```
GET /api/mappings?type=all&keyword=Image&page=1&per_page=10
```

**响应示例**：
```json
{
  "success": true,
  "total": 251,
  "page": 1,
  "per_page": 50,
  "data": [
    {
      "gee_api": {
        "full_name": "ee.Image",
        "class_name": "Image",
        "description": "影像对象"
      },
      "oge_api": "Coverage",
      "mapping_type": "one_to_one",
      "confidence": 0.95,
      "has_python_code": false
    }
  ]
}
```

---

### GET /api/mapping/{gee_name}

**描述**：查询单个 GEE API 的完整映射详情。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `gee_name` | string | **必填** | GEE API 全名，如 `ee.Image`（需 URL 编码） |

**请求示例**：
```
GET /api/mapping/ee.Image
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "gee_api": {
      "api_full_name": "ee.Image",
      "class_name": "Image"
    },
    "oge_api": {
      "api_name": "Coverage",
      "catalog_name": "基础算子",
      "description": "栅格数据读取",
      "input_types": ["productID", "bbox"],
      "output_type": "Coverage"
    },
    "mapping_type": "one_to_one",
    "confidence": 0.95
  }
}
```

---

### GET /api/mapping-library

**描述**：返回所有 GEE API 及其映射状态，用于关联库视图。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `keyword` | string | 可选 | 按 API 名或描述搜索 |
| `class` | string | 可选 | 按 GEE 类名过滤 |
| `mapping` | string | 可选 | 映射状态：`mapped`/`unmapped`/`all` |
| `mapping_type` | string | 可选 | 映射类型过滤 |
| `page` | int | 可选 | 页码，默认 1 |
| `per_page` | int | 可选 | 每页条数，默认 50 |

**响应示例**：
```json
{
  "success": true,
  "total": 300,
  "data": [
    {
      "api_full_name": "ee.Image",
      "class_name": "Image",
      "description": "影像对象",
      "mapped": true,
      "mapping_type": "one_to_one",
      "oge_api_name": "Coverage"
    }
  ]
}
```

---

## 📚 API 知识库

### GET /api/gee-apis

**描述**：查询 GEE API 列表，支持搜索和分页。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `keyword` | string | 可选 | 按全名/类名/描述搜索 |
| `class` | string | 可选 | 按 GEE 类名过滤 |
| `page` | int | 可选 | 页码，默认 1 |
| `per_page` | int | 可选 | 每页条数，默认 50，上限 200 |

**响应示例**：
```json
{
  "success": true,
  "total": 150,
  "data": [
    {
      "id": 1,
      "api_full_name": "ee.Image",
      "class_name": "Image",
      "description": "影像对象",
      "arg_types": ["string"],
      "samplecode": "var img = ee.Image('...');"
    }
  ]
}
```

---

### GET /api/oge-apis

**描述**：查询 OGE API 列表，支持搜索和分页。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `keyword` | string | 可选 | 按 API 名/描述/目录名搜索 |
| `catalog` | string | 可选 | 按目录名过滤 |
| `page` | int | 可选 | 页码，默认 1 |
| `per_page` | int | 可选 | 每页条数，默认 50，上限 200 |

**响应示例**：
```json
{
  "success": true,
  "total": 100,
  "data": [
    {
      "api_name": "Coverage.selectBands",
      "catalog_name": "基础算子",
      "description": "选择影像波段",
      "input_types": ["Coverage", "list"],
      "output_type": "Coverage"
    }
  ]
}
```

---

### GET /api/oge-api-detail

**描述**：查询单个 OGE API 详情。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `api_name` | string | **必填** | OGE API 名称，如 `Coverage.selectBands` |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "api_name": "Coverage.selectBands",
    "catalog_name": "基础算子",
    "description": "选择影像波段",
    "input_types": ["Coverage", "list"],
    "output_type": "Coverage",
    "samplecode": "result = service.getProcess('Coverage.selectBands').execute(img, ['B4'])"
  }
}
```

---

### GET /api/native-python

**描述**：查询所有标记为 Python 原生实现的映射，含完整 Python 代码。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `keyword` | string | 可选 | 按 API 名搜索 |
| `page` | int | 可选 | 页码，默认 1 |
| `per_page` | int | 可选 | 每页条数，默认 50 |

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "gee_api": { /* GEE API 信息 */ },
      "native_python_code": "def eeNumber(value):\n    return float(value)",
      "dependencies": ["math"],
      "example": "result = eeNumber(42)"
    }
  ]
}
```

---

## 📝 示例代码

### GET /api/gee-samplecodes

**描述**：查询有示例代码的 GEE API 列表。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `keyword` | string | 可选 | 按全名/类名/描述搜索 |
| `class` | string | 可选 | 按 GEE 类名过滤 |
| `page` | int | 可选 | 页码，默认 1 |

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "fullName": "ee.Image.abs",
      "className": "Image",
      "description": "计算影像绝对值",
      "samplecode": "var result = image.abs();",
      "source": "generated"
    }
  ]
}
```

---

### GET /api/gee-samplecode/{name}

**描述**：查询单个 GEE API 的完整示例代码详情。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | **必填** | GEE API 全名，如 `ee.Image.abs` |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "fullName": "ee.Image.abs",
    "className": "Image",
    "description": "计算影像绝对值",
    "arguments": [{ "name": "param1", "type": "Image" }],
    "samplecodes": [{ "order": 1, "code": "var result = image.abs();" }]
  }
}
```

---

## 📖 案例管理

### GET /api/examples

**描述**：获取案例列表。

**请求参数**：无

**响应示例**：
```json
{
  "success": true,
  "examples": [
    {
      "id": "ndvi_calculator",
      "name": "NDVI 计算",
      "description": "计算年度NDVI最大值",
      "tags": ["NDVI", "Landsat"],
      "difficulty": "medium",
      "has_oge": true
    }
  ]
}
```

---

### GET /api/examples/{case_id}

**描述**：获取案例详情。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `case_id` | string | **必填** | 案例 ID，如 `ndvi_calculator` |

**响应示例**：
```json
{
  "success": true,
  "example": {
    "id": "ndvi_calculator",
    "name": "NDVI 计算",
    "gee_code": "var collection = ee.ImageCollection(...)\n...",
    "oge_code": "import oge\noge.initialize()\n...",
    "description": "计算年度NDVI最大值"
  }
}
```

---

### POST /api/examples

**描述**：添加新案例到案例库。

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | **必填** | 案例名称 |
| `gee_code` | string | **必填** | GEE JavaScript 代码 |
| `oge_code` | string | 可选 | OGE Python 代码 |
| `description` | string | 可选 | 案例描述 |
| `tags` | array | 可选 | 标签数组 |
| `source` | string | 可选 | 数据来源 |
| `difficulty` | string | 可选 | 难度：`easy`/`medium`/`hard`，默认 `medium` |

**请求示例**：
```json
{
  "name": "NDVI 测试案例",
  "gee_code": "var image = ee.Image('LANDSAT/LC08/C02/T1_TOA');\nvar ndvi = image.normalizedDifference(['B5', 'B4']);\nMap.addLayer(ndvi);",
  "oge_code": "import oge\noge.initialize()\nservice = oge.Service()",
  "description": "简单的 NDVI 计算",
  "tags": ["测试", "NDVI"],
  "difficulty": "easy"
}
```

**响应示例**：
```json
{
  "success": true,
  "example": {
    "id": "NDVI_测试案例_1785909109",
    "name": "NDVI 测试案例"
  }
}
```

---

### PUT /api/examples/{case_id}

**描述**：修改已有案例的信息，支持部分字段更新（只需要提供要修改的字段）。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `case_id` | string | **必填** | 案例 ID |

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | 可选 | 案例名称（修改时不能为空字符串） |
| `gee_code` | string | 可选 | GEE JavaScript 代码 |
| `oge_code` | string | 可选 | OGE Python 代码（传空字符串则删除文件） |
| `description` | string | 可选 | 案例描述 |
| `tags` | array | 可选 | 标签数组 |
| `source` | string | 可选 | 数据来源 |
| `difficulty` | string | 可选 | 难度：`easy`/`medium`/`hard` |

**请求示例**：
```json
{
  "name": "NDVI 计算（已更新）",
  "description": "更新后的案例描述",
  "tags": ["NDVI", "Landsat", "更新"],
  "difficulty": "medium"
}
```

**响应示例**：
```json
{
  "success": true,
  "example": {
    "id": "NDVI_测试案例_1785909109",
    "name": "NDVI 计算（已更新）",
    "description": "更新后的案例描述",
    "tags": ["NDVI", "Landsat", "更新"],
    "source": "",
    "difficulty": "medium"
  }
}
```

**错误响应**：
```json
// 案例不存在
{ "success": false, "error": "案例不存在" }  // HTTP 404

// 名称为空
{ "success": false, "error": "案例名称不能为空" }  // HTTP 400
```

---

### DELETE /api/examples/{case_id}

**描述**：删除指定案例，移除案例目录及其所有文件（meta.json、gee.txt、oge.txt）。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `case_id` | string | **必填** | 案例 ID |

**请求示例**：
```
DELETE /api/examples/NDVI_测试案例_1785909109
```

**响应示例**：
```json
{
  "success": true,
  "message": "案例 NDVI_测试案例_1785909109 已删除"
}
```

**错误响应**：
```json
// 案例不存在
{ "success": false, "error": "案例不存在" }  // HTTP 404
```

### POST /api/examples/analyze

**描述**：使用 LLM 智能分析 GEE/OGE 代码，自动提取案例元数据（名称、描述、标签等），用于案例添加/编辑时的 AI 自动填充。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `gee_code` | string | **必填** | GEE JavaScript 代码 |
| `oge_code` | string | 可选 | OGE Python 代码，用于辅助分析 |

**请求示例**：
```json
POST /api/examples/analyze
Content-Type: application/json

{
  "gee_code": "var ndvi = image.normalizedDifference(['B5', 'B4']);",
  "oge_code": ""
}
```

**响应示例**：
```json
{
  "success": true,
  "metadata": {
    "name": "NDVI 植被指数计算",
    "description": "使用 Landsat 影像的 B5 和 B4 波段计算归一化植被指数 (NDVI)",
    "source": "Landsat 8/9",
    "difficulty": "medium",
    "tags": ["NDVI", "植被指数", "Landsat", "波段运算"],
    "task_goal": "计算归一化植被指数",
    "key_params": "波段名：B5(NIR), B4(Red)；运算符：normalizedDifference",
    "workflow_steps": ["加载影像", "计算 NDVI", "可视化结果"]
  }
}
```

**错误响应**：
```json
// LLM 服务不可用
{ "success": false, "error": "LLM 服务不可用，请先启动 Ollama 服务" }  // HTTP 503

// 代码为空
{ "success": false, "error": "GEE 代码不能为空" }  // HTTP 400
```

---

## 🧪 测试记录

### GET /api/test-records

**描述**：查询测试记录列表。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `api_id` | string | 可选 | 按接口 ID 过滤 |
| `success` | string | 可选 | 按成功状态：`true`/`false` |
| `page` | int | 可选 | 页码，默认 1 |
| `per_page` | int | 可选 | 每页条数，默认 20，上限 100 |

**响应示例**：
```json
{
  "success": true,
  "total": 50,
  "data": [
    {
      "id": 1,
      "api_id": "convert-llm",
      "api_path": "/api/convert-llm",
      "method": "POST",
      "status_code": 200,
      "response_time": 3500,
      "success": true
    }
  ]
}
```

---

### POST /api/test-records

**描述**：保存测试记录。

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `api_id` | string | **必填** | 接口 ID |
| `api_path` | string | **必填** | 接口路径 |
| `method` | string | **必填** | 请求方法 |
| `request_params` | string | 可选 | 请求参数 JSON 字符串 |
| `request_time` | string | **必填** | 请求时间 ISO 格式 |
| `status_code` | int | **必填** | 响应状态码 |
| `response_time` | int | 可选 | 响应耗时（毫秒） |
| `response_body` | string | 可选 | 响应体 JSON 字符串 |
| `success` | int | **必填** | 是否成功：0/1 |
| `error_message` | string | 可选 | 错误信息 |

**请求示例**：
```json
{
  "api_id": "convert-llm",
  "api_path": "/api/convert-llm",
  "method": "POST",
  "request_params": "{\"gee_code\": \"...\"}",
  "request_time": "2024-01-01T10:00:00",
  "status_code": 200,
  "response_time": 3500,
  "response_body": "{\"success\": true}",
  "success": 1
}
```

**响应示例**：
```json
{ "success": true, "id": 1 }
```

---

### GET /api/test-records/{id}

**描述**：查询单条测试记录详情。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | int | **必填** | 记录 ID |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "api_id": "convert-llm",
    "api_path": "/api/convert-llm",
    "response_body": "{\"success\": true, \"result\": {...}}",
    "success": true
  }
}
```

---

### DELETE /api/test-records/{id}

**描述**：删除单条测试记录。

**响应示例**：
```json
{ "success": true }
```

---

### POST /api/test-records/clear

**描述**：清空所有测试记录。

**响应示例**：
```json
{ "success": true }
```

---

### GET /api/test-records/stats

**描述**：获取测试记录统计信息。

**响应示例**：
```json
{
  "success": true,
  "data": {
    "total": 100,
    "success_rate": 0.85,
    "by_api": [{ "api": "convert-llm", "count": 50 }]
  }
}
```

---

## 📊 统计

### GET /api/classes

**描述**：查询历史转换记录列表。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `limit` | int | 可选 | 返回条数，默认 20，上限 100 |

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "case_name": "NDVI 计算",
      "engine": "llm_enhanced",
      "created_at": "2024-01-01T10:00:00"
    }
  ]
}
```

---

### GET /api/history/{record_id}

**描述**：查询单条历史记录详情。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `record_id` | int | **必填** | 记录 ID |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "case_name": "NDVI 计算",
    "gee_code": "var collection = ee.ImageCollection(...)",
    "result": { /* 完整转换结果 */ }
  }
}
```

---

### GET /api/stats

**描述**：获取知识库统计信息，包括 LLM 状态。

**请求参数**：无

**响应示例**：
```json
{
  "success": true,
  "data": {
    "total_gee_apis": 150,
    "total_oge_apis": 100,
    "total_mappings": 251,
    "by_mapping_type": {
      "one_to_one": 100,
      "one_to_many": 30,
      "native_python": 50
    },
    "history_count": 30,
    "llm_available": true
  }
}
```

---

## 🎯 Benchmark 测试集

### GET /api/benchmark-cases

**描述**：获取 benchmark 测试集案例列表。返回 `benchmark_with_dag_rebalanced_v4.json` 中所有案例的摘要信息（不含 dag 等大字段，减少传输量）。

**请求参数**：无

**响应示例**：
```json
{
  "success": true,
  "cases": [
    {
      "case_id": "T0001",
      "task_type": "影像加载",
      "description": "加载 Landsat 8 影像并显示",
      "difficulty": "简单",
      "lang": "python",
      "code_length": 120,
      "notes": "",
      "data_ref": "LANDSAT/LC08"
    }
  ],
  "total": 50
}
```

**错误响应**：
```json
{ "success": false, "error": "Benchmark 文件不存在" }  // HTTP 404
```

---

### GET /api/benchmark-case/{case_id}

**描述**：获取单个 benchmark 案例的完整信息（含完整 OGE 代码、dag 等）。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `case_id` | string | **必填** | 案例 ID，如 `T0001` |

**响应示例**：
```json
{
  "success": true,
  "case": {
    "case_id": "T0001",
    "task_type": "影像加载",
    "description": "加载 Landsat 8 影像并显示",
    "difficulty": "简单",
    "lang": "python",
    "code": "import oge\noge.initialize()\nservice = oge.Service()\ncoverage = service.getCoverage(...)",
    "notes": "",
    "data_ref": "LANDSAT/LC08",
    "dag": { }
  }
}
```

**错误响应**：
```json
// 文件不存在
{ "success": false, "error": "Benchmark 文件不存在" }  // HTTP 404

// 案例不存在
{ "success": false, "error": "案例 T0001 不存在" }  // HTTP 404
```

---

## 🔄 反向转换

### POST /api/oge-to-gee

**描述**：使用 LLM 将 OGE Python 代码反向转换为 GEE JavaScript 代码。LLM 分析 OGE 代码的算子调用语义，映射回等效的 Google Earth Engine JavaScript 代码。依赖 LLM 服务可用。

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `oge_code` | string | **必填** | OGE Python 代码 |
| `description` | string | 可选 | 任务描述，辅助 LLM 理解意图 |

**请求示例**：
```json
POST /api/oge-to-gee
Content-Type: application/json

{
  "oge_code": "import oge\noge.initialize()\nservice = oge.Service()\ncoverage = service.getCoverage(coverageID=\"LC08_L1TP_119038_20230104\", productID=\"LC08_C02_L1\")\nred = service.getProcess(\"Coverage.selectBands\").execute(coverage, [\"B4\"])\nred.styles({\"min\":0,\"max\":0.3}).getMap(\"Red Band\")\noge.mapclient.centerMap(120.5, 32.0, 9)",
  "description": "加载 Landsat 影像并显示红波段"
}
```

**响应示例**：
```json
{
  "success": true,
  "gee_code": "var image = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_119038_20230104');\nvar red = image.select('B4');\nMap.addLayer(red, {min:0, max:0.3}, 'Red Band');\nMap.setCenter(120.5, 32.0, 9);",
  "explanations": [
    "service.getCoverage → ee.Image",
    "Coverage.selectBands → .select()",
    ".styles().getMap() → Map.addLayer()",
    "oge.mapclient.centerMap() → Map.setCenter()"
  ],
  "warnings": [],
  "feasible": true,
  "elapsed_ms": 8500.5
}
```

**错误响应**：
```json
// 代码为空
{ "success": false, "error": "OGE 代码不能为空" }  // HTTP 400

// LLM 不可用
{ "success": false, "error": "LLM 服务不可用，请检查本地大模型 API 连接" }  // HTTP 503
```

---

## 🎯 Benchmark 批量转换

### POST /api/benchmark-batch-convert（异步）

**描述**：异步批量将 benchmark 测试集的 OGE Python 代码转换为 GEE JavaScript 代码。立即返回任务 ID，后台线程逐个案例调用 LLM 的 `oge_to_gee` 方法。支持按 difficulty / task_type 过滤，支持断点续跑（resume=true 跳过已完成的案例）。结果实时写入 `resource/benchmark_convert_results.json`。使用 `GET /api/benchmark-batch-status?task_id=...` 查询进度。

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `difficulty` | string | 可选 | 按难度过滤（如 `"简单"`/`"中等"`/`"困难"`） |
| `task_type` | string | 可选 | 按任务类型过滤（如 `"image_processing"`） |
| `resume` | boolean | 可选 | 是否断点续跑，默认 `true`（跳过已有结果的案例） |
| `force` | boolean | 可选 | 是否强制重新转换所有案例，默认 `false` |

**请求示例**：
```json
POST /api/benchmark-batch-convert
Content-Type: application/json

{}
```

```json
// 只转换中等难度的案例，断点续跑
{
  "difficulty": "中等",
  "resume": true
}
```

```json
// 强制重新转换所有案例
{
  "force": true
}
```

**响应示例**：
```json
{
  "success": true,
  "task_id": "a1b2c3d4",
  "message": "已启动后台批量转换任务，共 147 个案例。使用 GET /api/benchmark-batch-status?task_id=a1b2c3d4 查询进度。",
  "total": 147
}
```

**错误响应**：
```json
// LLM 不可用
{ "success": false, "error": "LLM 服务不可用，请检查本地大模型 API 连接" }  // HTTP 503

// 无符合条件的案例
{ "success": false, "error": "没有符合条件的案例" }  // HTTP 400

// Benchmark 文件不存在
{ "success": false, "error": "Benchmark 文件不存在" }  // HTTP 404
```

---

### GET /api/benchmark-batch-status

**描述**：查询批量转换任务的进度。支持按 task_id 查询单个任务，或不传参数返回所有任务状态。

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `task_id` | string | 可选 | 任务 ID，由 POST /api/benchmark-batch-convert 返回。不传则返回所有任务 |

**请求示例**：
```bash
# 查询单个任务进度
curl "http://127.0.0.1:5001/api/benchmark-batch-status?task_id=a1b2c3d4"

# 查询所有任务
curl http://127.0.0.1:5001/api/benchmark-batch-status
```

**响应示例（单任务）**：
```json
{
  "success": true,
  "data": {
    "status": "running",
    "total": 147,
    "converted": 42,
    "skipped": 0,
    "failed": 0,
    "progress": 28.6,
    "elapsed_ms": 358000.0,
    "start_time": "2026-08-19T11:30:00"
  }
}
```

**响应示例（所有任务）**：
```json
{
  "success": true,
  "tasks": [
    {"task_id": "a1b2c3d4", "status": "running", "progress": 28.6, ...},
    {"task_id": "e5f6g7h8", "status": "completed", "progress": 100.0, ...}
  ]
}
```

---

### GET /api/benchmark-batch-result

**描述**：获取已保存的 benchmark 批量转换结果。如果尚未执行批量转换，返回空结果和提示信息。

**请求参数**：无

**响应示例**：
```json
{
  "success": true,
  "data": {
    "total": 50,
    "converted": 50,
    "skipped": 0,
    "failed": 0,
    "elapsed_ms": 420000.0,
    "results": [
      {
        "case_id": "T0001",
        "llm_gee_code": "...",
        "ground_truth_gee": "...",
        "status": "success",
        "..."
      }
    ]
  }
}
```

**空结果响应**：
```json
{
  "success": true,
  "data": {
    "total": 0,
    "converted": 0,
    "skipped": 0,
    "failed": 0,
    "elapsed_ms": 0,
    "results": [],
    "message": "暂无批量转换结果，请先调用 POST /api/benchmark-batch-convert"
  }
}
```

---

### DELETE /api/benchmark-batch-result

**描述**：清空已保存的 benchmark 批量转换结果文件。

**请求参数**：无

**响应示例**：
```json
{ "success": true }
```

---

### DELETE /api/benchmark-batch-status/{task_id}

**描述**：清除已完成的任务状态记录（仅清除内存中的任务状态，不删除已保存的结果文件）。

**路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `task_id` | string | **必填** | 任务 ID |

**响应示例**：
```json
{ "success": true }
```

**错误响应**：
```json
{ "success": false, "error": "任务 a1b2c3d4 不存在" }  // HTTP 404
```

---

## 附录：HTTP 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 OK | 请求成功 |
| 400 Bad Request | 请求参数错误（如缺少必填参数） |
| 404 Not Found | 资源不存在（如案例 ID 无效） |
| 409 Conflict | 资源冲突（如案例 ID 已存在） |
| 500 Internal Server Error | 服务器内部错误 |
| 503 Service Unavailable | LLM 服务不可用 |

---

## 附录：映射类型说明

| 类型 | 说明 |
|------|------|
| `one_to_one` | GEE API → 一个 OGE API |
| `one_to_many` | GEE API → 多个 OGE API 组合 |
| `many_to_one` | 多个 GEE API → 一个 OGE API |
| `native_python` | 用 Python 原生语法实现，无需调用 OGE API |
| `llm_semantic` | LLM 语义匹配（通过 `match_gee_to_oge` 推断） |