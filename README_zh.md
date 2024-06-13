# QDA-SQL：多类型多轮Text-to-SQL对话自动生成
**其他语言版本: [English](README.md).**</br>
代码以 CoSQL 为例，数据集中没有领域知识，若需要包含领域知识则在`goals_of_cosql_dev.csv`中注明。

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


```
# 示例
python classification_generate_multithread.py --csv_file_path goals_of_cosql_dev.csv --type_needed 10 --start_id 20 --end_id 1000 --threads 5 --projectname "test"
```
💡 例如，`type_needed = 8` 和 `id_needed = [1000, 1500]` 意味着生成对话最多组合 8 次随机组合Thematic Relation和Q-A type，选定 goalsql 的 question_id（`goals_of_cosql_dev.csv` 中的 id）区间为 1000～1500。生成的问答将保存到 `QAs_generate/c_outputs/XXX`。

### STEP 3: 筛选和优化
运行 `critic_merge_classification_generate.py` 合并筛选优化上一步生成的多轮数据，分别保存到 `XXX.json`（初步筛选）、`XXX_optimized.json`（优化后）、`XXX_filtered.json`（最终筛选）。参数说明：
- `csv_file_path`: 第一步整理好的 goalsql 存放的 csv 文件路径。
- `filename`: 保存文件夹名。
```
# 示例
python critic_merge_classification_generate.py --csv_file_path goals_of_cosql_dev.csv --projectname "test" --threads 5 --savename "合并后的测试.json"
```
## 测试
### SQL生成任务
我们遵循 Spider 的评估方法来计算SQL语句的 Exact Match(EM)、Interaction Exact Match(IEM)、Execution Match(EX)、Interaction Execution Match(IEX) 等指标。详情定义参见 [Spider Github 页面](https://github.com/taoyds/spider)。

### SQL生成+意图识别任务
评估方法采用我们提出的 MMSQL 测试集及 AccS 指标用于同时测试模型对用户提问的意图识别能力和SQL生成能力。数据集及脚本参见 [MMSQL](https://github.com/mcxiaoxiao/mmsql)。

## 文件夹/文件的作用

- **QAs_generate/datasets/**: 存放数据集，例如 `QAs_generate\datasets\cosql_dataset\database`、`QAs_generate/datasets/BIRD/dev/dev_databases` 。数据集的组织需要参照[Spider](https://github.com/taoyds/spider)的格式。
推荐数据集：

| Dataset | Description | Download Link |
|---------|-------------|---------------|
| Spider  | A large-scale complex and cross-domain semantic parsing and text-to-SQL dataset | [Spider](https://yale-lily.github.io/spider) |
| CoSQL   | A conversational text-to-SQL dataset | [CoSQL](https://yale-lily.github.io/cosql) |
| SParC   | A cross-domain semantic parsing in context dataset | [SParC](https://yale-lily.github.io/sparc) |
| BIRD    | A Big Bench for Large-Scale Database Grounded Text-to-SQLs | [BIRD](https://bird-bench.github.io/) |

这些数据集以与我们的生成脚本兼容的格式组织。

- **QAs_generate/outputs/**: 存放生成的对话，例如 `QAs_generate/outputs/test2/` 用于存放任务名为 test2 的生成对话，`dev/outputs/test2_merged.json` 存放 test2 对话的合并结果（可以添加其他处理，如衡量难度、筛选高质量生成结果）。

- **QAs_generate/tools/**: 存放调用的的工具。

- **QAs_generate/function_test.ipynb**: 测试和使用各个工具的代码案例，便于深入修改各接口代码。

- **QAs_generate/cosql_parse_to_csv.py**: 解析 CoSQL 数据集，提取有用数据，生成标准的 `dev/goals_of_cosql_dev.csv` 供之后的对话生成程序使用。对于其他数据集，可以创建相应的 `XXXXX_parse` 文件生成 `dev/goals_of_XXXXX.csv`，列名不变。

- **QAs_generate/token_count.txt**: 使用 OpenAI API 进行 token 数量计数，如果需要归零，将数字改为 0 即可。

- **QAs_generate/classification_generate_multithread.py**: 多线程运行 `classification_generate` 更快生成问答样本。