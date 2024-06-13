import json
import csv


# 读取 JSON 文件
with open('datasets/cosql_dataset/cosql_all_info_dialogs.json', 'r', encoding='utf-8') as jsonfile:
   data = json.load(jsonfile)
    
# 创建CSV文件并写入数据
csv_file_path = 'goals_of_cosql_dev.csv'  # 请将文件路径替换为实际路径
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['id','goal_question_src_id', 'db_id', 'goal_question', 'evidence_of_goal', 'goal_sql','table_names', 'goal_sql_difficulty','goal_sql_difficulty_spider_standard']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # 遍历每个条目并写入CSV文件
    i = 0
    
    for entry in data.values():
        # print(entry)
        table_names_string = ",".join(entry["assistant_table_names"])
        i+=1
        writer.writerow({
            'id':i,
            'goal_question_src_id': entry["_id"],
            'db_id': entry["db_id"],
            'goal_question': entry["query_goal"],
            'evidence_of_goal': "",
            'goal_sql': entry["sql"],
            'table_names':table_names_string,
            'goal_sql_difficulty': "",
            'goal_sql_difficulty_spider_standard': ""
        })


print("Goal questions 数据已成功整理到CSV文件:", csv_file_path)
