import os
import json
from transformers import AutoTokenizer
import torch
from loguru import logger
import copy
from tqdm import tqdm
from tools.db_detail import bird_getdesc
from trainer.component.utils import ModelUtils
from trainer.component.template import template_dict

input_file_path = 'multi_eval/cosqlSQLtest.json'
output_file_path = 'multi_eval/分段训练CodeLlama-7b-base测试集生成结果.json'
model_name_or_path = '/mnt/nvme1n1p2/share/hf-models/CodeLlama-7b-Instruct-hf'
# model_name_or_path = '../../LLaMA-Factory/nsql-llama-2-7B'
# model_name_or_path = 'trainer/script/checkpoint/CodeLlama-7b-Instruct-hf-aug-qlora-sft-merge'
# model_name_or_path = 'trainer/script/checkpoint/CodeLlama-7b-Instruct-hf-aug-qlora-sft-merge'
template_name = 'llama2'
adapter_name_or_path = None

template = template_dict[template_name]

load_in_4bit = False

device="cuda"
max_new_tokens = 300
top_p = 0.9
temperature = 0.05
repetition_penalty = 1.0

def build_prompt_chatglm3(tokenizer, query, history, system=None):
    history.append({"role": 'user', 'message': query})
    # system
    input_ids = tokenizer.get_prefix_tokens() + \
                [tokenizer.get_command(f"<|system|>")] + \
                tokenizer.encode(system, add_special_tokens=False)
    # convs
    for item in history:
        role, message = item['role'], item['message']
        if role == 'user':
            tokens = [tokenizer.get_command(f"<|user|>")] + \
                     tokenizer.encode(message, add_special_tokens=False) + \
                     [tokenizer.get_command(f"<|assistant|>")]
        else:
            tokens = tokenizer.encode(message, add_special_tokens=False) + [tokenizer.eos_token_id]
        input_ids += tokens

    return input_ids

def build_prompt(tokenizer, template, query, history, system=None):
    template_name = template.template_name
    system_format = template.system_format
    user_format = template.user_format
    assistant_format = template.assistant_format
    system = system if system is not None else template.system

    if template_name == 'chatglm2':
        prompt = tokenizer.build_prompt(query, history)
        input_ids = tokenizer.encode(prompt)
    elif template_name == 'chatglm3':
        input_ids = build_prompt_chatglm3(tokenizer, query, history, system)
    else:
        history.append({"role": 'user', 'message': query})
        input_ids = []

        # setting system information
        if system_format is not None:

            if system is not None:
                system_text = system_format.format(content=system)
                input_ids = tokenizer.encode(system_text, add_special_tokens=False)
        # concat conversation
        # print("——————history————————\ninput:"+system_text)
        for item in history:
            role, message = item['role'], item['message']
            if role == 'user':
                message = user_format.format(content=message, stop_token=tokenizer.eos_token)
            else:
                message = assistant_format.format(content=message, stop_token=tokenizer.eos_token)
            # print(message)
            tokens = tokenizer.encode(message, add_special_tokens=False)
            input_ids += tokens
    input_ids = torch.tensor([input_ids], dtype=torch.long)
    # print("——————————————")
    return input_ids

def load_tokenizer(model_name_or_path):
    # config = AutoConfig.from_pretrained(model_name_or_path, trust_remote_code=True)
    # 加载tokenzier
    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path,
        trust_remote_code=True,
        use_fast=False
        # use_fast=False if config.model_type == 'llama' else True
    )

    if tokenizer.__class__.__name__ == 'QWenTokenizer':
        tokenizer.pad_token_id = tokenizer.eod_id
        tokenizer.bos_token_id = tokenizer.eod_id
        tokenizer.eos_token_id = tokenizer.eod_id
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # assert tokenizer.pad_token_id is not None, "pad_token_id should not be None"
    return tokenizer
import json
from tqdm import tqdm

template = template_dict[template_name]
logger.info(f'Loading model from: {model_name_or_path}')
logger.info(f'adapter_name_or_path: {adapter_name_or_path}')

model = ModelUtils.load_model(
    model_name_or_path,
    load_in_4bit=load_in_4bit,
    adapter_name_or_path=adapter_name_or_path
).eval()
tokenizer = load_tokenizer(model_name_or_path if adapter_name_or_path is None else adapter_name_or_path)

if template_name == 'chatglm2':
    stop_token_id = tokenizer.eos_token_id
elif template_name == 'chatglm3':
    stop_token_id = [tokenizer.eos_token_id, tokenizer.get_command("<|user|>"), tokenizer.get_command("<|observation|>")]
else:
    if template.stop_word is None:
        template.stop_word = tokenizer.eos_token
    stop_token_id = tokenizer.encode(template.stop_word, add_special_tokens=False)
    assert len(stop_token_id) == 1
    stop_token_id = stop_token_id[0]

with open(input_file_path, 'r', encoding='utf-8') as infile:
    items = json.load(infile)

if os.path.exists(output_file_path):
    os.remove(output_file_path)

with open(output_file_path, 'w', encoding='utf-8') as outfile:
    outfile.write('[]')

for item in tqdm(items[:]):
    # print("————————————————————————————————————————")
    history = []  
    try:
        for index in range(0, len(item['turns']), 2):
            if index + 1 < len(item['turns']):
                question = item['turns'][index]['text']


                description = bird_getdesc(item['db_name'])
                system = f"/* Given the following tables in the sqlite database: */\n{description}\n/* Answer the following dialogue questions based on the above database information using only SQL: */\n"
                query = question

                input_ids = build_prompt(tokenizer, template, query, copy.deepcopy(history), system=system).to(model.device)
                attention_mask = torch.ones(input_ids.shape,dtype=torch.long,device=device)
                outputs = model.generate(
                    input_ids=input_ids, max_new_tokens=max_new_tokens, do_sample=True,
                    attention_mask=attention_mask,
                    top_p=top_p, temperature=temperature, repetition_penalty=repetition_penalty,
                    eos_token_id=stop_token_id
                )
                outputs = outputs.tolist()[0][len(input_ids[0]):]
                response = tokenizer.decode(outputs).strip().replace(template.stop_word, "").strip()
                
                
                history.append({"role": 'user', 'message': query})
                history.append({"role": 'assistant', 'message': response})

                item['turns'][index+1]['predict'] = response

        with open(output_file_path, 'r+', encoding='utf-8') as outfile:
            outfile.seek(0, os.SEEK_END)
            position = outfile.tell() - 1
            outfile.seek(position)
            outfile.write(",\n" if position > 1 else "")
            json.dump(item, outfile, ensure_ascii=False)
            outfile.write("]")

    except Exception as e:
        logger.error(f"Error: {e}")

logger.info("all items processed and saved to output file.")