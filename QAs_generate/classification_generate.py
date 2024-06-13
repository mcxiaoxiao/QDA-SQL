# from tools.llm import ask_question_gpt as ask
from tools.llm import ask_question_gemini as ask
import os
from tools.generate_questions import *
import csv
from tqdm import tqdm
import re
import argparse
import json
import random
import time
from tools.sql_execute import sqlite_execute as execute

#保存工具
def save_cp(goal_id,db_name,result,projectname):
    filename = 'c_outputs/'+projectname+'/'+str(goal_id)+'_' + db_name + '.json'
    
    if not os.path.exists('c_outputs/'+projectname):
        os.makedirs('c_outputs/'+projectname)

    # 如果文件存在，读取旧的结果
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            old_result = json.load(f)
    else:
        old_result = []
    
    # 将新的结果加入到旧的结果中
    result = old_result + result
    
    # 将结果保存回文件
    with open(filename, 'w') as f:
        json.dump(result, f)


#sql执行工具
def bird_sql_evoke(query,db_name):
    result, execution_time ,executable = execute("datasets/cosql_dataset/database/"+db_name+"/"+db_name+".sqlite", query)
    return result, execution_time ,executable

#llm回答提取出json
def parse_json(content):
    content = content.replace("\n","")
    content = content.strip()
    json_objects = re.findall(r'\{.*?\}', content)
    # print("json_objects")
    # print(json_objects)
    parsed_objects = []
    for json_object in json_objects:
        dict_object = json.loads(json.dumps(eval(json_object)))
        parsed_objects.append(dict_object)
        
    return parsed_objects
# Type 1: INFER_SQL-CONFIRM_SQL
def infer_confirm(database_id, utterance, goal_sql):
    question1 = get_infer(database_id, utterance, goal_sql)
    # print(question1)
    answer1 = ask(question1)
    # print(answer1)
    text_sqls = parse_json(answer1)

    qa_pair = []
    for dict_object in text_sqls:
        sql_value = dict_object.get('sql', '')
        result, execution_time ,executable = bird_sql_evoke(sql_value,database_id)
        if executable and result != []:
            # print(dict_object)
            print("SQL valid")
            question2 = get_infer_des(dict_object['text'], dict_object['sql'], database_id)
            answer2 = ask(question2)
            # print("answer2")
            answer2 = answer2.replace("\n","")
            # print(answer2)
            des = parse_json(answer2)
            # print("解析后的description")
            # print(des)
            # print(des[0]['description'])
            user_question = {"isuser": True, "text": dict_object['text'], "type": 'INFER_SQL'}
            system_response = {"isuser": False, "query": dict_object['sql'],"result":result, "text": des[0]['description'], "type": 'CONFIRM_SQL'}
            
            qa_pair.append(user_question)
            qa_pair.append(system_response)
        else:
            # print(dict_object)
            print("SQL invalid")

    return(qa_pair)
    
# Type 2: AMBIGUOUS-CLARIFY-(INFER_SQL/INFORM SQL可能存在NEGATE)-CONFIRM SQL
def ambiguous_clarify(database_id,utterance,goal_sql):
    question1 = get_ambiguous(database_id, utterance, goal_sql)
    # print(question1)
    answer1 = ask(question1)
    text_sqls = parse_json(answer1)
    # print(text_sqls)

    qa_pair = []
    for dict_object in text_sqls:
        # print("yhis")
        # print(dict_object)
        sql_value = dict_object.get('sqlquery', '')
        result, execution_time ,executable = bird_sql_evoke(sql_value,database_id)
        if executable and result != []:
            print("SQL valid")
            if(dict_object['type'] == 'INFER_SQL'):
                question2 = get_infer_des(dict_object['question'], dict_object['sqlquery'], database_id)
                answer2 = ask(question2)
                # print("answer2")
                # print(answer2)
                des = parse_json(answer2)
                # print("解析后的description")
                # print(des)
                # print(des[0]['description'])
                user_question1 = {"isuser": True, "text": dict_object['ambiguous_question'], "type": 'AMBIGUOUS'}
                system_response1 = {"isuser": False, "text": dict_object['clarify_answer'], "type": 'CLARIFY'}
                user_question2 = {"isuser": True, "text": dict_object['question'], "type": 'INFER_SQL'}
                system_response2 = {"isuser": False, "query": dict_object['sqlquery'],"result":result, "text": des[0]['description'], "type": 'CONFIRM_SQL'}
            else:
                user_question1 = {"isuser": True, "text": dict_object['ambiguous_question'], "type": 'AMBIGUOUS'}
                system_response1 = {"isuser": False, "text":dict_object['clarify_answer'], "type": 'CLARIFY'}
                user_question2 = {"isuser": True, "text": dict_object['question'], "type": 'INFORM_SQL'}
                system_response2 = {"isuser": False, "query": dict_object['sqlquery'],"result":result, "text": dict_object['description'], "type": 'CONFIRM_SQL'}
                
            qa_pair.append(user_question1)
            qa_pair.append(system_response1)
            qa_pair.append(user_question2)
            qa_pair.append(system_response2)
        else:
            # print(dict_object)
            print("SQL invalid")

    return(qa_pair)

