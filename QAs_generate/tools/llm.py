import requests
import json
import time
from zhipuai import ZhipuAI
import re
from openai import OpenAI
import os
import random
from IPython.display import Markdown
 

client1 = OpenAI(api_key="") # please fill in your own API key

def remove_sql_blocks(text):
    cleaned_text = text.replace('sql', '',1)
    code_blocks = re.findall(r'```(.*?)```', cleaned_text, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    else: 
        return  text

def ask_question_gpt(prompt):
    messages = [{"role": "user", "content": prompt}]
    for attempt in range(10):  # Retry up to 10 times
        try:
            response = client1.chat.completions.create(
                model='gpt-4o',
                messages=messages,
                temperature=0.0
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(e)
            if attempt < 50:  # Don't wait after the last attempt
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"An error occurred with GPT request after 10 attempts: {e}")
                return "failed"

# glm
def ask_question_glm(question):
    
    
    client = ZhipuAI(api_key="xxxxx") # 请填写您自己的APIKey
    
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
    "xxxxx",
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
            time.sleep(3)  # 暂停一秒再重试，以防止过于频繁的请求
    
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
