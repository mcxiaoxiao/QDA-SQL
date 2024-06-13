import os
import re
import argparse
import json
import pandas as pd
from tools.sql_execute import sqlite_execute as execute
from tqdm import tqdm
from tools.llm import ask_question_gemini as ask
from tools.generate_questions import *
import matplotlib.pyplot as plt
import sqlparse
from threading import Lock
import threading
import numpy as np
import sys

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='Run a script with multiple threads.To merge the jsons generated')
    parser.add_argument('--csv_file_path', type=str, required=True, help='Path to the goalsql CSV file.')
    parser.add_argument('--projectname', type=str, required=True, help='projectname to be merged.')
    parser.add_argument('--threads', type=int, required=True, help='Number of Threads.')
    parser.add_argument('--savename', type=str, required=True, help='name of the new json.')

    args = parser.parse_args()

    # 使用命令行参数
    csv_file_path = args.csv_file_path
    filename = args.projectname
    threads_count = args.threads
    savename = args.savename

df = pd.read_csv(csv_file_path)

#sql执行工具
def wiki5_sql_evoke(query,db_name):
    result, execution_time ,executable = execute("datasets/cosql_dataset/database/"+db_name+"/"+db_name+".sqlite", query)
    return result, execution_time ,executable

#llm回答提取出json
def parse_json(content):
    try:
        content = content.replace("\n","")
        content = content.strip()
        json_objects = re.findall(r'\{.*?\}', content)
        parsed_objects = []
        for json_object in json_objects:
            dict_object = json.loads(json.dumps(eval(json_object)))
            parsed_objects.append(dict_object)
        # print("parsed_objects"+str(parsed_objects))
        return parsed_objects
    except Exception as e:
        print(e)
        return []
def check_cannot(previous,question,dbname,evidence):
        max_retries = 5
        retry_count = 0
        QA = []
        
        while retry_count < max_retries:
            try:
                question_cn = critic_cannot(dbname,previous,question,evidence)
                # print(question_cn)
                answer1 = ask(question_cn)
                answer = parse_json(answer1)
                print(answer)
                if answer[0].get('answerable','')=='yes':
                    return False
                if answer[0].get('answerable','')=='no':
                    return True
                break
            except Exception as e:
                print(e)
                print(f"Check if indeed unanswerable, number of checks : {retry_count+1}")
                retry_count += 1
                
        return QA
def process_json(filename):
    parts = filename.split('_', 1)
    # parts[0]就是下划线之前的部分
    q_id = parts[0]
    dbname = parts[1][:-5]
    selected_row = df.loc[df['id'] == int(q_id)]
    evidence = ''
    # 如果存在符合条件的行，取其'evidence_of_goal'的值
    if not selected_row.empty:
        evidence = selected_row['evidence_of_goal'].values[0]


    if filename.endswith(".json"):
        with open(os.path.join(directory, filename), 'r') as f:
            data = json.load(f)

            filtered_data = []
            for index, value in enumerate(data[::2]):
                index = index * 2
                # print(index)
                # print(data[index],data[index + 1])
                type1 = data[index]['type']
                type2 = data[index+1]['type']
                valid_combinations = [
                    (type1 == 'INFER_SQL' and type2 == 'CONFIRM_SQL'),
                    (type1 == 'AMBIGUOUS' and type2 == 'CLARIFY'),
                    (type1 == 'INFORM_SQL' and type2 == 'CONFIRM_SQL'),
                    (type1 == 'CANNOT_ANSWER' and (type2 in ['SORRY','REQUEST MORE'])),
                    (type1 == 'IMPROPER' and (type2 in ['REQUEST_MORE', 'GREETING', 'SORRY', 'WELCOME', 'GOOD_BYE']))
                ]
                if any(valid_combinations) and index+1 < len(data) and data[index]['isuser'] == True and data[index+1]['isuser'] == False:
                    if data[index]['text']!="" and data[index+1]['text']!="":
                        # print( "QA:"+str(index)+"通过初步校验")
                        if data[index]['type']=="CANNOT_ANSWER":
                            print("Individual verification of whether the question is indeed unanswerable :"+data[index]['text'])
                            relation = data[index].get('relation','')
                            previous = str(filtered_data)
                            q = str(data[index]['text'])
                            ton = check_cannot(previous,q,dbname,evidence)
                            if ton:
                                print("Check for errors, keep CANNOT_ANSWER - SORRY")
                            else:
                                print("Check for errors, delete CANNOT_ANSWER - SORRY")
                                continue
    
                        filtered_data.append(data[index])
                        filtered_data.append(data[index+1])

            if len(filtered_data)<4: # 去除低于2轮的对话
                print("Insufficient number of rounds")
                return [],'','',''
 
            print("This group retains "+str(len(filtered_data))+"/"+str(len(data)))

            return filtered_data,q_id,dbname,evidence
        return [],'','',''
        
                

