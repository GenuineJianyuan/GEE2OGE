"""
GEE (Google Earth Engine) 到 OGE (Open Geospatial Engine) API 映射转换模块。

本模块提供了 GEE API 到 OGE API 的映射关系查询和转换功能，
包括输入/输出数据类封装、Excel 映射表加载、gee.json 详细 API 信息集成，
以及 API 转换逻辑。

数据来源:
- gee_to_oge_matches.xlsx: GEE 到 OGE 的 API 映射表
- gee.json: GEE API 详细信息（参数、返回值、用法等）
"""

import json
import os
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict


# ============================================================
# 输入数据类 - GEE 端
# ============================================================

@dataclass
class GeeArgumentInfo:
    """GEE API 参数信息类

    Attributes:
        name: 参数名称
        type: 参数类型 (如 Image, Float, String 等)
        details: 参数详细说明
        order: 参数顺序
    """
    name: str
    type: str = ''
    details: str = ''
    order: int = 0

    def to_dict(self) -> dict:
        """将参数信息转换为字典"""
        return {
            'name': self.name,
            'type': self.type,
            'details': self.details,
            'order': self.order
        }


@dataclass
class GeeApiInfo:
    """GEE API 基础信息类 - 来自映射表

    Attributes:
        canonical_name: GEE 规范化 API 名称 (如 ee.Image.abs)
        api_names: GEE API 别名列表
        description_en: 英文描述
        description_zh: 中文描述
    """
    canonical_name: str
    api_names: List[str]
    description_en: str
    description_zh: str

    def has_alias(self) -> bool:
        """判断该 API 是否有多个别名

        Returns:
            bool: 如果有多个别名返回 True
        """
        return len(self.api_names) > 1

    def get_all_names(self) -> List[str]:
        """获取所有可能的 API 名称

        Returns:
            List[str]: 所有 API 名称的列表
        """
        return [self.canonical_name] + self.api_names


@dataclass
class GeeApiDetail:
    """GEE API 详细信息类 - 来自 gee.json

    Attributes:
        full_name: 完整 API 名称 (如 ee.Algorithms.CannyEdgeDetector)
        class_name: 类名 (如 ee.Algorithms)
        method_name: 方法名 (如 CannyEdgeDetector)
        description: 详细英文描述
        usage: 用法签名 (如 ee.Image.abs(image, threshold))
        returns: 返回值类型
        arguments: 参数列表
        url: API 文档链接
        organization_path: 组织结构路径
        raw_data: 原始 JSON 数据
    """
    full_name: str
    class_name: str = ''
    method_name: str = ''
    description: str = ''
    usage: str = ''
    returns: str = ''
    arguments: List[GeeArgumentInfo] = field(default_factory=list)
    url: str = ''
    organization_path: str = ''
    raw_data: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, json_data: dict) -> 'GeeApiDetail':
        """从 gee.json 的一条记录创建 GeeApiDetail 实例

        Args:
            json_data: gee.json 中的一条记录

        Returns:
            GeeApiDetail: 解析后的 API 详细信息
        """
        arguments = []
        for arg in json_data.get('arguments', []):
            arguments.append(GeeArgumentInfo(
                name=arg.get('name', ''),
                type=arg.get('type', ''),
                details=arg.get('details', ''),
                order=arg.get('order', 0)
            ))

        org_path = ''
        org = json_data.get('organization', {})
        if org:
            path_names = org.get('pathNames', [])
            org_path = ' / '.join(path_names) if path_names else ''

        return cls(
            full_name=json_data.get('fullName', ''),
            class_name=json_data.get('className', ''),
            method_name=json_data.get('methodName', ''),
            description=json_data.get('description', ''),
            usage=json_data.get('usage', ''),
            returns=json_data.get('returns', ''),
            arguments=arguments,
            url=json_data.get('url', ''),
            organization_path=org_path,
            raw_data=json_data
        )

    def get_argument_names(self) -> List[str]:
        """获取所有参数名称列表

        Returns:
            List[str]: 参数名称列表
        """
        return [arg.name for arg in self.arguments]

    def get_required_arguments(self) -> List[GeeArgumentInfo]:
        """获取必需参数列表（根据 type 字段是否包含 'optional' 判断）

        Returns:
            List[GeeArgumentInfo]: 必需参数列表
        """
        return [arg for arg in self.arguments if 'optional' not in arg.type.lower()]

    def to_dict(self) -> dict:
        """将详细信息转换为字典

        Returns:
            dict: API 详细信息字典
        """
        return {
            'full_name': self.full_name,
            'class_name': self.class_name,
            'method_name': self.method_name,
            'description': self.description,
            'usage': self.usage,
            'returns': self.returns,
            'arguments': [arg.to_dict() for arg in self.arguments],
            'argument_names': self.get_argument_names(),
            'required_arguments': [arg.to_dict() for arg in self.get_required_arguments()],
            'url': self.url,
            'organization_path': self.organization_path
        }


