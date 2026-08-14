from dotenv import load_dotenv
import os
import MySQLdb

# 加载同级目录.env文件
load_dotenv()

# 读取环境变量
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

print("=== 读取到的MySQL配置 ===")
print(f"HOST: {MYSQL_HOST}")
print(f"PORT: {MYSQL_PORT}")
print(f"USER: {MYSQL_USER}")
print(f"DATABASE: {MYSQL_DATABASE}")
print("-" * 40)

try:
    # 建立连接
    conn = MySQLdb.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DATABASE,
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION();")
    version = cursor.fetchone()
    print(f"✅ MySQL连接成功！数据库版本: {version[0]}")

    cursor.close()
    conn.close()

except MySQLdb.OperationalError as e:
    print(f"❌ 连接失败：{e}")
    print("\n排查重点提醒：")
    print("1. 当前HOST=127.0.0.1，如果你在宿主机运行脚本！")
    print("   docker容器内MySQL的127.0.0.1 ≠ 宿主机127.0.0.1")
    print("   需要改成容器IP / docker网关 / 使用容器名作为host（docker compose网络）")
    print("2. 确认etl_user账号允许对应地址访问（@% 或对应IP）")
    print("3. 检查容器3306端口映射是否正常")
except Exception as e:
    print(f"❌ 其他错误：{e}")
