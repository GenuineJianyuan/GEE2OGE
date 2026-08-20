"""调试 API 识别"""
import sys
sys.path.insert(0, r'd:\docs\交投\文档\全球院工作\geeToOGE')
from case_study_pipeline import CaseStudyPipeline

code = """var winterImage = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_119038_20230104');
var winterRed = winterImage.select('B4');
var winterNir = winterImage.select('B5');
var winterNdviNumerator = winterNir.subtract(winterRed);
var winterNdviDenominator = winterNir.add(winterRed);
var winterNdvi = winterNdviNumerator.divide(winterNdviDenominator).rename('Winter_NDVI');
Map.addLayer(winterNdvi, vis, 'Winter NDVI');
"""

print("变量类型推断：")
var_types = CaseStudyPipeline._infer_variable_types(code)
for k, v in var_types.items():
    print(f"  {k}: {v}")

print("\nAPI 识别：")
apis = CaseStudyPipeline._extract_gee_apis(code)
for api in apis:
    print(f"  {api}")
