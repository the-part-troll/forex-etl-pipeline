#!/usr/bin/env python3
"""
数据库连接工具（单例模式，复用连接）
"""

import pymysql
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')

class DBConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_connection()
        return cls._instance
    
    def _init_connection(self):
        self.host = os.getenv('MYSQL_HOST', '127.0.0.1')
        self.port = int(os.getenv('MYSQL_PORT', 3306))
        self.user = os.getenv('MYSQL_USER', 'forex_user')
        self.password = os.getenv('MYSQL_PASSWORD', 'forex_pass')
        self.database = os.getenv('MYSQL_DATABASE', 'forex_db')
        self._conn = None
    
    @property
    def conn(self):
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                autocommit=False
            )
        return self._conn
    
    def close(self):
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None

# 全局单例
db = DBConnection()
