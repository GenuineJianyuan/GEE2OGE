"""
GEE2OGE 迁移系统 - 本地大模型服务模块

对接本地部署的 deepseek-v4-flash-0731 模型，
为 GEE→OGE 转换流水线提供智能增强：
1. 语义匹配增强：当数据库无精确映射时，用 LLM 推断最接近的 OGE API
2. 自然语言解析：从代码上下文推断变量类型和 API 意图
3. 代码优化：生成更地道的 OGE 代码
4. 代码生成：基于算子映射和 OGE 语法指南生成可执行的 OGE Python 代码
"""

import json
import os
import re
import sys
import traceback
from typing import Any, Dict, List, Optional

import requests

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# ============================================================
# LLM API 配置（本地部署）
# 支持通过环境变量覆盖，便于不同环境（本地/集群）部署时无需改代码
# 环境变量：LLM_BASE_URL / LLM_API_KEY / LLM_MODEL /
#           LLM_TIMEOUT_SECONDS / LLM_ENABLE_THINKING
# ============================================================
LLM_CONFIG = {
    "base_url": os.environ.get("LLM_BASE_URL", "http://111.37.195.37:8015/v1"),
    "api_key": os.environ.get("LLM_API_KEY", "sk-chenwenjielocalhost"),
    "model": os.environ.get("LLM_MODEL", "deepseek-v4-flash-0731"),
    "max_tokens": 4096,
    "temperature": 0.1,
    "timeout_seconds": int(os.environ.get("LLM_TIMEOUT_SECONDS", "420")),
    "enable_thinking": os.environ.get("LLM_ENABLE_THINKING", "false").lower() in ("true", "1", "yes"),
}

# ============================================================
# 加载 OGE 代码生成规则（从资源文件）
# ============================================================
RULES_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resource', 'oge_step_codegen.txt')


