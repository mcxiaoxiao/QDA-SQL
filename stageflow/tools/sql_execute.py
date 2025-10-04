import sqlite3
import time

def sqlite_execute(dbname, sql):
    # 连接到指定的 SQLite 数据库文件
    conn = sqlite3.connect(dbname)
    
    # 创建一个游标对象
    cursor = conn.cursor()
    
    try:
        # 记录查询开始时间
        start_time = time.time()
        
        # 执行 SQL 查询
        cursor.execute(sql)
        
        # 提交更改
        conn.commit()
        
        # 记录查询结束时间
        end_time = time.time()
        
        # 计算查询执行时间
        query_time = end_time - start_time
        
        # 获取查询结果
        result = cursor.fetchall()
        
        # 返回查询结果、执行时间和可执行性
        return result[:10], query_time, True
        
    except sqlite3.Error as e:
        # 如果执行出现异常，返回空结果、执行时间和不可执行性
        return [], 0.0, False
        
    finally:
        # 关闭连接
        conn.close()
