import threading
import subprocess
import argparse
import os
from tqdm import tqdm
import time

def split_range(start, end, chunks):
    """将范围拆分为若干个子区间"""
    step = (end - start) // chunks
    ranges = [(start + i * step, start + (i + 1) * step - 1) for i in range(chunks - 1)]  # 为最后一个区间留出空间
    ranges.append((start + (chunks - 1) * step, end))  # 确保最后一个区间覆盖到end
    return ranges

def run_script(csv_file_path, type_needed, id_range, projectname):
    """构建并运行命令"""
    
    id_needed = f"{id_range[0]} {id_range[1]}"
    cmd = f"python classification_generate.py --csv_file_path {csv_file_path} --type_needed {type_needed} --id_needed {id_needed} --projectname \"{projectname}\""
    subprocess.run(cmd, shell=True)

def monitor_progress(directory, total_files, initial_count):
    """监控目录下文件数量的变化，并更新进度条"""
    with tqdm(total=total_files) as pbar:
        current_count = initial_count
        while current_count + 1 < initial_count + total_files:
            new_count = len(os.listdir(directory))
            pbar.update(new_count - current_count)
            current_count = new_count
            time.sleep(10)  # 每10秒检查一次

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='Run a script with multiple threads.')
    parser.add_argument('--csv_file_path', type=str, required=True, help='Path to the CSV file.')
    parser.add_argument('--type_needed', type=int, required=True, help='Type needed.')
    parser.add_argument('--start_id', type=int, required=True, help='Start ID.')
    parser.add_argument('--end_id', type=int, required=True, help='End ID.')
    parser.add_argument('--threads', type=int, required=True, help='Number of Threads.')
    parser.add_argument('--projectname', type=str, required=True, help='Base name for the project.')

    args = parser.parse_args()

    # 使用命令行参数
    csv_file_path = args.csv_file_path
    type_needed = args.type_needed
    start_id = args.start_id
    end_id = args.end_id
    threads_count = args.threads
    projectname = args.projectname

    output_directory = f"c_outputs/{projectname}"
    os.makedirs(output_directory, exist_ok=True)
    
    # 拆分id_needed区间
    id_ranges = split_range(start_id, end_id, threads_count)

    # 获取初始文件数量
    output_directory = f"c_outputs/{projectname}"
    initial_file_count = len(os.listdir(output_directory))

    # 需要生成的总文件数量
    total_files_needed = end_id - start_id + 1

    # 启动监控进度的线程
    monitor_thread = threading.Thread(target=monitor_progress, args=(output_directory, total_files_needed, initial_file_count))
    monitor_thread.start()

    # 创建并启动数据处理线程
    data_threads = []
    for id_range in id_ranges:
        t = threading.Thread(target=run_script, args=(csv_file_path, type_needed, id_range, projectname))
        t.start()
        data_threads.append(t)

    # 等待所有数据处理线程完成
    for t in data_threads:
        t.join()

    # 等待监控进度的线程完成
    monitor_thread.join()

    print("Execution of all commands is complete.")
