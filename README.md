# 多轮对话自动生成 Multi-Turn Text-to SQL dataset Auto-generation
## 文件夹/文件 的作用？
  
- QAs_generate/datasets/ 放数据集，比如QAs_generate/datasets/BIRD/dev/dev_databases dev/datasets/BIRD/dev/dev_tables.json
- QAs_generate/outputs/ 生成的对话，其中比如 QAs_generate/outputs/test2/ 下用来放置任务名为test2生成的对话 dev/outputs/test2_merged.json 存放 test2对话的合并（顺便可以加上想要的其他处理，比如衡量难度，筛选高质量生成结果）
- QAs_generate/tools/ 用到的工具

- QAs_generate/function_test.ipynb 以下各个引用的工具的测试和使用案例
  - db_detail 根据数据集的table描述文件生成对指定数据库的描述
  - evaluation 生成parsed sql和sql hardness（spider标准）
  - generate_questions 填充prompt，组成各种问题
  - llm 调用LLM（调用gpt*/glm*/gemini*）
  - sql_execute 执行sql语句，只有sqlite，现在可以返回执行状况，执行耗时，执行结果
  - merge_outputs 合并 dev/datasets/下的对话数据，可以定些筛选规则，增加合并些数据（比如难度，标注行为）进去

- QAs_generate/cosql_parse_to_csv.py 解析cosql数据集，把有用的数据提取进来，生成标准的dev/goals_of_cosql_dev.csv供之后的生成对话程序使用 要是有别的数据集可以换XXXXX_parse生成dev/goals_of_XXXXX.csv 列名不变
  
- QAs_generate/token_count.txt 使用openai api token数计数器，如果需要归零数字改成0即可

- QAs_generate/classification_generate_multithread.py 多线程运行 classification_generate 加速生成

## 生成区分行为类型的对话 
⚠️ cosql 没有领域知识

### STEP1 解析数据集
(**csv已经生成好,如果不需要加入新数据可以直接下一步** 规范格式用 可以手动写新的数据进csv ) 解析数据集步骤：填写 cosql_all_info_dialogs.json 地址，运行 `cosql_parse_to_csv.py` 生成 goals_of_cosql_dev.csv
```
python cosql_parse_to_csv.py
```

### STEP2 问答对生成
运行 `classification_generate_multithread.py` 生成有分类多轮数据 csv_file_path:整理好的goalsql存放的csv type_needed:最多对话数量 start_id:id开始 end_id:id结束 threads:线程数 projectname:保存文件夹名 type_needed = 8 id_needed = [1000,1500] 意思是生成对话最多组合8种对话类型，goalsql选定question_id(goals_of_cosql_dev.csv中的id)区间为1000～1500 生成的问答将保存到QAs_generate/c_outputs/XXX
```
#example
python classification_generate_multithread.py --csv_file_path goals_of_cosql_dev.csv --type_needed 10 --start_id 20 --end_id 1000 --threads 5 --projectname "test"
```

### STEP3 优化+筛选
运行 `critic_merge_classification_generate.py` 合并筛选优化上一步生成的多轮数据 分别保存到 XXX.json（初步筛选） XXX_optimized.json（优化后） XXX_filtered.json（最终筛选） csv_file_path:第一步整理好的goalsql存放的csv filename:保存文件夹名

```
#example
python critic_merge_classification_generate.py --csv_file_path goals_of_cosql_dev.csv --projectname "test"  --threads 5 --savename "合并后的测试.json"
```
### STEP4 人工修改
把上一步骤生成的json人工优化

### STEP5 拆分成可以用来测试的数据集
- 为了分解出多轮SQL生成任务，参照`generate_SQL_task_datasets.ipynb`筛选适合多轮SQL生成任务的数据集
- 其他任务的格式
- 其他任务的格式


# 多轮对话benchmark数据集
根据QAs_generate中生成的完整多轮对话拆分成多个任务train集dev集

## 数据集
### 多轮SQL生成任务:QEM IEM QEX IEX
We follow the Spider evaluation methods to compute Component Matching, Exact Set Matching, Execution Accuracies.Interaction Exact Set Matching, and Interaction Execution Accuracies. Check out more details at [the Spider Github page](https://github.com/taoyds/spider).
### 其他任务:指标
评估方法
### 其他任务:指标
评估方法

