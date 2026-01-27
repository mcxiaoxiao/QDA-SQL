import os
import json
from loguru import logger
from tools.sql_execute_detail import sqlite_execute as execute
import copy
import re
from tqdm import tqdm
from tools.db_detail import bird_getdesc
from tools.llm import ask_question_gemini

# 配置参数
input_file_path = 'testsets/sparc_dev_SQLonly.json'  # 修改为testset文件夹下的cosql_dev.json
output_file_path = 'outputs/gemini-3-pro_zeroshot_cosql_dev201-f.json'  # 输出文件路径

# 确保输出目录存在
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

definition = '''
ambiguous: When the question contains ambiguous tokens that may appear in multiple locations within the tables. The system needs to request clarification from the user.
Example: "What's the id of Glenn?" - The system should ask "Do you mean the location of the school named 'Glenn' or the id of the donator named Glenn?"

answerable: When the question is clear, and the queried column exists. The system needs to provide an SQL query based on the context.
Example: "No, I mean the id of the donator named Glenn." - The system should respond with an SQL query like "SELECT endowment_id FROM endowment WHERE "donator_name" LIKE "Glenn%";"

unanswerable: When the question involves information that is missing from the database. The system needs to explain to the user the reason for this absence.
Example: "Are all the donors from the same country?" - The system should respond with "Sorry we don't have the information about the nationality of the donators."

improper: When the question does not pertain to querying a database. A regular system response will suffice.
Example: "Thanks!" - The system should respond with "You are welcome!"
'''

def parse_json(content):
    try:
        content = content.replace("\n","")
        content = content.strip()
        json_objects = re.findall(r'\{.*?\}', content)
        parsed_objects = []
        for json_object in json_objects:
            dict_object = json.loads(json.dumps(eval(json_object)))
            parsed_objects.append(dict_object)
        return parsed_objects
    except Exception as e:
        print(e)
        return []

# 加载输入数据
logger.info(f'Loading input data from: {input_file_path}')
with open(input_file_path, 'r', encoding='utf-8') as infile:
    items = json.load(infile)
    #只选择一部分的输入
    items = items[201:]


# 初始化输出文件
if os.path.exists(output_file_path):
    os.remove(output_file_path)

with open(output_file_path, 'w', encoding='utf-8') as outfile:
    outfile.write('[]')

# 遍历处理每个对话
for item in tqdm(items):

    # 统计进度：当前是第几个 item，还剩几个
    current_idx = items.index(item) + 1
    remaining = len(items) - current_idx
    logger.success(f"Progress: {current_idx}/{len(items)} processed, {remaining} remaining.")

    try:
        # 初始化对话历史
        history = []
        
        for index in range(0, len(item['turns']), 2):
            if index + 1 < len(item['turns']):
                question = item['turns'][index]['text']
                description = bird_getdesc(item['db_name'])
                system_is = "You are a SQL question detector and you need to categorize the type of user question and answer the user with the requested content"
                
                # 构建带有历史的查询提示词
                history_str = "Previous Conversation History:" + "\n".join([f"User: {h['user']}\nAssistant: {h['assistant']}" for h in history]) + "\n" if history else ""
                query_is = 'Database Structure:' + description + "Classification Definition:" + definition + history_str + "User Question:" + question + '\nCategorize and answer user questions based on database structure and conversation history, output in json format {"type":"", "reply":""} don\'t output other text or explanation'
                
                logger.info(f'Processing question: {question}' + f' Index: {index}')
                logger.info(f'Query IS with history: {query_is}')
                
                # 使用Gemini API获取响应
                response = ask_question_gemini(query_is)
                logger.info(f'Received response: {response}')
                sql_query = ''
                # 解析响应
                result = parse_json(response)
                if result:
                    result = result[0]
                    item['turns'][index+1]['predict_type'] = result.get('type', '')
                    item['turns'][index+1]['predict'] = result.get('reply', '')
                
                if item['turns'][index+1]['predict_type'] == 'answerable':

                    logger.info(f'Answerable question: {question}' + f' Index: {index}')

                    # 构建SQL查询提示词，包含对话历史
                    system = f"/* Given the following tables in the sqlite database: */\n{description}\n/* Answer the following dialogue questions based on the above database information, conversation history, and using only SQL: */\n"
                    sql_history_str = "Conservation History:\n".join([f"User: {h['user']}\nAnswer: {h['assistant']}\n SQL: {h['sql']}" for h in history]) + "\n" if history else ""
                    query_final = system + sql_history_str + "Current User Question:" + question
                    
                    # 记录SQL查询提示词
                    logger.info(f'SQL Query Prompt with history: {query_final}')
                    
                    # 使用Gemini API获取SQL响应
                    sql_response = ask_question_gemini(query_final)
                    logger.info(f'Received SQL response: {sql_response}')
                    
                    # 提取SQL查询
                    sql_query = sql_response.strip()
                    
                    # 保存预测结果
                    item['turns'][index+1]['predict'] = sql_query
                
                # 更新对话历史
                history.append({
                    'user': question,
                    'assistant': item['turns'][index+1]['predict'],
                    'sql': sql_query
                })
        
        # 将结果写入输出文件（每处理完一个对话就更新）
        with open(output_file_path, 'r+', encoding='utf-8') as outfile:
            # 读取当前内容
            outfile.seek(0)
            current_data = json.load(outfile)
            
            
            current_data.append(item)
            
            # 重新写入完整数据
            outfile.seek(0)
            outfile.truncate()
            json.dump(current_data, outfile, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Error processing item: {e}")
        import traceback
        traceback.print_exc()

logger.info(f'All predictions saved to: {output_file_path}')
