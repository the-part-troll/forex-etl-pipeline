# test_mysql.py
import pymysql

try:
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="etl_pass",
        database="mysql",
        charset="utf8mb4"
    )
    print("✅ Python 连接MySQL成功")
    cur = conn.cursor()
    cur.execute("SELECT VERSION();")
    print("MySQL版本:", cur.fetchone())
    conn.close()
except Exception as e:
    print("❌ 连接失败：", e)
