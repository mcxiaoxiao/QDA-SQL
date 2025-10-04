# QDA-SQL: Questions Enhanced Dialogue Augmentation for Multi-Turn Text-to-SQL  


## Abstract
QDA-SQL leverages large language models (LLMs) to generate multi-turn dialogue samples with diverse question types for Text-to-SQL data augmentation. Given a set of question examples and databases, it produces high-quality samples. This document uses the CoSQL dataset as an example, which does not include domain-specific knowledge. If domain-specific knowledge is required, please specify it in `goals_of_cosql_dev.csv`. Additionally, `Supplementary_Material.pdf` contains written information that aids in understanding the paper.




## Getting Started
😉 To ensure the project runs correctly, you need to first organize your dataset according to the [file structure](#file-structure)
### STEP 1: Parse Dataset (Optional)
(**CSV file has already been generated. If no new data needs to be added, you can proceed to the next step**. New data can be added following the format in `goals_of_cosql_dev.csv`). To parse the dataset, specify the path to `cosql_all_info_dialogs.json` and run `cosql_parse_to_csv.py` to generate `goals_of_cosql_dev.csv`.
```bash
python cosql_parse_to_csv.py
```

### STEP 2: Generate Question-Answer Pairs
Run `classification_generate_multithread.py` to generate multi-turn dialogues with classification. Parameters:
- `csv_file_path`: Path to the CSV file containing the organized goalsql data.
- `type_needed`: Maximum number of dialogues to generate.
- `start_id`: Starting ID.
- `end_id`: Ending ID.
- `threads`: Number of threads.
- `projectname`: Name of the folder to save the results.

```bash
# Example
python classification_generate_multithread.py --csv_file_path goals_of_cosql_dev.csv --type_needed 10 --start_id 20 --end_id 1000 --threads 5 --projectname "test"
```
💡 For instance, `type_needed = 8` and `id_needed = [1000, 1500]` mean generating dialogues with up to 8 different combinations of Thematic Relation and Q-A type, within the question_id range [1000, 1500] from goalsql (`goals_of_cosql_dev.csv`). The generated Q&A pairs will be saved in `QAs_generate/c_outputs/XXX`.

### STEP 3: Filter and Optimize
Run `critic_merge_classification_generate.py` to merge, filter, and optimize the multi-turn data generated in the previous step. The results will be saved as `XXX.json` (initial filter), `XXX_optimized.json` (optimized), and `XXX_filtered.json` (final filter). Parameters:
- `csv_file_path`: Path to the CSV file containing the organized goalsql data.
- `filename`: Name of the folder to save the results.

```bash
# Example
python critic_merge_classification_generate.py --csv_file_path goals_of_cosql_dev.csv --projectname "test" --threads 5 --savename "merged_test.json"
```

## Evaluation
### SQL Generation Task
We follow the SParC evaluation methodology to compute metrics such as Exact Match (EM), Interaction Exact Match (IEM), Execution Match (EX), and Interaction Execution Match (IEX). For detailed definitions, refer to the [SParC GitHub page](https://github.com/taoyds/sparc).</br>
We have provided an evaluation script `evaluation.py` in the `evaluation` folder, adapted from the SParC test scripts, to evaluate our outputs. An example model output is also provided as `example.json`.

```bash
# Example
python evaluation.py --json example.json --etype all --db ../QAs_generate/datasets/cosql_dataset/database --table ../QAs_generate/datasets/cosql_dataset/tables.json
```


## File Architecture

- **QAs_generate/datasets/**: Stores datasets, such as `QAs_generate/datasets/cosql_dataset/database` and `QAs_generate/datasets/BIRD/dev/dev_databases`. The dataset organization should follow the format of [Spider](https://github.com/taoyds/spider).
Recommended datasets:

| Dataset | Description | Download Link |
|---------|-------------|---------------|
| Spider  | A large-scale complex and cross-domain semantic parsing and text-to-SQL dataset | [Spider](https://yale-lily.github.io/spider) |
| CoSQL   | A conversational text-to-SQL dataset | [CoSQL](https://yale-lily.github.io/cosql) |
| SParC   | A cross-domain semantic parsing in context dataset | [SParC](https://yale-lily.github.io/sparc) |
| BIRD    | A Big Bench for Large-Scale Database Grounded Text-to-SQLs | [BIRD](https://bird-bench.github.io/) |

These datasets are organized in format compatible with our generation scripts.

- **QAs_generate/outputs/**: Stores generated dialogues, such as `QAs_generate/outputs/test2/` for dialogues generated with the project name test2, and `dev/outputs/test2_merged.json` for the merged results of test2 dialogues (additional processing like difficulty assessment and high-quality result filtering can be added).

- **QAs_generate/tools/**: Stores utility tools.

- **QAs_generate/function_test.ipynb**: Provides code examples for testing and using various tools, facilitating deeper modifications of each interface.

- **QAs_generate/cosql_parse_to_csv.py**: Parses the CoSQL dataset, extracts useful data, and generates a standard `dev/goals_of_cosql_dev.csv` for subsequent dialogue generation. For other datasets, create corresponding `XXXXX_parse` files to generate `dev/goals_of_XXXXX.csv`, keeping the column names unchanged.

- **QAs_generate/token_count.txt**: Tracks token usage with the OpenAI API. To reset the count, set the number to 0.

- **QAs_generate/classification_generate_multithread.py**: Runs `classification_generate` in multiple threads to speed up the generation of Q&A samples.

- **stageflow/**: Example scripts for stageflow.