# 处理文件子列表的函数
def process_files_sublist(filenames_sublist, directory, all_arrays, total_QA, lock, progress):
    for filename in filenames_sublist:
        full_path = os.path.join(directory, filename)
        try:
            filtered_data, q_id, dbname, evidence = process_json(filename)
            with lock:
                if len(filtered_data) > 0:
                    total_QA[0] += len(filtered_data)
                    all_arrays.append({"goal_question": q_id, "evidence": str(evidence), "db_name": dbname, "turns": filtered_data})
                    progress.update(1)
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            
#评估+筛选文件夹内json
def read_json_files(directory):
    all_arrays = []
    total_QA = [0]  # 使用列表作为可变对象以便在函数内部修改
    filenames = [f for f in os.listdir(directory) if f.endswith(".json")]
    lock = threading.Lock()  # 用于同步访问all_arrays和total_QA
    threads = []
    progress = tqdm(total=len(filenames))

    # 分割文件列表
    def split(a, n):
        k, m = divmod(len(a), n)
        return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))
    filenames_sublists = list(split(filenames, threads_count))

    print("filter split:"+str(filenames_sublists))

    # 为每个子列表创建并启动一个线程
    for sublist in filenames_sublists:
        thread = threading.Thread(target=process_files_sublist, args=(sublist, directory, all_arrays, total_QA, lock, progress))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    progress.close()
    print("Total QA:", total_QA[0])
    return all_arrays


directory = "c_outputs/" + filename
all_arrays = read_json_files(directory)


with open('c_outputs/'+filename+'.json', 'w') as f:
    json.dump(all_arrays, f)



def optimize(turn):
    evidence = turn['evidence']
    db_name = turn['db_name']
    q_id = turn['goal_question']
    turns = turn['turns']
    print("The current processing id:"+str(q_id))
    print("Filter by: sql correctness")
    to_remove = set()  # 用于记录需要被移除的元素的索引
    for i, turn in enumerate(turns):
        if "query" in turn:
            if i > 0:
                question = turns[i-1]["text"]
            else:
                question = ""

            # 执行SQL查询并返回结果、执行时间和可执行性
            result, execution_time, executable = wiki5_sql_evoke(turn['query'], db_name)

            # 如果result为空或executable为false，则直接加入移除队列
            if not result or not executable:
                to_remove.add(i)
                if i > 0:
                    to_remove.add(i-1)
                print("Remove invalid or non-executable SQL")
                continue  # 跳过当前循环的剩余部分
            turn['time'] = execution_time  # 为当前含有效query的元素添加执行时间字段

            previous = turns[:i]
            # 进行得分计算
            question_score_sql = score_sql(previous, result, question,turn['query'])
            score_ans = ask(question_score_sql)
            score_json = parse_json(score_ans)
            try:
                if(len(score_json)>0):
                    score = float(score_json[0].get('score', ''))
                else:
                    score = 0
            except ValueError:
                score = 0
            print("This group sql scored:" + str(score))
            if score > 9:
                print("Retain this group sql")
                turn['score'] = score
            else:
                print("Remove this QA turn")
                to_remove.add(i)  # 标记当前元素（包含query的元素）为移除
                if i > 0:
                    to_remove.add(i-1)  # 标记前一个元素为移除
                if i > 2 and turns[i-3]["type"] == "AMBIGUOUS":  # 检查i-3元素的条件
                    print("Remove the associated AMBIGUOUS turn ")
                    # 标记i-3到i的元素为移除
                    to_remove.update({i-3, i-2, i-1, i})

    # 反向排序to_remove，以便从后往前移除元素，避免索引变化的问题
    for index in sorted(to_remove, reverse=True):
        del turns[index]
        
    print("Optimization: contextualization")
    question_include_knowledge = include_knowledge(evidence,db_name,turns)
    optimized1_output = ask(question_include_knowledge)
    turns = parse_json(optimized1_output)
    
    return {"goal_question":str(q_id),"evidence":str(evidence),"db_name":str(db_name),"turns":turns}