# ============================================================
# 输出数据类 - OGE 端
# ============================================================

@dataclass
class OgeApiInfo:
    """OGE API 信息类 - 封装 OGE 端的 API 详细信息

    Attributes:
        module: OGE 模块名 (如 Coverage, Feature, Geometry 等)
        method: OGE 方法名 (如 abs, buffer, Point 等)
        full_name: 完整的 OGE API 名称 (如 Coverage.abs)
    """
    module: str
    method: str
    full_name: str

    @classmethod
    def from_full_name(cls, full_name: str) -> 'OgeApiInfo':
        """从完整名称解析创建 OgeApiInfo 实例

        Args:
            full_name: 完整的 OGE API 名称 (如 'Coverage.abs', 'oge.mapclient.centerMap')

        Returns:
            OgeApiInfo: 解析后的 OGE API 信息
        """
        parts = full_name.split('.')
        if len(parts) >= 2:
            module = '.'.join(parts[:-1])
            method = parts[-1]
        else:
            module = ''
            method = full_name
        return cls(module=module, method=method, full_name=full_name)


@dataclass
class OgeMappingResult:
    """OGE 映射结果类 - 封装 GEE 到 OGE 的映射结果

    Attributes:
        gee_api: GEE 端基础 API 信息
        oge_apis: 对应的 OGE API 列表 (可能一个 GEE API 对应多个 OGE API)
        matched: 是否已找到映射
        reason: 映射原因或备注
        gee_detail: GEE API 详细信息（来自 gee.json，可选）
    """
    gee_api: GeeApiInfo
    oge_apis: List[OgeApiInfo] = field(default_factory=list)
    matched: bool = False
    reason: str = ''
    gee_detail: Optional[GeeApiDetail] = None

    def get_oge_full_names(self) -> List[str]:
        """获取所有 OGE API 的完整名称列表

        Returns:
            List[str]: OGE API 完整名称列表
        """
        return [api.full_name for api in self.oge_apis]

    def has_detail(self) -> bool:
        """判断是否包含 GEE API 详细信息

        Returns:
            bool: 如果有详细信息返回 True
        """
        return self.gee_detail is not None

    def to_dict(self, include_detail: bool = True) -> dict:
        """将映射结果转换为字典

        Args:
            include_detail: 是否包含 GEE 详细信息

        Returns:
            dict: 映射结果的字典表示
        """
        result = {
            'gee_canonical_name': self.gee_api.canonical_name,
            'gee_api_names': self.gee_api.api_names,
            'gee_description_en': self.gee_api.description_en,
            'gee_description_zh': self.gee_api.description_zh,
            'matched': self.matched,
            'oge_apis': self.get_oge_full_names(),
            'reason': self.reason
        }

        if include_detail and self.gee_detail:
            result['gee_detail'] = self.gee_detail.to_dict()

        return result


# ============================================================
# Excel 解析工具
# ============================================================

