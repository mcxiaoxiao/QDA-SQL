import json
import os

# 读取cosql_dev.json文件
file_path = 'cosql_dev.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 遍历数据并修改type字段
for item in data:
    # 遍历每个turn
    for turn in item['turns']:
        # 检查是否有type字段且是数组格式
        if 'type' in turn and isinstance(turn['type'], list):
            # 获取type数组
            type_list = turn['type']
            # 检查是否包含INFORM_SQL或INFER_SQL
            if 'INFORM_SQL' in type_list or 'INFER_SQL' in type_list:
                turn['type'] = 'answerable'
            # 检查是否包含GOOD_BYE或THANK_YOU
            elif 'GOOD_BYE' in type_list or 'THANK_YOU' in type_list:
                turn['type'] = 'improper'
            # 检查是否包含AMBIGUOUS
            elif 'AMBIGUOUS' in type_list:
                turn['type'] = 'ambiguous'

# 将修改后的数据写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'已完成转换，文件已保存至 {file_path}')