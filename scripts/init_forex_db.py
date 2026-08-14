#!/usr/bin/env python3
"""
外汇牌价数据库初始化脚本
创建 ODS、DWD 和日志表
"""

import os
from dotenv import load_dotenv
from pathlib import Path
import pymysql

# 加载 .env 配置
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

def get_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database='forex_db',          # 注意：这里连接到 forex_db
        charset='utf8mb4'
    )

def init_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. ODS层：原始页面存储表（存储每次抓取的完整HTML）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ods_forex_raw (
            id VARCHAR(64) PRIMARY KEY COMMENT '页面唯一ID (基于抓取时间戳)',
            raw_html LONGTEXT COMMENT '完整的HTML页面源码',
            fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
            content_hash VARCHAR(64) COMMENT '页面内容的MD5哈希',
            parse_status TINYINT DEFAULT 0 COMMENT '0-待解析, 1-解析成功, -1-解析失败',
            error_msg VARCHAR(500) COMMENT '解析错误信息'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS层-原始外汇页面'
    ''')

    # 2. DWD层：清洗后的牌价明细表（每条货币一条记录）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dwd_forex_rates (
            id VARCHAR(64) PRIMARY KEY COMMENT '记录唯一ID (currency_name + fetch_time)',
            currency_name VARCHAR(50) NOT NULL COMMENT '货币名称（如：美元）',
            buy_rate VARCHAR(20) COMMENT '现汇买入价',
            sell_rate VARCHAR(20) COMMENT '现汇卖出价',
            cash_buy_rate VARCHAR(20) COMMENT '现钞买入价',
            cash_sell_rate VARCHAR(20) COMMENT '现钞卖出价',
            central_parity VARCHAR(20) COMMENT '中行折算价',
            publish_date VARCHAR(20) COMMENT '发布日期（页面上的日期）',
            publish_time VARCHAR(20) COMMENT '发布时间（页面上的时间）',
            fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
            hash_key VARCHAR(64) NOT NULL COMMENT '基于货币名称+价格+时间的哈希值（用于增量判断）',
            is_active TINYINT DEFAULT 1 COMMENT '是否有效（逻辑删除）',
            INDEX idx_currency (currency_name),
            INDEX idx_fetch_time (fetch_time),
            INDEX idx_hash (hash_key)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD层-外汇牌价明细'
    ''')

    # 3. 脏数据日志表（记录解析失败的情况）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forex_dirty_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            error_type VARCHAR(50) NOT NULL COMMENT '错误类型: parse_error/missing_field',
            error_detail TEXT COMMENT '详细错误信息',
            raw_snippet VARCHAR(500) COMMENT '错误数据片段',
            fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
            INDEX idx_fetch_time (fetch_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外汇脏数据日志'
    ''')

    # 4. 同步元数据表（记录每次同步的状态）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forex_sync_metadata (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sync_id VARCHAR(64) COMMENT '同步批次ID',
            total_processed INT DEFAULT 0 COMMENT '处理总数',
            inserted_count INT DEFAULT 0 COMMENT '新增记录数',
            updated_count INT DEFAULT 0 COMMENT '更新记录数',
            deleted_count INT DEFAULT 0 COMMENT '删除记录数',
            error_count INT DEFAULT 0 COMMENT '错误数',
            sync_start DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '同步开始时间',
            sync_end DATETIME COMMENT '同步结束时间',
            status VARCHAR(20) DEFAULT 'running' COMMENT 'running/success/failed'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外汇同步元数据'
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ forex_db 所有表创建成功！")
    print("   - ods_forex_raw (原始页面)")
    print("   - dwd_forex_rates (牌价明细)")
    print("   - forex_dirty_log (脏数据日志)")
    print("   - forex_sync_metadata (同步元数据)")

if __name__ == '__main__':
    init_tables()