# Type 3: INFORM_SQL-CONFIRM_SQL
def inform_confirm(database_id,utterance,goal_sql):
    question1 = get_confirm(database_id, utterance, goal_sql)
    # print(question1)
    answer1 = ask(question1)
    # print(answer1)
    text_sqls = parse_json(answer1)

    qa_pair = []
    for dict_object in text_sqls:
        sql_value = dict_object.get('sql','')
        result, execution_time ,executable = bird_sql_evoke(sql_value,database_id)
        if executable and result != []:
            # print(dict_object['text'], dict_object['sql'],dict_object['description'])
            # print(dict_object)
            print("SQL valid")
            user_question = {"isuser": True, "text": dict_object['text'], "type": 'INFORM_SQL'}
            system_response = {"isuser": False, "query": dict_object['sql'],"result":result, "text": dict_object['description'], "type": 'CONFIRM_SQL'}
            qa_pair.append(user_question)
            qa_pair.append(system_response)
        else:
            # print(dict_object)
            print("SQL invalid")

    return(qa_pair)

# Type 4: CANNOT ANSWER-SORRY
def cannot_sorry(database_id,utterance,goal_sql):
    question1 = get_cannot(database_id, utterance, goal_sql)
    # print(question1)
    answer1 = ask(question1)
    # print(answer1)
    text_sqls = parse_json(answer1)

    qa_pair = []
    for dict_object in text_sqls:
        # print(dict_object['user'], dict_object['explanation'])
        # print(dict_object)
        print("SQL valid")
        user_question = {"isuser": True, "text": dict_object['user'], "type": 'CANNOT_ANSWER'}
        system_response = {"isuser": False, "text": dict_object['explanation'], "type": 'SORRY'}
        qa_pair.append(user_question)
        qa_pair.append(system_response)
    return(qa_pair)

# Type 5: IMPROPER-REQUEST MORE/GREETING/SORRY/WELCOME/GOOD BYE
def improper(database_id,utterance,goal_sql):
    question1 = get_improper(database_id, utterance, goal_sql)
    # print(question1)
    answer1 = ask(question1)
    # print(answer1)
    text_sqls = parse_json(answer1)

    qa_pair = []
    for dict_object in text_sqls:
        # print(dict_object)
        print("SQL valid")
        user_question = {"isuser": True, "text": dict_object['question'], "type": dict_object['question_type']}
        system_response = {"isuser": False, "text": dict_object['answer'], "type": dict_object['answer_type']}
        qa_pair.append(user_question)
        qa_pair.append(system_response)
    return(qa_pair)


# 创建 ArgumentParser 对象
parser = argparse.ArgumentParser(description='Generate categorized multi-round interactive quizzes')

# 添加命令行参数
parser.add_argument('--csv_file_path', type=str, help='Path to the CSV file')
parser.add_argument('--type_needed', type=int, help='Type needed')
parser.add_argument('--id_needed', type=int, nargs='+', help='IDs needed (space-separated list)')
parser.add_argument('--projectname', type=str, help='Project name')

# 解析命令行参数
args = parser.parse_args()

# 使用参数
csv_file_path = args.csv_file_path
type_needed = args.type_needed
id_needed = args.id_needed
projectname = args.projectname

print(f"CSV File Path: {csv_file_path}")
print(f"Type Needed: {type_needed}")
print(f"ID Needed: {id_needed}")
print(f"Project Name: {projectname}")

# csv_file_path = 'goals_of_cosql_dev.csv'  # 请将文件路径替换为实际路径
# type_needed = 10
# id_needed = [6,10] 
# projectname = 'gemini的6-10'
# 读取CSV文件 遍历Gq
start_time = time.time()  # 获取当前时间

with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for goal_question_data in reader:
        if int(goal_question_data['id']) < id_needed[0] or int(goal_question_data['id']) > id_needed[1]:# 处理id区间
            continue
        print("__________________________________________________")
        print("Current round data :")
        print("Generation range :"+str(id_needed))
        print("goal_id :", goal_question_data['id'])
        print("db_id :", goal_question_data['db_id'])
        # print("goal_sql:", goal_question_data['goal_sql'])
        utterance = "json properties and values should be double-quoted.new questions must be related to previous questions and have entity omissions/dependencies in new questions' text. The question you ask needs to be difficult enough that it requires the use of complex sql to answer it. Previous questions are below(maybe null):"
        goal_sql = goal_question_data['goal_sql']
        db_name = goal_question_data['db_id']

        
        # 创建一个字典，将数字映射到函数
        functions = {
            1: infer_confirm,
            2: ambiguous_clarify,
            3: inform_confirm,
            4: cannot_sorry,
            5: improper
        }
        
        # 从1到5中随机选择type_needed个数字
        selected_numbers = random.choices(range(1, 6), k=type_needed)
        print("types:")
        print(selected_numbers)
        # selected_numbers = [2,2,2]
        # 对于每个选定的数字，执行对应的函数
        
        for number in selected_numbers:
            try:
                result = functions[number](db_name,utterance ,goal_sql)
                text_list = [str(item['text']) for item in result]
                combined_text = ' '.join(text_list)
                utterance = utterance + combined_text
                # print("utterance")
                # print(utterance)
                save_cp(goal_question_data['id'],db_name,result,projectname)
                if result[1]['type'] == 'GOOD_BYE':
                    break
                if result[1]['type'] == 'WELCOME':
                    break
            except Exception as e:
                print(f"An error occurred: {e}")
                continue
                
end_time = time.time()  # 获取当前时间
print(f"Execution time: {end_time - start_time} seconds")
    