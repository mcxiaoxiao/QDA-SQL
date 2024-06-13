# QDA-SQL：多类型多轮Text-to-SQL对话自动生成
**其他语言版本: [English](README.md).**



## 生成区分行为类型的对话
⚠️ 代码以 CoSQL 为例，数据集中没有领域知识，若需要包含领域知识则在`goals_of_cosql_dev.csv`中注明。

### STEP 1: 解析数据集
(**csv 已经生成好，如果不需要加入新数据可以直接进行下一步**。可以按照`goals_of_cosql_dev.csv`的示例格式添加新的数据)
解析数据集步骤：填写 `cosql_all_info_dialogs.json` 地址，运行 `cosql_parse_to_csv.py` 生成 `goals_of_cosql_dev.csv`。
```
python cosql_parse_to_csv.py
```

### STEP 2: 问答对生成
运行 `classification_generate_multithread.py` 生成有分类的多轮数据。参数说明：
- `csv_file_path`: 整理好的 goalsql 存放的 csv 文件路径。
- `type_needed`: 最多对话数量。
- `start_id`: id 开始。
- `end_id`: id 结束。
- `threads`: 线程数。
- `projectname`: 保存文件夹名。

例如，`type_needed = 8` 和 `id_needed = [1000, 1500]` 意味着生成对话最多组合 8 次随机组合Thematic Relation和Q-A type，选定 goalsql 的 question_id（`goals_of_cosql_dev.csv` 中的 id）区间为 1000～1500。生成的问答将保存到 `QAs_generate/c_outputs/XXX`。
```
# 示例
python classification_generate_multithread.py --csv_file_path goals_of_cosql_dev.csv --type_needed 10 --start_id 20 --end_id 1000 --threads 5 --projectname "test"
```

### STEP 3: 筛选和优化
运行 `critic_merge_classification_generate.py` 合并筛选优化上一步生成的多轮数据，分别保存到 `XXX.json`（初步筛选）、`XXX_optimized.json`（优化后）、`XXX_filtered.json`（最终筛选）。参数说明：
- `csv_file_path`: 第一步整理好的 goalsql 存放的 csv 文件路径。
- `filename`: 保存文件夹名。
```
# 示例
python critic_merge_classification_generate.py --csv_file_path goals_of_cosql_dev.csv --projectname "test" --threads 5 --savename "合并后的测试.json"
```

## 数据集
### 多轮 SQL 生成任务: QM, IM, EX, IX
我们遵循 Spider 的评估方法来计算组件匹配、精确集合匹配、执行准确率、对话精确集合匹配和对话执行准确率。更多详情请参见 [Spider Github 页面](https://github.com/taoyds/spider)。

### 其他任务: 指标
评估方法。

## 文件夹/文件的作用

- **QAs_generate/datasets/**: 存放数据集，例如 `QAs_generate/datasets/BIRD/dev/dev_databases` 和 `dev/datasets/BIRD/dev/dev_tables.json`。
- **QAs_generate/outputs/**: 存放生成的对话，例如 `QAs_generate/outputs/test2/` 用于存放任务名为 test2 的生成对话，`dev/outputs/test2_merged.json` 存放 test2 对话的合并结果（可以添加其他处理，如衡量难度、筛选高质量生成结果）。
- **QAs_generate/tools/**: 存放使用的工具。

- **QAs_generate/function_test.ipynb**: 测试和使用各个引用工具的案例：
  - **db_detail**: 根据数据集的表描述文件生成对指定数据库的描述。
  - **evaluation**: 生成解析后的 SQL 和 SQL 难度（Spider 标准）。
  - **generate_questions**: 填充提示，生成各种问题。
  - **llm**: 调用 LLM（如 GPT、GLM、Gemini 等）。
  - **sql_execute**: 执行 SQL 语句，目前仅支持 SQLite，返回执行状况、执行耗时和执行结果。
  - **merge_outputs**: 合并 `dev/datasets/` 下的对话数据，可以制定筛选规则，增加合并数据（如难度、标注行为）。

- **QAs_generate/cosql_parse_to_csv.py**: 解析 CoSQL 数据集，提取有用数据，生成标准的 `dev/goals_of_cosql_dev.csv` 供之后的对话生成程序使用。如果有其他数据集，可以创建相应的 `XXXXX_parse` 文件生成 `dev/goals_of_XXXXX.csv`，列名不变。

- **QAs_generate/token_count.txt**: 使用 OpenAI API 进行 token 数量计数，如果需要归零，将数字改为 0 即可。

- **QAs_generate/classification_generate_multithread.py**: 多线程运行 `classification_generate` 加速生成。