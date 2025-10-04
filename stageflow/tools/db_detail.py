import os
import pandas as pd
import json

def bird_getdesc(dbname):
    # 指定JSON文件路径
    filepath = 'datasets/cosql_dataset/tables.json'

    # 读取JSON文件
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 在JSON数据中查找包含特定db_id:dbname对的数组
    result = [item for item in data if 'db_id' in item and item['db_id'] == dbname]

    table_names_original = result[0]['table_names_original']
    column_names_original = result[0]['column_names_original']
    column_names = result[0]['column_names']    
    column_types = result[0]['column_types'] 

    
    if result:
        desc = ""
        i=0
        for table_index, table_name in enumerate(table_names_original):
            desc=desc+table_name+'('
            for column_index, column_value in enumerate(column_names_original):
                if column_value[0]==table_index:
                    desc=desc+'|'+column_value[1]+':'+column_names[column_index][1]+' Type:'+column_types[column_index]
                    i=i+1
            desc=desc+')\n'
        return desc
    else:
        # 如果没有找到匹配的结果，返回空数据帧
        return " 无描述 "
