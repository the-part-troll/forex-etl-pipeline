#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from pathlib import Path
import MySQLdb as mysql
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')  


# get_connection 函数
def get_connection():
    return mysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        charset='utf8mb4'
    )

def init_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. ODS层：原始文档表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ods_documents (
            id VARCHAR(64) PRIMARY KEY,
            source_type VARCHAR(20) NOT NULL,
            source_url VARCHAR(500),
            source_key VARCHAR(100),
            raw_content LONGTEXT,
            content_hash VARCHAR(64),
            fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            clean_status TINYINT DEFAULT 0,
            error_msg VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # 2. DWD层：清洗段落表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dwd_segments (
            id VARCHAR(64) PRIMARY KEY,
            doc_id VARCHAR(64) NOT NULL,
            segment_index INT NOT NULL,
            cleaned_text TEXT NOT NULL,
            text_hash VARCHAR(64) NOT NULL,
            char_count INT DEFAULT 0,
            is_active TINYINT DEFAULT 1,
            extra_meta JSON,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES ods_documents(id) ON DELETE CASCADE,
            INDEX idx_doc_id (doc_id),
            INDEX idx_is_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # 3. 脏数据日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dirty_data_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            doc_id VARCHAR(64),
            source_key VARCHAR(100),
            error_type VARCHAR(50) NOT NULL,
            error_detail TEXT,
            raw_snippet VARCHAR(500),
            log_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # 4. 同步元数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_metadata (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sync_type VARCHAR(50) NOT NULL,
            source_key VARCHAR(100),
            total_processed INT DEFAULT 0,
            inserted_count INT DEFAULT 0,
            updated_count INT DEFAULT 0,
            deleted_count INT DEFAULT 0,
            error_count INT DEFAULT 0,
            sync_start DATETIME DEFAULT CURRENT_TIMESTAMP,
            sync_end DATETIME,
            status VARCHAR(20) DEFAULT 'running'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 所有表创建成功！数据库结构已就绪。")

if __name__ == '__main__':
    init_tables()