print("\033[92m {}\033[00m".format("Optimization step begins"))

try:
    with open(f'c_outputs/{filename}.json', "r") as f:
        data = json.load(f)

except FileNotFoundError:
    print(f"json file c_outputs/{filename}.json not found")
    exit()

# 检查优化结果文件是否存在，如果不存在，则创建一个新文件并初始化为一个空数组
optimized_file_path = f'c_outputs/{filename}_optimized.json'

try:
    with open(optimized_file_path, "r") as f:
        # 尝试读取文件以确认其存在
        pass
except FileNotFoundError:
    # 如果文件不存在，初始化一个空数组并保存
    with open(optimized_file_path, "w") as f:
        json.dump([], f, ensure_ascii=False, indent=4)
qa_sum = 0

def split_data(data, n_splits):
    k, m = divmod(len(data), n_splits)
    return (data[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n_splits))
# 线程工作函数
def process_data(sub_data, optimized_file_path, qa_sum_list, lock, pbar):
    for turn in sub_data:
        try:
            optimized_turn = optimize(turn)
        except Exception as e:
            print(f"Error optimize:{e}")
        if len(optimized_turn) > 0:
            with lock:
                # 读取当前文件内容
                with open(optimized_file_path, "r+") as f:
                    data = json.load(f)
                    data.append(optimized_turn)  # 将新的优化结果追加到数组中
                    f.seek(0)  # 重置文件指针到文件开头
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    f.truncate()  # 删除文件指针之后的所有内容
                qa_sum_list[0] += 1
            pbar.update(1)

# 修改主函数，以收集所有线程的结果并最后写入文件
def main(data,optimized_file_path):
    num_threads = threads_count
    qa_sum_list = [0]
    lock = Lock()

    # 初始化文件，确保其为一个空的JSON数组
    with open(optimized_file_path, "w") as f:
        json.dump([], f)

    splitted_data = split_data(data, num_threads)  
    print("split："+str(splitted_data))
    pbar = tqdm(total=len(data))
    
    threads = [threading.Thread(target=process_data, args=(chunk, optimized_file_path, qa_sum_list, lock, pbar)) for chunk in splitted_data]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    pbar.close()

    print("\033[92m {}\033[00m".format("Optimization steps complete, total Q&A turns :" + str(qa_sum_list[0])))


main(data[:], optimized_file_path)

import json

# 读取JSON文件
with open('c_outputs/'+filename+'_optimized.json', 'r') as file:
    data = json.load(file)

# 初始化总数
total_turns_length = 0

# 遍历数据，去除turns字段长度为0的元素，并累加turns长度
filtered_data = [item for item in data if len(item['turns']) > 0]
total_turns_length = sum(len(item['turns']) for item in filtered_data)

print(f"The total length of turns: {total_turns_length}")

# 将过滤后的数据保存回新的JSON文件
with open('c_outputs/'+filename+'_filtered.json', 'w') as outfile:
    json.dump(filtered_data, outfile, ensure_ascii=False, indent=4)

print("The filtered data has been saved to "+'c_outputs/'+filename+'_filtered.json')


# 所有json文件都在这个目录下
directory = 'c_outputs'

# 保存处理后的数据
output_file_path = savename

# 文件名列表
files = [
    filename+'_filtered.json'
]

# 初始化一个空列表用于存放所有数组的元素
all_elements = []