def load_codegen_rules() -> str:
    """加载 OGE 代码生成规则文件

    从 resource/oge_step_codegen.txt 读取规则内容，
    用于指导 LLM 生成符合规范的 OGE Python 代码。

    Returns:
        str: 规则文件内容，如果文件不存在返回默认规则
    """
    try:
        if os.path.exists(RULES_FILE_PATH):
            with open(RULES_FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return content
    except Exception:
        pass
    
    # 默认规则（文件不存在时使用）
    return """你是一个 OGE Python 代码生成助手。针对单个步骤生成 OGE 代码。

初始化骨架：
import oge
oge.initialize()
service = oge.Service()

算子调用：
result = service.getProcess("算子名").execute(位置参数)

数据加载：
- Coverage: service.getCoverage(coverageID="...", productID="...")
- FeatureCollection: service.getFeatureCollection(featureId="...")
- Geometry: service.getProcess("Geometry.Point").execute([lng, lat], "EPSG:4326")
"""


# 全局加载规则
OGE_CODEGEN_RULES = load_codegen_rules()


# ============================================================
# OGE 语法指南（让 LLM 理解 OGE 的核心语法和模式）
# ============================================================
OGE_SYNTAX_GUIDE = """
# OGE Python API 语法指南

## 1. 初始化模式
```python
import oge
oge.initialize()
service = oge.Service()
```
注意：OGE 使用 `service = oge.Service()` 而非 `oge.Service.initialize()`。

## 2. 数据加载

### 加载影像（对应 GEE 的 ee.Image / ee.ImageCollection）
```python
# 方式1：直接调用 service 方法
coverage = service.getCoverage(
    coverageID="LC08_L1TP_119038_20230104_20230111_02_T1",
    productID="LC08_C02_L1"
)

# 方式2：通过 getProcess 调用
coverage = service.getProcess("Service.getCoverage").execute(
    coverageID="xxx", productID="xxx"
)
```

### 加载矢量（对应 GEE 的 ee.FeatureCollection）
```python
# 方式1：加载已有矢量数据
featureCollection = service.getProcess("Service.getFeatureCollection").execute(
    featureCollectionID="xxx"
)

# 方式2：从 GeoJSON 构建
featureCollection = service.getProcess("FeatureCollection.loadFromGeojson").execute(
    {"type": "FeatureCollection", "features": [...]}
)

# 方式3：从 Feature 列表构建（最常用）
feature1 = service.getProcess("Feature.loadFromGeometry").execute(geometry1, props1)
feature2 = service.getProcess("Feature.loadFromGeometry").execute(geometry2, props2)
featureCollection = service.getProcess("FeatureCollection.loadFromFeatureList").execute(
    [feature1, feature2]
)
```

### 构造几何（对应 GEE 的 ee.Geometry.Point/Polygon 等）
```python
# 点
point = service.getProcess("Geometry.Point").execute([114.5, 31.3], "EPSG:4326")

# 多边形
polygon = service.getProcess("Geometry.Polygon").execute(
    [[[114,31],[114,30],[115,30],[114,31]]], "EPSG:4326", True
)

# 线
line = service.getProcess("Geometry.LineString").execute(
    [[35,10],[37,12],[40,15]], "EPSG:4326"
)
```

### 构造要素（对应 GEE 的 ee.Feature）
```python
feature = service.getProcess("Feature.loadFromGeometry").execute(
    geometry, {"prop1": 10, "prop2": "value"}
)
```

## 3. 数据处理（算子调用模式）

### 一元运算（如 abs, sqrt, not）
```python
result = service.getProcess("Coverage.abs").execute(input_coverage)
```

### 二元运算（如 add, subtract, multiply）
```python
result = service.getProcess("Coverage.add").execute(coverage1, coverage2)
```

### 波段操作（对应 GEE 的 select, bandNames）
```python
# 选择波段
result = service.getProcess("Coverage.band").execute(coverage, "B4")

# 多波段选择
result = service.getProcess("Coverage.select").execute(coverage, ["B4", "B3", "B2"])
```

### 过滤操作（对应 GEE 的 filter, filterDate）
```python
# 按日期过滤 FeatureCollection（注意第4个参数是时间字段名）
result = service.getProcess("FeatureCollection.filterDate").execute(
    featureCollection, "2021-07-01", "2021-08-01", "system:time_start"
)

# 按属性过滤
result = service.getProcess("FeatureCollection.filter").execute(
    featureCollection, property_name, value
)
```

### 裁剪操作（对应 GEE 的 clip）
```python
result = service.getProcess("Coverage.clip").execute(coverage, geometry)
```

### 统计操作（如 reduceRegion, sum, mean）
```python
# 区域统计
result = service.getProcess("Coverage.reduceRegion").execute(
    coverage, geometry, reducer
)
```

## 4. 可视化输出
```python
# 设置地图中心
oge.mapclient.centerMap(120.5, 32.0, 7)

# 获取地图显示
coverage.styles(vis_params).getMap("coverage_name")
feature.styles(["#FF0000"]).getMap("feature_name")
```

## 5. 关键差异说明
1. OGE 用 `service.getProcess("算子名").execute(...)` 调用大多数算子
2. Coverage/Feature/FeatureCollection 的方法在新版本也支持直接调用如 `coverage.band("B4")`
3. GEE 的 `ee.Filter` 在 OGE 中对应直接的 filter 算子
4. GEE 的 `ee.Date` 在 OGE 中用字符串表示（如 "2021-07-01"）
5. GEE 的 `display()` 在 OGE 中不需要，结果直接赋值给变量
6. GEE 的 `print()` 在 OGE 中用 `print()` 或直接查看变量

## 6. 变量类型对应
- GEE ee.Image → OGE Coverage
- GEE ee.ImageCollection → OGE Coverage（或多次 getCoverage）
- GEE ee.Feature → OGE Feature
- GEE ee.FeatureCollection → OGE FeatureCollection
- GEE ee.Geometry → OGE Geometry
- GEE ee.Number → OGE 原生 Python number
- GEE ee.String → OGE 原生 Python string
"""


class LLMService:
    """本地大模型服务

    提供 GEE→OGE 迁移相关的智能能力：
    - 语义匹配：GEE API → OGE API 的语义相似度推断
    - 代码分析：从 GEE 代码中提取变量类型、API 调用链
    - 代码生成：生成地道的 OGE 工作流代码
    - 缺失补全：为缺失的 GEE API 生成 Python 实现建议

    Attributes:
        base_url: LLM API 端点
        api_key: 认证密钥
        model: 模型名称
        max_tokens: 最大 token 数
        temperature: 生成温度
        timeout_seconds: 请求超时时间（秒）
        enable_thinking: 是否启用思考模式
    """

    def __init__(self):
        """初始化 LLM 服务"""
        self.base_url = LLM_CONFIG["base_url"]
        self.api_key = LLM_CONFIG["api_key"]
        self.model = LLM_CONFIG["model"]
        self.max_tokens = LLM_CONFIG["max_tokens"]
        self.temperature = LLM_CONFIG["temperature"]
        self.timeout_seconds = LLM_CONFIG.get("timeout_seconds", 420)
        self.enable_thinking = LLM_CONFIG.get("enable_thinking", False)
        self._available: Optional[bool] = None
        self._last_call_error: str = ''

    def is_available(self) -> bool:
        """检测 LLM 服务是否可用

        先尝试 HTTP 健康检查，再回退到简单的 LLM 调用测试

        Returns:
            bool: 可用返回 True
        """
        if self._available is not None:
            return self._available
        try:
            response = requests.get(
                self.base_url + '/models',
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                self._available = True
                return True
            response = self._call_llm("hi", max_tokens=5, max_retries=0)
            self._available = response is not None
        except Exception:
            self._available = False
        return self._available

    def reset_availability(self):
        """重置可用性缓存，下次检查会重新探测"""
        self._available = None

    def _call_llm(self, prompt: str, max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None, max_retries: int = 2) -> Optional[str]:
        """发起单次 LLM API 调用（带重试机制）

        通过 HTTP POST 请求调用本地部署的 deepseek-v4-flash-0731 模型，
        请求体中直接传入 enable_thinking 字段以控制是否启用思考模式。

        Args:
            prompt: 用户提示词
            max_tokens: 覆盖默认最大 token 数
            temperature: 覆盖默认温度
            max_retries: 最大重试次数

        Returns:
            Optional[str]: 模型回复文本，失败返回 None
        """
        import time

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "enable_thinking": self.enable_thinking,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout_seconds)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except requests.exceptions.HTTPError as e:
                self._last_call_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                if e.response.status_code in (502, 503, 504) and attempt < max_retries:
                    time.sleep(2 * (attempt + 1))
                    continue
                traceback.print_exc()
                return None
            except Exception as e:
                self._last_call_error = f"{type(e).__name__}: {str(e)}"
                if attempt < max_retries:
                    time.sleep(2 * (attempt + 1))
                    continue
                traceback.print_exc()
                return None
        return None

    # ================================================================
    # 核心能力 1: GEE → OGE 语义匹配
    # ================================================================

    def match_gee_to_oge(self, gee_api_name: str, gee_description: str = "",
                          candidate_oge_apis: Optional[List[str]] = None) -> Dict[str, Any]:
        """为 GEE API 推断最匹配的 OGE API

        当数据库无精确映射时，调用 LLM 进行语义推断

        Args:
            gee_api_name: GEE API 全名（如 ee.Image.abs）
            gee_description: GEE API 功能描述
            candidate_oge_apis: 候选 OGE API 列表（可选，提供以提升准确率）

        Returns:
            Dict: 匹配结果，包含:
                - matched: 是否找到匹配
                - oge_api: 匹配的 OGE API 名
                - confidence: 置信度 (0-1)
                - reasoning: 匹配理由
                - suggestion: 实现建议
        """
        candidates_text = ""
        if candidate_oge_apis:
            candidates_text = f"\n候选 OGE API 列表：\n" + "\n".join(
                f"  - {a}" for a in candidate_oge_apis
            )

        prompt = f"""你是一个 GIS 领域的 API 迁移专家。请为以下 GEE (Google Earth Engine) API 找到最匹配的 OGE API。

GEE API: {gee_api_name}
功能描述: {gee_description or '无'}
{candidates_text}

请以 JSON 格式返回：
{{
  "matched": true或false,
  "oge_api": "最匹配的 OGE API 名（如 Coverage.abs）",
  "confidence": 0到1的置信度,
  "reasoning": "匹配理由",
  "suggestion": "如果无直接匹配，给出 Python 实现建议"
}}

只返回 JSON，不要其他文字。"""

        response = self._call_llm(prompt)
        if response is None:
            return {
                "matched": False,
                "oge_api": None,
                "confidence": 0.0,
                "reasoning": "LLM 调用失败",
                "suggestion": None
            }

        # 解析 JSON
        return self._parse_llm_json(response, {
            "matched": False,
            "oge_api": None,
            "confidence": 0.0,
            "reasoning": "",
            "suggestion": None
        })

    # ================================================================
    # 核心能力 2: GEE 代码分析
    # ================================================================

    def analyze_gee_code(self, gee_code: str) -> Dict[str, Any]:
        """分析 GEE 代码，提取变量类型、API 调用链、任务目标、关键参数，并按语义拆分步骤

        本方法在原"代码目的总结"的基础上，同时完成步骤拆分工作：
        - 让 LLM 按语义功能将代码划分为有序步骤
        - 每个步骤包含描述和对应的代码片段（已删除注释）
        - 强制要求覆盖所有可执行代码行，不允许遗漏

        Args:
            gee_code: 原始 GEE JavaScript 代码

        Returns:
            Dict: 分析结果，包含:
                - task_goal: 任务目标
                - steps: 按语义拆分的步骤列表，每个步骤含 description 和 code
                - variable_types: 变量类型字典
                - api_calls: API 调用列表
                - dataflow: 数据流描述
                - suggestions: 迁移建议
                - key_params: 关键参数字典
        """
        prompt = f"""你是一个 GIS 代码分析专家。请分析以下 GEE (Google Earth Engine) JavaScript 代码，完成【任务目标总结】和【按语义拆分步骤】两项工作。

代码:
```javascript
{gee_code}
```

请以 JSON 格式返回分析结果：
{{
  "task_goal": "一句话描述这段代码的核心任务",
  "steps": [
    {{
      "description": "该步骤的简短描述（10-20字，如：加载并过滤影像集合）",
      "code": "该步骤对应的代码（删除所有注释，只保留可执行代码）"
    }}
  ],
  "variable_types": {{"变量名": "GEE 类全名"}},
  "api_calls": ["API 1", "API 2"],
  "dataflow": "数据流描述",
  "suggestions": ["迁移建议1", "迁移建议2"],
  "key_params": {{
    "datasets": ["数据源ID列表，如 LANDSAT/LC08/C02/T1_TOA"],
    "dates": ["日期列表，如 2021-01-01"],
    "coordinates": [{{"lng": 经度, "lat": 纬度}}],
    "properties": [{{"key": "属性名", "value": "属性值"}}],
    "filters": ["过滤条件描述"],
    "operations": ["主要操作方法列表"],
    "other": {{"其他关键参数": "值"}}
  }}
}}

【步骤拆分 - 重要要求，必须严格遵守】
1. steps 必须覆盖代码中的【所有可执行代码行】，绝对不能遗漏任何一行代码
2. 每个 step 的 code 字段中【删除所有注释】（// 开头的注释行），只保留可执行代码
3. 按语义功能划分步骤（如：数据加载、滤波、波段选择、指数计算、可视化、地图设置等）
4. 每个 step 的 description 要简短明确（10-20字）
5. 步骤之间保持原始代码的顺序，不要重排
6. 如果某行代码横跨多个功能，归到主要功能步骤即可，不要在多个步骤中重复
7. 不要合并不相关的代码到同一个步骤
8. 即使代码只有一行，也要作为一个步骤返回

【key_params 说明】
- key_params 中的字段是可选的，只有当代码中存在这些参数时才填写
- coordinates 用于存储代码中出现的地理坐标点
- properties 用于存储 Feature 的属性键值对
- filters 用于存储过滤条件
- other 用于存储其他重要参数（如阈值、波段名、指数名等）

只返回 JSON，不要其他文字。"""

        response = self._call_llm(prompt)
        if response is None:
            return {
                "task_goal": "",
                "steps": [],
                "variable_types": {},
                "api_calls": [],
                "dataflow": "",
                "suggestions": [],
                "key_params": {}
            }

        return self._parse_llm_json(response, {
            "task_goal": "",
            "steps": [],
            "variable_types": {},
            "api_calls": [],
            "dataflow": "",
            "suggestions": [],
            "key_params": {}
        })

    # ================================================================
    # 核心能力 3: OGE 代码生成
    # ================================================================

    @staticmethod
    def _extract_required_apis(gee_code: str) -> List[str]:
        """从 GEE 代码中提取 API 调用列表

        Args:
            gee_code: GEE JavaScript 代码

        Returns:
            List[str]: 识别到的 GEE API 名称列表
        """
        apis = set()

        # 匹配 ee.XXX.YYY 或 ee.XXX.YYY.ZZZ 形式
        # 如 ee.Image, ee.ImageCollection, ee.Feature, ee.FeatureCollection
        # 如 ee.Geometry.Point, ee.Geometry.LineString
        # 如 ee.Filter.date
        ee_pattern = r'ee\.([a-zA-Z]+(?:\.[a-zA-Z]+){0,2})'
        for match in re.finditer(ee_pattern, gee_code):
            api_name = 'ee.' + match.group(1)
            apis.add(api_name)

        # 匹配 Map.addLayer, Map.setCenter 等
        map_pattern = r'(Map\.\w+)'
        for match in re.finditer(map_pattern, gee_code):
            apis.add(match.group(1))

        # 匹配 Export.image.toAsset 等
        export_pattern = r'(Export\.\w+\.\w+)'
        for match in re.finditer(export_pattern, gee_code):
            apis.add(match.group(1))

        # 匹配 print 调用
        if re.search(r'\bprint\s*\(', gee_code):
            apis.add('print')

        return sorted(list(apis))

    def generate_oge_code(self, gee_code: str, mapping_context: str = "") -> Dict[str, Any]:
        """将 GEE 代码转换为 OGE 工作流代码

        使用 oge_step_codegen.txt 模板作为 prompt 指导 LLM 生成代码。
        针对整个 GEE 脚本生成完整的、只初始化一次的 OGE 工作流代码。

        Args:
            gee_code: 原始 GEE JavaScript 代码
            mapping_context: 映射上下文信息（包含 GEE→OGE 算子映射详情）

        Returns:
            Dict: 生成结果，包含:
                - oge_code: 生成的 OGE Python 代码（经后处理修正）
                - explanations: 各步骤的转换说明
                - warnings: 警告信息
                - feasibility: 可行性评估
        """
        # 提取 GEE 代码中的 API 调用
        required_apis = self._extract_required_apis(gee_code)
        required_apis_text = ', '.join(required_apis) if required_apis else '（未识别到 GEE API）'

        # 构建映射详情文本
        matched_details_text = mapping_context if mapping_context else '（无可用映射，LLM 自行推断）'

        # 检测缺失的 API
        missing_apis_text = '无'

        # 使用 oge_step_codegen.txt 模板填充变量
        # 注意：虽然模板是为单步骤设计的，但我们将整个脚本视为一个完整工作流
        template_prompt = OGE_CODEGEN_RULES.replace(
            '{file_name}', 'GEE_Script'
        ).replace(
            '{purpose}', '将 GEE JavaScript 代码转换为符合 OGE 规范的完整 Python 工作流代码（一个完整脚本，不是单步骤）'
        ).replace(
            '{workflow_notes}', '基于 GEE→OGE 算子映射表进行转换，覆盖数据读取、算子调用、可视化全流程。注意：这是一个完整脚本，不是单个步骤，因此只初始化一次。'
        ).replace(
            '{step_index}', '1'
        ).replace(
            '{step_summary}', '将整个 GEE 脚本作为一个完整工作流转换为 OGE Python 代码。这不是单个步骤，而是完整的脚本，必须一次性生成所有代码。'
        ).replace(
            '{required_apis_text}', required_apis_text
        ).replace(
            '{matched_oge_details}', matched_details_text
        ).replace(
            '{missing_required_apis_text}', missing_apis_text
        )

        # 构建增强的 prompt，明确约束 LLM 生成正确的代码
        full_prompt = f"""{template_prompt}

==================================================
【重要补充指令 - 请严格遵守】

1. 这是一个完整的 GEE 脚本，不是单个步骤。你必须：
   - 只生成一组初始化代码（import oge / oge.initialize() / service = oge.Service()），放在最前面
   - 后续所有操作（数据读取、算子调用、可视化）都紧跟在初始化之后，不需要重复初始化

2. 正确的代码结构应该是：
```python
import oge
oge.initialize()
service = oge.Service()

# 1. 数据读取（根据 GEE 代码中的具体变量名和值）
winterImage = service.getCoverage(
    coverageID="LC08_L1TP_119038_20230104_20230111_02_T1",
    productID="LC08_C02_L1"
)

# 2. 算子调用（使用 getProcess.execute 模式）
winterRed = service.getProcess("Coverage.selectBands").execute(winterImage, ["B4"])

# 3. 可视化（使用 .styles().getMap() 模式）
vis_params = {{
    "min": -1,
    "max": 1,
    "palette": ["blue", "lightblue", "green", "yellow", "red"]
}}
winterNdvi.styles(vis_params).getMap("Winter NDVI")

# 4. 地图中心设置（使用 oge.mapclient.centerMap() 模式）
oge.mapclient.centerMap(120.5, 32.0, 9)
```

3. 绝对不要犯以下错误：
   - ❌ 不要每个步骤都重复初始化（import oge / oge.initialize() / service = oge.Service()）
   - ❌ 不要用 service.getProcess("service.getCoverage").execute(...)，应该用 service.getCoverage(...)
   - ❌ 不要用 service.getProcess("getMap").execute(...)，应该用 .styles().getMap(...)
   - ❌ 不要用 service.getProcess("oge.mapclient.centerMap").execute(...)，应该用 oge.mapclient.centerMap(...)
   - ❌ 不要用 ... 省略参数，必须根据 GEE 代码中的实际变量名和值来填充
   - ❌ 不要虚构不存在的 OGE API

4. 下面是需要转换的完整 GEE 脚本：

```javascript
{gee_code}
```

5. 请生成完整可执行的 OGE Python 代码，严格按照上面的示例结构。"""

        response = self._call_llm(full_prompt)
        if response is None:
            return {
                "oge_code": "",
                "explanations": [],
                "warnings": ["LLM 调用失败，使用规则引擎回退"],
                "feasibility": "infeasible"
            }

        # 解析 JSON 响应
        result = self._parse_llm_json(response, {
            "oge_code": "",
            "feasible": True,
            "needs_missing_api_workaround": False,
            "missing_apis_blocking": [],
            "decision_note": "",
            "explanations": [],
            "warnings": []
        })

        # 调试日志
        print(f'[LLM CodeGen] Response length: {len(response)}')
        print(f'[LLM CodeGen] Response preview: {response[:200]}...')
        print(f'[LLM CodeGen] Parsed result keys: {list(result.keys())}')
        print(f'[LLM CodeGen] oge_code length: {len(result.get("oge_code", ""))}')

        # 处理 oge_code 可能被包裹在 markdown 代码块中的情况
        oge_code = result.get("oge_code", "")
        if oge_code:
            # 移除可能的 ```python ... ``` 包裹
            oge_code = re.sub(r'^```python\s*\n?', '', oge_code)
            oge_code = re.sub(r'\n?```\s*$', '', oge_code)
            oge_code = oge_code.strip()
            # 后处理修正（移除重复初始化、修正错误 API 等）
            oge_code = self._post_process_oge_code(oge_code)
            result["oge_code"] = oge_code

        # 转换 feasible 格式
        feasible = result.get("feasible", True)
        if feasible is True:
            result["feasibility"] = "full_feasible"
        elif feasible is False:
            result["feasibility"] = "infeasible"
        else:
            result["feasibility"] = str(feasible)

        return result

    def oge_to_gee(self, oge_code: str, description: str = "") -> Dict[str, Any]:
        """将 OGE 工作流代码反向转换为 GEE JavaScript 代码

        通过 LLM 分析 OGE Python 代码的语义和算子调用，
        映射回等效的 Google Earth Engine JavaScript 代码。

        Args:
            oge_code: OGE Python 工作流代码
            description: 任务描述（可选，帮助 LLM 理解意图）

        Returns:
            Dict: 转换结果，包含:
                - gee_code: 生成的 GEE JavaScript 代码
                - explanations: 转换说明列表
                - warnings: 警告信息列表
                - feasible: 是否可行
        """
        desc_part = f"\n任务描述：{description}" if description else ""

        prompt = f"""你是一个 GIS 代码转换专家，精通 OGE（Open Geo Engine）和 Google Earth Engine (GEE) 两种平台。
请将以下 OGE Python 代码转换为等效的 GEE JavaScript 代码。

{desc_part}

==================================================
【OGE 代码】

```python
{oge_code}
```

==================================================
【转换规则】

1. OGE API → GEE API 映射关系：
   - service.getCoverageCollection / service.getCoverage → ee.ImageCollection / ee.Image
   - Coverage.selectBands → .select()
   - Coverage.focalMean → .reduceNeighborhood(ee.Reducer.mean(), ...)
   - Coverage.focalMedian → .reduceNeighborhood(ee.Reducer.median(), ...)
   - Coverage.convolve → .convolve()
   - Coverage.terrHillshade → ee.Terrain.hillshade()
   - Coverage.reproject → .reproject()
   - Coverage.projection → .projection()
   - CoverageCollection.mosaic → .mosaic()
   - Kernel.prewitt → ee.Kernel.prewitt()
   - .styles().getMap() → Map.addLayer()
   - oge.mapclient.centerMap() → Map.setCenter()
   - productID 如 "ASTER_GDEM_DEM30" → 'NASA/ASTER_GED/...DEM' 等对应 GEE 数据集
   - productID 如 "LC08_L1T" / "LC08_C02_L1" → 'LANDSAT/LC08/C02/T1_TOA' 等

2. 代码结构要求：
   - 使用 GEE JavaScript 语法（var 声明、function 等）
   - 保留原始代码的变量命名和逻辑结构
   - 使用 GEE 的链式调用风格
   - Map.addLayer() 的可视化参数使用 GEE 格式

3. 输出格式：返回 JSON 对象，包含以下字段：
   - "gee_code": 生成的 GEE JavaScript 代码（纯代码，不要 markdown 包裹）
   - "explanations": 数组，每个元素是转换说明（如 "XXX 映射为 YYY"）
   - "warnings": 数组，无法直接映射的 API 或注意事项
   - "feasible": 是否完全可转换

```json
{{
    "gee_code": "// GEE JavaScript code here",
    "explanations": ["..."],
    "warnings": ["..."],
    "feasible": true
}}
```"""

        response = self._call_llm(prompt)
        if response is None:
            # 获取最后一次错误信息
            last_err = getattr(self, '_last_call_error', '未知错误')
            return {
                "gee_code": "",
                "explanations": [],
                "warnings": [f"LLM 调用失败: {last_err}"],
                "feasible": False
            }

        result = self._parse_llm_json(response, {
            "gee_code": "",
            "explanations": [],
            "warnings": [],
            "feasible": True
        })

        # 清理 markdown 包裹
        gee_code = result.get("gee_code", "")
        if gee_code:
            gee_code = re.sub(r'^```javascript\s*\n?', '', gee_code)
            gee_code = re.sub(r'^```js\s*\n?', '', gee_code)
            gee_code = re.sub(r'\n?```\s*$', '', gee_code)
            gee_code = gee_code.strip()
            result["gee_code"] = gee_code

        print(f'[LLM OGE→GEE] Response length: {len(response)}')
        print(f'[LLM OGE→GEE] gee_code length: {len(gee_code)}')

        return result

    def _post_process_oge_code(self, code: str) -> str:
        """后处理修正 OGE 代码中的常见 LLM 生成错误

        修正以下问题：
        1. 移除重复的初始化代码（只保留第一组）
        2. 初始化方式修正（按 oge_step_codegen.txt 规范使用 oge.Service()）
        3. 修正错误的 API 调用模式（如 service.getProcess("service.getCoverage")）
        4. 修正 mapclient 调用（不能用 getProcess 调用）
        5. 错误算子名修正
        6. 关键字参数 → 位置参数
        7. 清理代码结构

        Args:
            code: LLM 生成的原始 OGE 代码

        Returns:
            str: 修正后的 OGE 代码
        """
        # ========== 修正1: 移除重复的初始化代码 ==========
        code = self._remove_duplicate_initialization(code)

        # ========== 修正2: 初始化方式修正 ==========
        code = re.sub(
            r'\bservice\s*=\s*oge\.Service\.initialize\(\)',
            'service = oge.Service()',
            code
        )
        code = re.sub(
            r'oge\.Service\.initialize\(\)',
            'oge.Service()',
            code
        )

        # ========== 修正3: 修正错误的 API 调用模式 ==========
        # service.getProcess("service.getCoverage").execute(...) → service.getCoverage(...)
        # 这是 LLM 最常见的错误：把数据读取 API 当作 process 调用
        code = self._fix_wrong_process_calls(code)

        # ========== 修正4: 修正 mapclient 调用 ==========
        # service.getProcess("oge.mapclient.centerMap").execute(lon, lat, zoom) → oge.mapclient.centerMap(lon, lat, zoom)
        code = self._fix_mapclient_calls(code)

        # ========== 修正5: 错误算子名修正 ==========
        code = re.sub(
            r'getProcess\("FeatureCollection"\)\.execute\(',
            'getProcess("FeatureCollection.loadFromFeatureList").execute(',
            code
        )
        code = re.sub(
            r'getProcess\("getFeatureCollection"\)\.execute\(',
            'getProcess("FeatureCollection.loadFromFeatureList").execute(',
            code
        )
        code = re.sub(
            r'getProcess\("filterDate"\)\.execute\(',
            'getProcess("FeatureCollection.filterDate").execute(',
            code
        )
        code = re.sub(
            r'getProcess\("filter"\)\.execute\(',
            'getProcess("FeatureCollection.filter").execute(',
            code
        )

        # 修正3b-3d: oge.Xxx.Yyy(...) → service.getProcess("Xxx.Yyy").execute(...)
        code = re.sub(
            r'oge\.Feature\.(\w+)\(',
            r'service.getProcess("Feature.\1").execute(',
            code
        )
        code = re.sub(
            r'oge\.Coverage\.(\w+)\(',
            r'service.getProcess("Coverage.\1").execute(',
            code
        )
        code = re.sub(
            r'oge\.FeatureCollection\.(\w+)\(',
            r'service.getProcess("FeatureCollection.\1").execute(',
            code
        )

        # ========== 修正6: 关键字参数 → 位置参数 ==========
        kw_args = ['features', 'geometry', 'properties', 'featureCollection',
                   'start', 'end', 'input', 'output', 'reducer', 'geometry1', 'geometry2',
                   'collection', 'timeField', 'time_field']
        for kw in kw_args:
            code = re.sub(r'(execute\(\s*)' + kw + r'\s*=', r'\1', code)
            code = re.sub(r',\s*' + kw + r'\s*=', ', ', code)

        # ========== 修正7: 清理代码结构 ==========
        code = self._clean_code_structure(code)

        # ========== 修正8: 确保初始化代码存在 ==========
        code = self._ensure_initialization_code(code)

        return code

    @staticmethod
    def _remove_duplicate_initialization(code: str) -> str:
        """移除重复的初始化代码，只保留第一组完整的初始化块

        LLM 经常会为每个步骤重复生成:
        import oge
        oge.initialize()
        service = oge.Service()

        我们只保留第一组完整的初始化块，移除后续所有的初始化代码。

        Args:
            code: 可能包含重复初始化的代码

        Returns:
            str: 去重后的代码
        """
        lines = code.split('\n')
        
        # 初始化相关的行模式
        init_line_patterns = [
            r'^\s*import\s+oge\s*$',
            r'^\s*oge\.initialize\(\)\s*$',
            r'^\s*service\s*=\s*oge\.Service\(\)\s*$',
            r'^\s*service\s*=\s*oge\.Service\.initialize\(\)\s*$',
            r'^\s*#\s*Initialize.*$',
            r'^\s*#\s*初始化.*$',
        ]

        def is_init_line(line: str) -> bool:
            """判断一行是否是初始化相关的行"""
            return any(re.match(p, line) for p in init_line_patterns)

        # 策略：使用标记来识别初始化块
        # 当遇到第一行初始化代码时，标记为 in_first_init_block = True
        # 当遇到非初始化代码时，如果之前在初始化块中，则标记为 first_init_block_complete = True
        # 对于后续的初始化块（first_init_block_complete = True 后遇到的初始化代码），全部跳过
        
        result_lines = []
        first_init_block_complete = False  # 第一组初始化块是否已完整保留
        current_init_block_lines = []  # 当前正在处理的初始化块的行
        in_init_block = False  # 当前是否在初始化块中
        
        for line in lines:
            if is_init_line(line):
                if first_init_block_complete:
                    # 第一组初始化块已完成，跳过后续所有初始化行
                    continue
                else:
                    # 收集当前初始化块的行
                    in_init_block = True
                    current_init_block_lines.append(line)
            else:
                # 非初始化行
                if in_init_block:
                    # 之前在初始化块中，现在遇到非初始化行
                    # 说明第一组初始化块已经完整
                    result_lines.extend(current_init_block_lines)
                    current_init_block_lines = []
                    in_init_block = False
                    first_init_block_complete = True
                
                result_lines.append(line)
        
        # 处理文件末尾的初始化块（如果有的话）
        if in_init_block and not first_init_block_complete:
            # 只有一组初始化块，完整保留
            result_lines.extend(current_init_block_lines)
        
        return '\n'.join(result_lines)

    @staticmethod
    def _ensure_initialization_code(code: str) -> str:
        """确保代码中包含必要的初始化代码

        如果 LLM 生成的代码缺少初始化代码（import oge、oge.initialize()、service = oge.Service()），
        则在代码开头添加默认的初始化代码。

        Args:
            code: 需要检查的代码

        Returns:
            str: 确保包含初始化代码的代码
        """
        has_import = bool(re.search(r'import\s+oge', code))
        has_initialize = bool(re.search(r'oge\.initialize\(\)', code))
        has_service = bool(re.search(r'service\s*=\s*oge\.Service\(\)', code))

        if has_import and has_initialize and has_service:
            # 所有初始化代码都存在，无需修改
            return code

        # 需要添加初始化代码
        init_code = """import oge
oge.initialize()
service = oge.Service()

"""
        # 如果代码以 ```python 开头，需要在 ```python 后面插入
        if code.strip().startswith('```python'):
            # 移除 markdown 代码块标记，然后在开头添加初始化代码
            code = re.sub(r'^```python\s*\n?', '', code)
            code = re.sub(r'\n?```\s*$', '', code)
            code = init_code + code.strip()
            return code + '\n```'

        return init_code + code

    @staticmethod
    def _fix_wrong_process_calls(code: str) -> str:
        """修正错误的 process 调用模式

        LLM 常见错误模式:
        - service.getProcess("service.getCoverage").execute(coverage, productID)
          → service.getCoverage(coverageID="...", productID="...")
        - service.getProcess("Coverage.selectBands").execute(...)  → 保持不变（这个是正确的）

        注意: 只有当 getProcess 的参数以 "service." 开头时才需要修正

        Args:
            code: 可能包含错误 process 调用的代码

        Returns:
            str: 修正后的代码
        """
        # 模式1: 处理 coverageID 和 productID 是字面量字符串的情况
        # service.getProcess("service.getCoverage").execute("LC08_...", "LC08_C02_L1")
        # → service.getCoverage(coverageID="LC08_...", productID="LC08_C02_L1")
        pattern1 = r'service\.getProcess\("service\.getCoverage"\)\.execute\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)'
        code = re.sub(
            pattern1,
            r'service.getCoverage(coverageID="\1", productID="\2")',
            code
        )

        # 模式2: 处理变量名参数的情况
        # service.getProcess("service.getCoverage").execute(coverage, productID)
        # → service.getCoverage(coverageID=coverage, productID=productID)
        pattern2 = r'service\.getProcess\("service\.getCoverage"\)\.execute\(([^)]*)\)'

        def replace_coverage_call(match):
            args = match.group(1).strip()
            # 将参数转换为关键字参数格式
            # 原始参数可能是: coverage, coverageID, productID
            # 需要转换为: coverageID="xxx", productID="xxx"
            parts = [p.strip() for p in args.split(',') if p.strip()]
            if len(parts) >= 2:
                coverage_id = parts[0]
                product_id = parts[1]
                return f'service.getCoverage(coverageID={coverage_id}, productID={product_id})'
            elif len(parts) == 1:
                return f'service.getCoverage(coverageID={parts[0]}, productID="REPLACE_WITH_PRODUCT_ID")'
            else:
                return 'service.getCoverage(coverageID="REPLACE_WITH_COVERAGE_ID", productID="REPLACE_WITH_PRODUCT_ID")'

        code = re.sub(pattern2, replace_coverage_call, code)

        return code

    @staticmethod
    def _fix_mapclient_calls(code: str) -> str:
        """修正 mapclient 调用

        LLM 常见错误:
        - service.getProcess("oge.mapclient.centerMap").execute(lon, lat, zoom)
          → oge.mapclient.centerMap(lon, lat, zoom)
        - service.getProcess("getMap").execute(...)  → 移除这个错误调用

        Args:
            code: 可能包含错误 mapclient 调用的代码

        Returns:
            str: 修正后的代码
        """
        # 模式1: service.getProcess("oge.mapclient.centerMap").execute(lon, lat, zoom)
        # → oge.mapclient.centerMap(lon, lat, zoom)
        pattern1 = r'service\.getProcess\("oge\.mapclient\.centerMap"\)\.execute\(([^)]*)\)'

        def replace_center_map(match):
            args = match.group(1).strip()
            return f'oge.mapclient.centerMap({args})'

        code = re.sub(pattern1, replace_center_map, code)

        # 模式2: service.getProcess("getMap").execute(...) → 移除
        # getMap 应该通过 .styles().getMap() 调用，而不是 getProcess
        # 匹配多种变体
        code = re.sub(
            r'^\s*result\s*=\s*service\.getProcess\("getMap"\)\.execute\([^)]*\)\s*$',
            '',
            code,
            flags=re.MULTILINE
        )
        code = re.sub(
            r'^\s*service\.getProcess\("getMap"\)\.execute\([^)]*\)\s*$',
            '',
            code,
            flags=re.MULTILINE
        )
        # 也处理没有括号的情况（LLM 可能生成 ... 作为参数）
        code = re.sub(
            r'^\s*result\s*=\s*service\.getProcess\("getMap"\)\.execute\(\.\.\.\)\s*$',
            '',
            code,
            flags=re.MULTILINE
        )
        code = re.sub(
            r'^\s*service\.getProcess\("getMap"\)\.execute\(\.\.\.\)\s*$',
            '',
            code,
            flags=re.MULTILINE
        )

        return code

    @staticmethod
    def _clean_code_structure(code: str) -> str:
        """清理代码结构，移除多余的空行和注释

        Args:
            code: 需要清理的代码

        Returns:
            str: 清理后的代码
        """
        lines = code.split('\n')
        cleaned_lines = []

        for line in lines:
            # 移除完全为空的行（但保留代码块之间的适当间隔）
            if line.strip() == '':
                # 连续空行只保留一个
                if cleaned_lines and cleaned_lines[-1].strip() == '':
                    continue
                cleaned_lines.append('')
                continue

            # 移除明显的步骤标记注释
            if re.match(r'^\s*#\s*-+\s*Step\s+\d+.*$', line):
                continue
            if re.match(r'^\s*#\s*Step\s+\d+.*$', line):
                continue

            cleaned_lines.append(line)

        # 移除首尾空行
        result = '\n'.join(cleaned_lines)
        result = result.strip() + '\n'

        return result

    @staticmethod
    def _count_params_in_call(inner: str) -> int:
        """统计函数调用的参数数量（正确处理嵌套括号和引号）

        Args:
            inner: 括号内部文本（不含外层括号）

        Returns:
            int: 参数数量
        """
        depth = 0
        in_quote = False
        quote_char = None
        count = 1
        for ch in inner:
            if in_quote:
                if ch == quote_char:
                    in_quote = False
            else:
                if ch in ('"', "'"):
                    in_quote = True
                    quote_char = ch
                elif ch in ('(', '[', '{'):
                    depth += 1
                elif ch in (')', ']', '}'):
                    depth -= 1
                elif ch == ',' and depth == 0:
                    count += 1
        return count

    @staticmethod
    def _split_params(inner: str) -> List[str]:
        """按顶层逗号分割参数（正确处理嵌套括号和引号）

        Args:
            inner: 括号内部文本

        Returns:
            List[str]: 参数列表
        """
        parts = []
        current = ''
        depth = 0
        in_quote = False
        quote_char = None
        for ch in inner:
            if in_quote:
                current += ch
                if ch == quote_char:
                    in_quote = False
            else:
                if ch in ('"', "'"):
                    in_quote = True
                    quote_char = ch
                    current += ch
                elif ch in ('(', '[', '{'):
                    depth += 1
                    current += ch
                elif ch in (')', ']', '}'):
                    depth -= 1
                    current += ch
                elif ch == ',' and depth == 0:
                    parts.append(current.strip())
                    current = ''
                else:
                    current += ch
        if current.strip():
            parts.append(current.strip())
        return parts

    def _fix_filter_date_calls(self, code: str) -> str:
        """修正所有 filterDate 调用的参数数量

        Args:
            code: 源代码

        Returns:
            str: 修正后的代码
        """
        result = code
        pattern = re.compile(
            r'getProcess\("FeatureCollection\.filterDate"\)\.execute\(',
            re.DOTALL
        )
        offset_delta = 0

        for m in pattern.finditer(code):
            start = m.start() + offset_delta
            paren_pos = m.end() - 1 + offset_delta

            # 用栈找对应的结束括号
            depth = 0
            end_pos = paren_pos
            for i in range(paren_pos, len(result)):
                if result[i] == '(':
                    depth += 1
                elif result[i] == ')':
                    depth -= 1
                    if depth == 0:
                        end_pos = i + 1
                        break

            full = result[start:end_pos]
            inner = result[paren_pos + 1:end_pos - 1]

            # 统计参数
            param_count = self._count_params_in_call(inner)

            if param_count <= 3:
                # 缺少第4参数，追加
                fixed = full[:-1].rstrip() + ', "system:time_start")'
                result = result[:start] + fixed + result[end_pos:]
                offset_delta += len(fixed) - len(full)

            elif param_count >= 5:
                # 参数过多，检查是否有重复的 system:time_start
                parts = self._split_params(inner)
                if len(parts) >= 5 and parts[-1] in ('"system:time_start"', "'system:time_start'"):
                    # 去掉最后一个参数
                    new_inner = ', '.join(parts[:-1])
                    fixed = result[start:paren_pos + 1] + new_inner + ')'
                    result = result[:start] + fixed + result[end_pos:]
                    offset_delta += len(fixed) - len(full)

        return result

    def _fix_geometry_calls(self, code: str) -> str:
        """修正 oge.Geometry.Xxx() 直接调用为 service.getProcess 模式，并补 EPSG 参数

        Args:
            code: 源代码

        Returns:
            str: 修正后的代码
        """
        result = code
        # 匹配 oge.Geometry.XxxName(...) 的调用
        pattern = re.compile(r'oge\.Geometry\.(\w+)\(', re.DOTALL)
        offset_delta = 0

        for m in pattern.finditer(code):
            geo_type = m.group(1)
            start = m.start() + offset_delta
            paren_pos = m.end() - 1 + offset_delta

            # 找完整括号
            depth = 0
            end_pos = paren_pos
            for i in range(paren_pos, len(result)):
                if result[i] == '(':
                    depth += 1
                elif result[i] == ')':
                    depth -= 1
                    if depth == 0:
                        end_pos = i + 1
                        break

            full = result[start:end_pos]
            inner = result[paren_pos + 1:end_pos - 1]

            # 转换为 getProcess 模式
            new_prefix = f'service.getProcess("Geometry.{geo_type}").execute('

            # 检查是否已有 EPSG 参数
            param_count = self._count_params_in_call(inner)

            if param_count == 1:
                # 只有1个参数（坐标），需要追加 EPSG
                fixed = new_prefix + inner + ', "EPSG:4326")'
            elif param_count == 2:
                # 已有2个参数，可能已有 EPSG，保持原样
                fixed = new_prefix + inner + ')'
            else:
                fixed = new_prefix + inner + ')'

            result = result[:start] + fixed + result[end_pos:]
            offset_delta += len(fixed) - len(full)

        return result

    # ================================================================
    # 核心能力 4: 缺失 API 的 Python 实现建议
    # ================================================================

    def suggest_python_implementation(self, gee_api_name: str,
                                       gee_description: str = "") -> Dict[str, Any]:
        """为缺失的 GEE API 生成 Python 实现建议

        Args:
            gee_api_name: GEE API 全名
            gee_description: GEE API 功能描述

        Returns:
            Dict: 实现建议
        """
        prompt = f"""你是一个 GIS 算法专家。请为以下 GEE API 生成 Python 原生实现。

GEE API: {gee_api_name}
功能描述: {gee_description or '无'}

请以 JSON 格式返回：
{{
  "python_code": "完整的 Python 实现代码",
  "dependencies": ["依赖库1", "依赖库2"],
  "params_description": "参数说明",
  "return_description": "返回值说明",
  "example": "使用示例"
}}

只返回 JSON，不要其他文字。"""

        response = self._call_llm(prompt)
        if response is None:
            return {
                "python_code": "",
                "dependencies": [],
                "params_description": "",
                "return_description": "",
                "example": ""
            }

        return self._parse_llm_json(response, {
            "python_code": "",
            "dependencies": [],
            "params_description": "",
            "return_description": "",
            "example": ""
        })

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def _parse_llm_json(response_text: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """安全解析 LLM 返回的 JSON 文本

        处理 LLM 可能返回的 ```json``` 包裹、前导/后导文字等情况

        Args:
            response_text: LLM 返回文本
            default: 解析失败时的默认值

        Returns:
            Dict: 解析后的字典
        """
        text = response_text.strip()

        # 去除可能的 ```json``` 包裹
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        for start_char in ['{', '[']:
            start_idx = text.find(start_char)
            if start_idx >= 0:
                for end_char in ['}', ']']:
                    end_idx = text.rfind(end_char)
                    if end_idx > start_idx:
                        try:
                            return json.loads(text[start_idx:end_idx + 1])
                        except json.JSONDecodeError:
                            continue

        return default

    def analyze_case_metadata(self, gee_code: str, oge_code: str = "") -> Dict[str, Any]:
        """分析案例的 GEE 和 OGE 代码，自动提取案例元数据

        通过 LLM 分析代码意图，自动推断案例的名称、描述、标签、来源和难度等级。

        Args:
            gee_code: GEE JavaScript 源代码
            oge_code: OGE Python 转换代码（可选）

        Returns:
            Dict: 分析结果，包含:
                - name: 建议的案例名称
                - description: 案例描述
                - tags: 标签列表
                - source: 数据来源说明
                - difficulty: 难度等级 (easy/medium/hard)
                - task_goal: 代码任务目标
        """
        oge_part = f"\n\n对应的 OGE 代码：\n```python\n{oge_code}\n```" if oge_code else ""

        prompt = f"""你是一个 GIS 代码分析专家。请分析以下 GEE (Google Earth Engine) JavaScript 代码{oge_part}，
自动提取案例的元数据信息。

GEE 代码：
```javascript
{gee_code}
```

请以 JSON 格式返回分析结果：
{{
  "name": "建议的案例名称（简洁明了，10字以内）",
  "description": "案例功能描述（一句话说明该代码的核心用途，20-50字）",
  "tags": ["标签1", "标签2", "标签3"],
  "source": "使用的数据源/传感器名称",
  "difficulty": "难度等级(easy简单/medium中等/hard困难)",
  "task_goal": "代码的核心任务目标"
}}

要求：
1. name 要简洁有意义，能体现案例核心功能
2. tags 选择 2-5 个最相关的标签（如：NDVI、指数计算、可视化、影像加载、过滤等）
3. difficulty 判断标准：
   - easy: 单步操作，简单的加载/显示/基础计算
   - medium: 2-3 步操作，包含过滤、计算、可视化等
   - hard: 复杂的多步流程，包含时间序列、复杂计算、导出等
4. source 根据代码中使用的数据集判断（如 Landsat 8、Sentinel-2、MODIS 等）
5. 只返回 JSON，不要返回其他内容"""

        response = self._call_llm(prompt, max_tokens=500)

        default_result = {
            "name": "",
            "description": "",
            "tags": [],
            "source": "",
            "difficulty": "medium",
            "task_goal": ""
        }

        if not response:
            return default_result

        result = self._parse_llm_json(response, default_result)

        # 确保字段完整且类型正确
        result.setdefault("name", "")
        result.setdefault("description", "")
        result.setdefault("tags", [])
        result.setdefault("source", "")
        result.setdefault("difficulty", "medium")
        result.setdefault("task_goal", "")

        # 校验 difficulty
        if result["difficulty"] not in ("easy", "medium", "hard"):
            result["difficulty"] = "medium"

        # 确保 tags 是数组
        if not isinstance(result["tags"], list):
            result["tags"] = []

        return result


# ============================================================
# 全局 LLM 服务实例（懒加载）
# ============================================================
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取全局 LLM 服务实例

    Returns:
        LLMService: 单例实例
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


if __name__ == "__main__":
    # 测试 LLM 服务
    print("测试 LLM 服务连接...")
    svc = get_llm_service()
    available = svc.is_available()
    print(f"LLM 服务可用: {available}")

    if available:
        print("\n测试 API 匹配...")
        result = svc.match_gee_to_oge("ee.Image.abs", "计算影像的绝对值")
        print(f"匹配结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