class ExcelParser:
    """Excel 文件解析器 - 使用 Python 标准库解析 xlsx 文件

    xlsx 文件本质是 zip 压缩包 + XML 文件格式，
    本类直接解析 XML 内容，无需第三方库依赖。
    """

    # xlsx 命名空间
    NS = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

    @staticmethod
    def parse_xlsx(xlsx_path: str) -> List[Dict[str, str]]:
        """解析 xlsx 文件并返回行数据列表

        Args:
            xlsx_path: xlsx 文件路径

        Returns:
            List[Dict[str, str]]: 每行为一个字典的列表
            字典键为列名（id, gee_canonical_api_name 等），值为单元格内容

        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: 文件格式不正确时抛出
        """
        if not os.path.exists(xlsx_path):
            raise FileNotFoundError(f"Excel 文件不存在: {xlsx_path}")

        if not xlsx_path.endswith('.xlsx'):
            raise ValueError(f"不支持的文件格式，需要 .xlsx 文件: {xlsx_path}")

        # 解析共享字符串
        strings = ExcelParser._parse_shared_strings(xlsx_path)

        # 解析工作表数据
        rows_data = ExcelParser._parse_sheet_data(xlsx_path, strings)

        return rows_data

    @staticmethod
    def _parse_shared_strings(xlsx_path: str) -> List[str]:
        """解析 xlsx 文件中的共享字符串表

        Args:
            xlsx_path: xlsx 文件路径

        Returns:
            List[str]: 共享字符串列表，索引对应单元格引用
        """
        with zipfile.ZipFile(xlsx_path, 'r') as z:
            with z.open('xl/sharedStrings.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                strings = []
                for si in root.findall('.//main:t', ExcelParser.NS):
                    strings.append(si.text or '')
                return strings

    @staticmethod
    def _parse_sheet_data(xlsx_path: str, strings: List[str]) -> List[Dict[str, str]]:
        """解析工作表数据

        Args:
            xlsx_path: xlsx 文件路径
            strings: 共享字符串列表

        Returns:
            List[Dict[str, str]]: 行数据列表
        """
        with zipfile.ZipFile(xlsx_path, 'r') as z:
            with z.open('xl/worksheets/sheet1.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()

                rows = root.findall('.//main:row', ExcelParser.NS)
                headers = []
                all_data = []

                for i, row in enumerate(rows):
                    cells = row.findall('main:c', ExcelParser.NS)
                    row_data = {}

                    for cell in cells:
                        cell_ref = cell.get('r')
                        col = ''.join(filter(str.isalpha, cell_ref))
                        cell_type = cell.get('t')
                        value_elem = cell.find('main:v', ExcelParser.NS)

                        if value_elem is not None:
                            if cell_type == 's':
                                idx = int(value_elem.text)
                                row_data[col] = strings[idx]
                            else:
                                row_data[col] = value_elem.text

                    if i == 0:
                        # 第一行为表头
                        headers = [row_data.get(chr(65 + j), '') for j in range(8)]
                    else:
                        # 数据行
                        record = {}
                        for j, h in enumerate(headers):
                            col_letter = chr(65 + j)
                            record[h] = row_data.get(col_letter, '')
                        all_data.append(record)

                return all_data


# ============================================================
# GEE JSON 解析工具
# ============================================================

class GeeJsonParser:
    """gee.json 文件解析器 - 加载 GEE API 详细信息

    从 gee.json 文件中提取 GEE API 的详细信息，
    包括参数、返回值、用法签名等。
    """

    @staticmethod
    def parse_gee_json(json_path: str) -> Dict[str, GeeApiDetail]:
        """解析 gee.json 文件

        Args:
            json_path: gee.json 文件路径

        Returns:
            Dict[str, GeeApiDetail]: 以 fullName 为键的 API 详细信息字典

        Raises:
            FileNotFoundError: 文件不存在时抛出
            ValueError: JSON 格式不正确时抛出
        """
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON 文件不存在: {json_path}")

        if not json_path.endswith('.json'):
            raise ValueError(f"不支持的文件格式，需要 .json 文件: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("gee.json 格式错误，应为 JSON 数组")

        result = {}
        for item in data:
            full_name = item.get('fullName', '')
            if full_name:
                result[full_name] = GeeApiDetail.from_json(item)

        return result


# ============================================================
# GEE 到 OGE 转换器
# ============================================================

class GeeToOgeConverter:
    """GEE 到 OGE API 转换器

    提供 GEE API 到 OGE API 的映射查询和转换功能。
    支持从 Excel 映射表加载数据、从 gee.json 加载详细 API 信息，
    以及按关键字、API 名称等进行查询。

    Attributes:
        mappings: 映射关系字典，键为 GEE canonical API 名称
        _api_name_index: API 名称倒排索引，用于快速查找
        gee_details: GEE API 详细信息字典（来自 gee.json）
    """

    def __init__(self, xlsx_path: Optional[str] = None, gee_json_path: Optional[str] = None):
        """初始化转换器

        Args:
            xlsx_path: Excel 映射表文件路径，如果提供则自动加载
            gee_json_path: gee.json 详细 API 信息文件路径，如果提供则自动加载
        """
        self.mappings: Dict[str, OgeMappingResult] = {}
        self._api_name_index: Dict[str, str] = {}  # 别名 -> canonical name
        self.gee_details: Dict[str, GeeApiDetail] = {}  # fullName -> GeeApiDetail

        if gee_json_path:
            self.load_gee_json(gee_json_path)

        if xlsx_path:
            self.load_from_xlsx(xlsx_path)

    def load_from_xlsx(self, xlsx_path: str) -> int:
        """从 Excel 文件加载映射关系

        Args:
            xlsx_path: Excel 映射表文件路径

        Returns:
            int: 加载的映射条目数量
        """
        raw_data = ExcelParser.parse_xlsx(xlsx_path)
        return self.load_from_raw_data(raw_data)

    def load_gee_json(self, gee_json_path: str) -> int:
        """从 gee.json 文件加载 GEE API 详细信息

        Args:
            gee_json_path: gee.json 文件路径

        Returns:
            int: 加载的 API 详细信息条目数量
        """
        self.gee_details = GeeJsonParser.parse_gee_json(gee_json_path)
        return len(self.gee_details)

    def load_from_raw_data(self, raw_data: List[Dict[str, str]]) -> int:
        """从原始数据列表加载映射关系

        Args:
            raw_data: 原始数据列表，每项为一个字典

        Returns:
            int: 加载的映射条目数量
        """
        count = 0
        for row in raw_data:
            canonical_name = row.get('gee_canonical_api_name', '').strip()
            if not canonical_name:
                continue

            # 解析 GEE API 基础信息
            api_names_raw = row.get('gee_api_name', canonical_name)
            api_names = [n.strip() for n in api_names_raw.split('|') if n.strip()]
            if not api_names:
                api_names = [canonical_name]

            gee_api = GeeApiInfo(
                canonical_name=canonical_name,
                api_names=api_names,
                description_en=row.get('gee_description_en', ''),
                description_zh=row.get('gee_description_zh', '')
            )

            # 解析 OGE 映射
            matched = row.get('matched', '0').strip() == '1'
            oge_name_raw = row.get('oge_name', '').strip()
            reason = row.get('reason', '').strip()

            # 解析 OGE API 列表（用 ; 分隔多个映射）
            oge_apis = []
            if matched and oge_name_raw:
                oge_names = [n.strip() for n in oge_name_raw.split(';') if n.strip()]
                for name in oge_names:
                    oge_apis.append(OgeApiInfo.from_full_name(name))

            # 尝试从 gee.json 中获取详细信息
            gee_detail = self._find_gee_detail(canonical_name, api_names)

            mapping = OgeMappingResult(
                gee_api=gee_api,
                oge_apis=oge_apis,
                matched=matched,
                reason=reason,
                gee_detail=gee_detail
            )

            # 建立主索引
            self.mappings[canonical_name] = mapping

            # 建立别名索引
            for alias in api_names:
                if alias not in self._api_name_index:
                    self._api_name_index[alias] = canonical_name

            count += 1

        return count

    def _find_gee_detail(self, canonical_name: str, api_names: List[str]) -> Optional[GeeApiDetail]:
        """在 gee_details 中查找匹配的 API 详细信息

        优先使用 canonical_name 精确匹配，然后尝试别名匹配。

        Args:
            canonical_name: GEE 规范化 API 名称
            api_names: GEE API 别名列表

        Returns:
            Optional[GeeApiDetail]: 匹配的详细信息，未找到返回 None
        """
        # 精确匹配 canonical name
        if canonical_name in self.gee_details:
            return self.gee_details[canonical_name]

        # 尝试别名匹配
        for name in api_names:
            if name in self.gee_details:
                return self.gee_details[name]

        # 尝试模糊匹配：检查 canonical_name 是否是某个 fullName 的子串
        for full_name, detail in self.gee_details.items():
            if canonical_name.lower() == full_name.lower():
                return detail
            # 对于不带 ee 前缀的名称（如 Map.addLayer），尝试添加 ee. 前缀
            if canonical_name.startswith('Map.') and f'ee.{canonical_name}' in self.gee_details:
                return self.gee_details[f'ee.{canonical_name}']

        return None

    def enrich_with_gee_json(self, gee_json_path: str) -> int:
        """加载 gee.json 并补充现有映射的详细信息

        Args:
            gee_json_path: gee.json 文件路径

        Returns:
            int: 成功补充详细信息的映射数量
        """
        self.load_gee_json(gee_json_path)

        enriched_count = 0
        for canonical, mapping in self.mappings.items():
            if not mapping.has_detail():
                gee_detail = self._find_gee_detail(
                    mapping.gee_api.canonical_name,
                    mapping.gee_api.api_names
                )
                if gee_detail:
                    mapping.gee_detail = gee_detail
                    enriched_count += 1

        return enriched_count

    def convert(self, gee_api_name: str) -> Optional[OgeMappingResult]:
        """将 GEE API 名称转换为 OGE 映射结果

        Args:
            gee_api_name: GEE API 名称（支持 canonical name 或别名）

        Returns:
            Optional[OgeMappingResult]: 映射结果，未找到返回 None
        """
        # 先尝试直接匹配 canonical name
        if gee_api_name in self.mappings:
            return self.mappings[gee_api_name]

        # 通过别名索引查找
        canonical = self._api_name_index.get(gee_api_name)
        if canonical and canonical in self.mappings:
            return self.mappings[canonical]

        return None

    def batch_convert(self, gee_api_names: List[str]) -> List[OgeMappingResult]:
        """批量转换 GEE API 名称

        Args:
            gee_api_names: GEE API 名称列表

        Returns:
            List[OgeMappingResult]: 映射结果列表，未找到的会创建空结果
        """
        results = []
        for name in gee_api_names:
            result = self.convert(name)
            if result:
                results.append(result)
            else:
                # 创建未找到的结果
                results.append(OgeMappingResult(
                    gee_api=GeeApiInfo(
                        canonical_name=name,
                        api_names=[name],
                        description_en='',
                        description_zh=''
                    ),
                    matched=False,
                    reason='未在映射表中找到'
                ))
        return results

    def search_by_keyword(self, keyword: str, search_in_detail: bool = True) -> List[OgeMappingResult]:
        """按关键字搜索映射关系

        在 GEE API 名称、描述、以及详细信息中搜索包含关键字的条目。

        Args:
            keyword: 搜索关键字（不区分大小写）
            search_in_detail: 是否也在详细信息中搜索

        Returns:
            List[OgeMappingResult]: 匹配的映射结果列表
        """
        keyword_lower = keyword.lower()
        results = []

        for canonical, mapping in self.mappings.items():
            gee_api = mapping.gee_api

            # 在 canonical name 中搜索
            if keyword_lower in canonical.lower():
                results.append(mapping)
                continue

            # 在别名中搜索
            if any(keyword_lower in n.lower() for n in gee_api.api_names):
                results.append(mapping)
                continue

            # 在描述中搜索
            if (keyword_lower in gee_api.description_en.lower() or
                    keyword_lower in gee_api.description_zh.lower()):
                results.append(mapping)
                continue

            # 在详细信息中搜索
            if search_in_detail and mapping.has_detail():
                detail = mapping.gee_detail
                if (keyword_lower in detail.description.lower() or
                        keyword_lower in detail.usage.lower() or
                        keyword_lower in detail.returns.lower() or
                        any(keyword_lower in arg.name.lower() for arg in detail.arguments)):
                    results.append(mapping)
                    continue

        return results

    def search_by_argument(self, argument_name: str) -> List[OgeMappingResult]:
        """按参数名搜索使用该参数的 GEE API

        Args:
            argument_name: 参数名（不区分大小写）

        Returns:
            List[OgeMappingResult]: 包含该参数的映射结果列表
        """
        arg_lower = argument_name.lower()
        results = []

        for mapping in self.mappings.values():
            if mapping.has_detail():
                detail = mapping.gee_detail
                if any(arg_lower in arg.name.lower() for arg in detail.arguments):
                    results.append(mapping)

        return results

    def get_api_detail(self, gee_api_name: str) -> Optional[GeeApiDetail]:
        """获取指定 GEE API 的详细信息

        Args:
            gee_api_name: GEE API 名称

        Returns:
            Optional[GeeApiDetail]: API 详细信息，未找到返回 None
        """
        mapping = self.convert(gee_api_name)
        if mapping and mapping.has_detail():
            return mapping.gee_detail
        return None

    def get_all_matched(self) -> List[OgeMappingResult]:
        """获取所有已匹配的映射条目

        Returns:
            List[OgeMappingResult]: 已匹配的映射结果列表
        """
        return [m for m in self.mappings.values() if m.matched]

    def get_all_unmatched(self) -> List[OgeMappingResult]:
        """获取所有未匹配的映射条目

        Returns:
            List[OgeMappingResult]: 未匹配的映射结果列表
        """
        return [m for m in self.mappings.values() if not m.matched]

    def get_statistics(self) -> Dict[str, int]:
        """获取映射统计信息

        Returns:
            Dict[str, int]: 包含 total, matched, unmatched, with_detail 的统计字典
        """
        total = len(self.mappings)
        matched = len(self.get_all_matched())
        unmatched = total - matched
        with_detail = sum(1 for m in self.mappings.values() if m.has_detail())
        return {
            'total': total,
            'matched': matched,
            'unmatched': unmatched,
            'with_detail': with_detail
        }

    def get_oge_modules(self) -> Dict[str, List[str]]:
        """获取所有 OGE 模块及其对应的 API 方法

        Returns:
            Dict[str, List[str]]: 模块名到方法名列表的映射
        """
        modules: Dict[str, List[str]] = {}
        for mapping in self.get_all_matched():
            for oge_api in mapping.oge_apis:
                module = oge_api.module
                if module not in modules:
                    modules[module] = []
                if oge_api.method not in modules[module]:
                    modules[module].append(oge_api.method)
        return modules

    def get_arguments_mapping(self) -> Dict[str, List[Dict]]:
        """获取所有已匹配 API 的参数映射信息

        Returns:
            Dict[str, List[Dict]]: GEE API 名称到参数列表的映射
        """
        result = {}
        for canonical, mapping in self.mappings.items():
            if mapping.has_detail() and mapping.gee_detail.arguments:
                result[canonical] = [arg.to_dict() for arg in mapping.gee_detail.arguments]
        return result

    def export_to_json(self, output_path: str, matched_only: bool = True,
                       include_detail: bool = True) -> None:
        """将映射结果导出为 JSON 文件

        Args:
            output_path: 输出 JSON 文件路径
            matched_only: 是否只导出已匹配的条目
            include_detail: 是否包含 GEE 详细信息
        """
        if matched_only:
            mappings = self.get_all_matched()
        else:
            mappings = list(self.mappings.values())

        output_data = [m.to_dict(include_detail=include_detail) for m in mappings]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    def list_all_apis(self, show_unmatched: bool = False) -> str:
        """列出所有 API 映射信息

        Args:
            show_unmatched: 是否显示未匹配的条目

        Returns:
            str: 格式化的 API 列表字符串
        """
        lines = []
        for canonical, mapping in sorted(self.mappings.items()):
            if not show_unmatched and not mapping.matched:
                continue

            status = '✓' if mapping.matched else '✗'
            oge_names = mapping.get_oge_full_names()
            oge_str = ', '.join(oge_names) if oge_names else 'N/A'
            detail_mark = ' [有详情]' if mapping.has_detail() else ''

            lines.append(f"[{status}] {canonical}{detail_mark} -> {oge_str}")
            if mapping.reason:
                lines.append(f"       备注: {mapping.reason}")

        return '\n'.join(lines)

    def get_python_function(self, gee_api_name: str) -> Optional[Callable]:
        """获取 GEE API 对应的 Python 实现函数（如果有的话）

        当 GEE API 在映射表中被标记为 Python 实现（如 Python Function、
        Python List、Python Dictionary 等），返回对应的 Python 函数。

        Args:
            gee_api_name: GEE API 名称

        Returns:
            Optional[Callable]: Python 实现函数，未找到返回 None

        Example:
            >>> converter = create_converter('gee_to_oge_matches.xlsx')
            >>> fn = converter.get_python_function('ee.Date.advance')
            >>> fn is not None
            True
            >>> fn('2023-01-15', 5, 'day')
            datetime.datetime(2023, 1, 20, ...)
        """
        try:
            from gee_python_functions import get_python_function as lookup
            return lookup(gee_api_name)
        except ImportError:
            return None

    def get_mapping_with_python(self, gee_api_name: str) -> Optional[Dict]:
        """获取 GEE API 的完整映射信息，包含 Python 实现函数（如果有的话）

        Args:
            gee_api_name: GEE API 名称

        Returns:
            Optional[Dict]: 包含映射信息和 Python 函数的字典
        """
        result = self.convert(gee_api_name)
        if result is None:
            return None

        info = result.to_dict()
        py_fn = self.get_python_function(gee_api_name)
        if py_fn is not None:
            info['python_function'] = {
                'name': py_fn.__name__,
                'module': py_fn.__module__,
                'doc': py_fn.__doc__,
            }
        return info

    def get_all_python_impl_mappings(self) -> List[Dict]:
        """获取所有映射为 Python 实现的条目

        Returns:
            List[Dict]: 包含 Python 实现的映射信息列表
        """
        python_keywords = ['Python', 'List Declaration', 'List Sequence', 'print']
        results = []
        for mapping in self.get_all_matched():
            oge_names = mapping.get_oge_full_names()
            is_python = any(
                any(kw.lower() in name.lower() for kw in python_keywords)
                for name in oge_names
            )
            if is_python:
                info = mapping.to_dict()
                py_fn = self.get_python_function(mapping.gee_api.canonical_name)
                if py_fn:
                    info['python_function'] = py_fn.__name__
                results.append(info)
        return results


# ============================================================
# 便捷函数
# ============================================================

def create_converter(xlsx_path: str, gee_json_path: Optional[str] = None) -> GeeToOgeConverter:
    """创建并加载 GEE 到 OGE 转换器

    Args:
        xlsx_path: Excel 映射表文件路径
        gee_json_path: gee.json 详细 API 信息文件路径（可选）

    Returns:
        GeeToOgeConverter: 初始化好的转换器实例
    """
    return GeeToOgeConverter(xlsx_path, gee_json_path)


def quick_convert(xlsx_path: str, gee_api_name: str,
                   gee_json_path: Optional[str] = None) -> Optional[OgeMappingResult]:
    """快速转换单个 GEE API

    Args:
        xlsx_path: Excel 映射表文件路径
        gee_api_name: GEE API 名称
        gee_json_path: gee.json 文件路径（可选）

    Returns:
        Optional[OgeMappingResult]: 映射结果
    """
    converter = GeeToOgeConverter(xlsx_path, gee_json_path)
    return converter.convert(gee_api_name)


def search_apis(xlsx_path: str, keyword: str,
                gee_json_path: Optional[str] = None) -> List[OgeMappingResult]:
    """快速搜索 GEE API

    Args:
        xlsx_path: Excel 映射表文件路径
        keyword: 搜索关键字
        gee_json_path: gee.json 文件路径（可选）

    Returns:
        List[OgeMappingResult]: 匹配的映射结果列表
    """
    converter = GeeToOgeConverter(xlsx_path, gee_json_path)
    return converter.search_by_keyword(keyword)