# 遍历文件列表，加载每个文件的内容并将其元素添加到all_elements列表中
for file_name in files:
    file_path = os.path.join(directory, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        # 加载JSON文件
        data = json.load(file)
        # 假设文件中的主体是一个数组
        if isinstance(data, list):
            all_elements.extend(data)
        else:
            print(f"Warning: {file_name} does not contain a list.")
print("The number of multi-round conversations before the final screening step is:"+str(len(all_elements)))


# sql_depth 函数，用于计算 SQL 查询的深度
def sql_depth(sql):
    def get_depth(node):
        if not isinstance(node, sqlparse.sql.TokenList):
            return 0
        else:
            return 1 + max((get_depth(child) for child in node), default=0)
    parsed = sqlparse.parse(sql)[0]
    depth = get_depth(parsed)
    return depth

# 假设 all_elements 已经是您要处理的数据列表

# 记录初始元素数量
initial_elements_count = len(all_elements)

# 用于记录筛选前后对话长度的列表
dialogue_lengths_before = []
dialogue_lengths_after = []

# 累加turns数组的长度
total_turns_length_before = 0
total_turns_length_after = 0

# 筛选前收集对话长度，并确保长度为偶数
for element in all_elements:
    turns = element.get('turns', [])
    # 如果turns长度不是偶数，则截取成偶数
    if len(turns) % 2 != 0:
        turns = turns[:-1]  # 移除最后一个元素
        element['turns'] = turns  # 更新元素中的turns数组
    dialogue_lengths_before.append(len(turns))
    total_turns_length_before += len(turns)

# 遍历all_elements列表的副本，以允许在遍历时修改原列表
for element in all_elements[:]:
    turns = element.get('turns', [])
    original_turns_length = len(turns)

    i = 0
    while i < len(turns) - 1:
        type1 = turns[i].get('type')
        type2 = turns[i + 1].get('type')
        sql = turns[i + 1].get('query','')
        if type2 != 'CONFIRM_SQL':
            sql = 'pass'
        valid_combinations = [
            (type1 == 'INFER_SQL' and type2 == 'CONFIRM_SQL'),
            (type1 == 'AMBIGUOUS' and type2 == 'CLARIFY'),
            (type1 == 'INFORM_SQL' and type2 == 'CONFIRM_SQL'),
            (type1 == 'CANNOT_ANSWER' and (type2 in ['SORRY', 'REQUEST_MORE'])),
            (type1 == 'IMPROPER' and (type2 in ['REQUEST_MORE', 'GREETING', 'SORRY', 'WELCOME', 'GOOD_BYE']))
        ]
       
            

        if not any(valid_combinations) or sql == '':
            
            if i > 1 and turns[i-2].get('type') == 'AMBIGUOUS':
                del turns[i-2:i+2]
                i -= 2
            else:
                del turns[i:i+2]
        else:
            i += 2
                
        

    # 如果turns最终长度为零，则删除整个元素
    if len(turns) == 0:
        all_elements.remove(element)
    else:
        dialogue_lengths_after.append(len(turns))  # 记录非零长度的对话
        total_turns_length_after += len(turns)

# 输出累加的turns数组长度
print(f"Total length of turns arrays before deletion: {total_turns_length_before}")
print(f"Total length of turns arrays after deletion: {total_turns_length_after}")

# 输出删除的元素数量
deleted_elements_count = initial_elements_count - len(all_elements)
print(f"Deleted {deleted_elements_count} elements with zero-length turns.")

with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(all_elements, output_file, ensure_ascii=False, indent=4)

print(f"Finished merging. The merged data has been saved to {output_file_path}")

# 绘制筛选前的长度分布
plt.hist(dialogue_lengths_before, bins=max(dialogue_lengths_before), edgecolor='black', alpha=0.3, label='Before Filtering')

# 绘制筛选后的长度分布
plt.hist(dialogue_lengths_after, bins=max(dialogue_lengths_after), edgecolor='red', alpha=0.3, label='After Filtering')

plt.title('Distribution of Dialogue Lengths Before and After Filtering')
plt.xlabel('Length of Dialogue')
plt.ylabel('Frequency')
plt.legend()
plt.show()


# 读取CSV文件并计算SQL深度分布
df['sql_depth'] = df['goal_sql'].apply(sql_depth)
original_depth_distribution = df['sql_depth'].value_counts().sort_index()

# 读取过滤后的JSON文件并计算SQL深度分布
def calculate_depth_from_json(file_path):
    depths = []
    with open(file_path, 'r') as file:
        data = json.load(file)
        for entry in data:
            for turn in entry['turns']:
                if 'query' in turn:
                    depth = sql_depth(turn['query'])
                    depths.append(depth)
    return pd.Series(depths).value_counts().sort_index()

filtered_depth_distribution = calculate_depth_from_json(output_file_path)

# 创建一个DataFrame来整合两个分布
combined_distribution = pd.DataFrame({
    'Original': original_depth_distribution,
    'Filtered': filtered_depth_distribution
}).fillna(0)  # 填充NaN值为0

# 绘制双色柱状图
combined_distribution.plot(kind='bar', figsize=(10, 6), color=['#7ABBDB', '#84BA42'])
plt.title('Comparison of SQL Depth Distribution')
plt.xlabel('Depth')
plt.ylabel('Frequency')
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle='--')

plt.show()

sys.exit()
