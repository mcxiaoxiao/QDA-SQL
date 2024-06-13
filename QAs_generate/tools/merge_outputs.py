import os
import json
import csv
from tools.evaluation import get_parse_sql_detail
import matplotlib.pyplot as plt

def merge_json_files(directory,csv_path,table_path):
    levels = ['easy', 'medium', 'hard', 'extra', 'unknow']
    hardness_origin = [0, 0, 0, 0, 0]
    hardness_generate = [0, 0, 0, 0, 0]
    
    # 确保目录存在
    if not os.path.exists('outputs/'+directory):
        print(f"Directory '{'outputs/'+directory}' does not exist.")
        return
    # 确保输出文件不存在，如果存在，则先删除
    if os.path.exists('outputs/'+directory+'_merged.json'):
        os.remove('outputs/'+directory+'_merged.json')
    # 获取目录下的所有文件
    files = [f for f in os.listdir('outputs/'+directory) if f.endswith('.json')]
    all_data = []
    goal_dict = get_goals_csv(csv_path)
    # print(goal_dict)
    # 遍历所有JSON文件
    turn_count = 0 
    for file_name in files:
        file_path = os.path.join(directory, file_name)
        with open('outputs/'+file_path, 'r') as file:
            data = json.load(file)
            for single_data in data:
                # print(single_data['database_id'],single_data['goal_id'])
                turns = single_data['turns']
                single_data['src_difficulty'] = goal_dict[single_data['goal_id']]['goal_sql_difficulty']
                single_data['spider_difficulty'] = goal_dict[single_data['goal_id']]['goal_sql_difficulty_spider_standard']
                single_data['goal_query'] = goal_dict[single_data['goal_id']]['goal_sql']
                # 将下标对应的ardness_origin列表中的值加1
                difficulty_index = levels.index(single_data['spider_difficulty'])
                hardness_origin[difficulty_index] += 1
                for turn in turns:
                    turn_count += 1
                    # print("存在turn")
                    parsed_turn = turn['query'].replace('\n',' ')
                    # print(parsed_turn)
                    sql,hardness = get_parse_sql_detail(parsed_turn,single_data['database_id'],table_path)
                    # print(hardness)
                    turn['spider_difficulty'] = hardness
                    # 获取难度级别在levels列表中的下标
                    difficulty_index = levels.index(hardness)
                    # 将下标对应的ardness_origin列表中的值加1
                    hardness_generate[difficulty_index] += 1
                    
        all_data.extend(data)
                
    with open('outputs/'+directory+'_merged.json', 'w',encoding='utf-8') as outfile:
        json.dump(all_data, outfile, indent=4)
    print(f"{len(all_data)} sets of dialogues\n{turn_count} turns QA \nMerged JSON data saved to '{'outputs/'+directory+'_merged.json'}'.")
    print(levels)
    print("generate hardness")
    print(hardness_generate)
    print("goal hardness")
    print(hardness_origin)

    # 创建柱形图
    plt.figure(figsize=(4, 3))
    bars = plt.bar(levels, hardness_generate)
    # 在每个柱子上方显示数值和百分比
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval,1), va='bottom')  # 显示数值
    plt.xlabel('hardness')
    plt.ylabel('num')
    plt.title('generate')
    # 显示图表
    plt.show()

    # 创建柱形图
    plt.figure(figsize=(4, 3))
    bars = plt.bar(levels, hardness_origin)
    # 在每个柱子上方显示数值和百分比
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval,1), va='bottom')  # 显示数值
    plt.xlabel('hardness')
    plt.ylabel('num')
    plt.title('origin')
    # 显示图表
    plt.show()
    
def get_goals_csv(csv_file_path ):
    result = {}
    # 打开CSV文件并逐行读取
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            id_value = row['id']
            goal_sql_difficulty = row['goal_sql_difficulty']
            goal_sql = row['goal_sql']
            goal_sql_difficulty_spider_standard = row['goal_sql_difficulty_spider_standard']
            if id_value in result:
                result[id_value]['goal_sql_difficulty'] = goal_sql_difficulty
                result[id_value]['goal_sql_difficulty_spider_standard'] = goal_sql_difficulty_spider_standard,
                result[id_value]['goal_sql'] = goal_sql
            else:
                result[id_value] = {
                    'goal_sql_difficulty': goal_sql_difficulty,
                    'goal_sql_difficulty_spider_standard': goal_sql_difficulty_spider_standard,
                    'goal_sql': goal_sql
                }
    return result