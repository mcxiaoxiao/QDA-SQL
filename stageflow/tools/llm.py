import requests
import json
import time
from zhipuai import ZhipuAI
import re
import openai
import os
import random
from IPython.display import Markdown
 



def remove_sql_blocks(text):
    cleaned_text = text.replace('sql', '',1)
    code_blocks = re.findall(r'```(.*?)```', cleaned_text, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    else: 
        return  text
    

# openai
def ask_question_gpt(question):
    openai.api_key = "your_openai_api_key" 
    prompt = question
    max_retries = 5
    retry_count = 0
    def request(prompt):

        try:
            print("waiting response from GPT....")
            result = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
            print("Received response from GPT.")
        
            # print("Reading token count from file...")
            with open("token_count.txt", "r") as file:
                token_count = file.read()
                if token_count == '':
                    token_count = 0
                else:
                    token_count = int(token_count)
            print(f"Current token count: {token_count}")
            token_count += int(result['usage']['total_tokens'])
            print(f"New token count: {token_count}")
    
            with open("token_count.txt", "w") as file:
                # print(token_count)
                file.write(str(token_count))
    
            return(result['choices'][0]['message']['content'].strip())
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    while retry_count < max_retries:
        result = request(prompt)
        # 调试用：
        # result = '[{"text": "Which circuit has the highest altitude?", "sql": "SELECT name, MAX(alt) FROM circuits","des":"这是描述1"}, {"text": "Who is the oldest driver?", "sql": "SELECT forename, surname, MAX(dob) FROM drivers","des":"这是描述2"}]'
        
        if result is not None:
            return result
        else:
            print("Failed to make request, retrying...")
        retry_count += 1
        time.sleep(3)  # 暂停一秒再重试，以防止过于频繁的请求
    return "请求错误"
    
        

# glm
def ask_question_glm(question):
    
    
    client = ZhipuAI(api_key="286239290a5586c267df06bd5e12cf13.ENorbrqN1mJF4DnV") # 请填写您自己的APIKey
    
    response = client.chat.asyncCompletions.create(
        model="glm-4",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "user",
                "content": question
            }
        ],
    )
    
    task_id = response.id
    task_status = ''
    get_cnt = 0
    
    while task_status != 'SUCCESS' and task_status != 'FAILED' and get_cnt <= 40:
        result_response = client.chat.asyncCompletions.retrieve_completion_result(id=task_id)
        # print(result_response)
        task_status = result_response.task_status
        if task_status == 'SUCCESS':
            return remove_sql_blocks(result_response.choices[0].message.content.strip())
        
        time.sleep(3)
        get_cnt += 1
        
#gemini
def ask_question_gemini(question):
    gemini_api_keys = [
    "AIzaSyCxpeaNafORNa4mddSV-da0tD1XLGeTHkw",
    "AIzaSyAUJEkCFcasjISnFQLqu5kyXFZWLppKIaU",
    "AIzaSyDfFuhj-UgJxC2ThsAgPYPhKyjFaPHqJ1M",
    "AIzaSyAWaTmfp7pCPcxpZln7EfzyZlkrIGltZfw"
    # 添加更多API密钥
    ]
    selected_gemini_api_key = random.choice(gemini_api_keys)
    print("waiting response from Gemini....")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key="+selected_gemini_api_key
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": question
            }]
        }]
    }
    
    max_retries = 5
    retry_count = 0
    response = None
    
    while retry_count < max_retries:
        response = requests.post(url, headers=headers, json=data,timeout = 30)
    
        if response.status_code == 200:
            break
        else:
            print("Failed to make request, retrying...")
            retry_count += 1
            time.sleep(6)  # 暂停一秒再重试，以防止过于频繁的请求
    
    if response is not None and response.status_code == 200:
        response_json = response.json()
        print("Received response from Gemini.")
        # generated_text = response_json['candidates'][0]['content']['parts'][0]['text']
        # 安全地访问嵌套的字典和列表
        generated_text = response_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        return generated_text
    else:
        print("Error: Failed after {} retries".format(max_retries))
        return "请求错误"
