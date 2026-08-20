import json
import os
import sys


def filter_json_fields(input_path, output_path=None, keep_fields=None):
    """
    从 JSON 中提取每个条目的指定字段，生成新的 JSON 文件。

    参数:
        input_path: 原始 JSON 路径
        output_path: 输出 JSON 路径（若 None 则自动生成）
        keep_fields: 要保留的字段列表，如 ['case_id', 'gee']；若 None 则交互输入
    """
    # 读取原始 JSON
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 识别顶层结构：是否包含 'results' 列表？
    if isinstance(data, dict) and 'results' in data:
        items = data['results']
        root_is_dict = True
    elif isinstance(data, list):
        items = data
        root_is_dict = False
    else:
        # 单个对象
        items = [data]
        root_is_dict = False

    if not items:
        print("❌ 未找到任何数据条目。")
        return

    # 获取所有可用字段（以第一个条目为准）
    first = items[0]
    available = list(first.keys())
    print("📋 可用字段：")
    for idx, f in enumerate(available, 1):
        print(f"  {idx}. {f}")

    # 确定要保留的字段
    if keep_fields is None:
        # 交互输入，默认保留 case_id 和 gee
        default = "case_id,gee"
        user_input = input(f"\n请输入要保留的字段（逗号分隔，默认 '{default}'）：").strip()
        if not user_input:
            fields_to_keep = [x.strip() for x in default.split(',')]
        else:
            fields_to_keep = [x.strip() for x in user_input.split(',') if x.strip()]
    else:
        fields_to_keep = keep_fields

    # 检查字段是否都存在
    missing = [f for f in fields_to_keep if f not in available]
    if missing:
        print(f"⚠️ 警告：以下字段不存在：{missing}，将跳过这些字段。")
        fields_to_keep = [f for f in fields_to_keep if f in available]

    if not fields_to_keep:
        print("❌ 没有有效的字段可保留，退出。")
        return

    print(f"✅ 将保留字段：{fields_to_keep}")

    # 构建新的数据
    new_items = []
    for item in items:
        filtered = {k: item.get(k) for k in fields_to_keep}
        # 如果某个字段缺失，该键值对不会出现（或为 None，但用 get 会返回 None）
        # 为了保持一致性，我们保留所有指定的键（即使值为 None）
        new_items.append(filtered)

    # 构造新的整体结构
    if root_is_dict:
        new_data = data.copy()  # 复制其他顶层字段（如 total, converted 等）
        new_data['results'] = new_items
    else:
        new_data = new_items

    # 生成输出路径
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_filtered{ext}"
    else:
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入新 JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎯 新 JSON 已保存至：{output_path}")
    print(f"📊 共处理 {len(new_items)} 个条目，每个条目包含 {len(fields_to_keep)} 个字段。")


if __name__ == "__main__":
    # ===== 配置 =====
    input_json = r"D:\docs\交投\文档\全球院工作\geeToOGE\web\static\testdata\benchmark_with_dag_rebalanced_v4.json"
    # 可选：直接指定要保留的字段（若不指定则交互输入）
    # 例如：keep = ["case_id", "gee", "llm_gee_code"]
    # 如果命令行有参数，取第一个参数作为逗号分隔的字段列表
    if len(sys.argv) > 1:
        custom_fields = [x.strip() for x in sys.argv[1].split(',') if x.strip()]
    else:
        custom_fields = None

    filter_json_fields(input_json, keep_fields=custom_fields)