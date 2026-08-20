import json
import os

# 文件路径
json_path = r"D:\docs\交投\文档\全球院工作\geeToOGE\web\static\testdata\scripts_ori\benchmark_convert_results.json"
output_dir = r"D:\docs\交投\文档\全球院工作\geeToOGE\web\static\testdata\scripts_ori"

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 读取 JSON
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取 results 列表
results = data.get('results', [])
if not results:
    print("未找到 results 字段或列表为空")
    exit()

# 遍历并保存
saved_count = 0
for item in results:
    case_id = item.get('case_id')
    code = item.get('llm_gee_code')

    if not case_id:
        print("警告：条目缺少 case_id，跳过")
        continue
    if code is None:
        print(f"警告：{case_id} 缺少 llm_gee_code，跳过")
        continue

    # 去除首尾空白（保留代码格式）
    code = code.strip()
    if not code:
        print(f"警告：{case_id} 的 llm_gee_code 为空，跳过")
        continue

    # 生成文件名，以 .js 结尾
    filename = f"{case_id}.js"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as out_f:
        out_f.write(code)

    saved_count += 1
    print(f"已保存: {filepath}")

print(f"\n完成！共保存 {saved_count} 个文件。")