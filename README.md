# 项目：Forex ETL Pipeline —— 外汇牌价增量同步管道

## 🚀 项目简介
本项目是一个**生产级数据工程实践项目**，实现了从**中国银行官网**实时抓取外汇牌价、经过清洗与结构化后，**增量同步**至 MySQL 数据仓库，并支持**历史趋势可视化**的完整 ETL 管道。

项目严格遵循**数据仓库分层设计**（ODS → DWD），并采用**基于哈希值的增量更新机制**，只对价格发生变动的货币进行写入，极大减少了冗余数据处理，体现了数据工程师在**数据建模、ETL 设计、反爬策略、容器化部署**等方面的综合能力。

---

## ✨ 核心功能特性
- **实时爬取**：定时抓取中国银行外汇牌价（每 5~7 分钟），支持网络异常自动重试与指数退避。
- **智能解析**：动态识别表头结构，列顺序自适应，空值安全处理，适应页面格式变化。
- **增量同步（核心亮点）**：基于 MD5 哈希比对，只对价格波动的货币插入新历史记录，避免全量写入。
- **数据分层存储**：
  - **ODS 层（贴源层）**：存储原始 HTML 页面，确保数据可溯源。
  - **DWD 层（明细层）**：存储清洗后的结构化历史牌价，支持任意时间点汇率回溯。
- **可视化分析**：集成 Matplotlib，可绘制任意货币的买入/卖出价历史趋势图。
- **工程化部署**：支持 Docker Compose 一键启动（MySQL + Python 调度器），实现环境一致性。

---

## 🛠️ 技术栈
| 组件 | 技术选型 | 用途 |
| :--- | :--- | :--- |
| **编程语言** | Python 3.11 | 主开发语言 |
| **包管理** | uv | 高性能 Python 包管理工具 |
| **数据采集** | requests + BeautifulSoup4 | 网页请求与 HTML 解析 |
| **数据存储** | MySQL 8.0 (Docker) | 数据仓库（ODS/DWD 分层存储） |
| **任务调度** | 自研调度器（while + time.sleep） | 定时触发 ETL 任务，内置熔断机制 |
| **可视化** | Matplotlib + Pandas | 历史数据趋势绘图 |
| **日志监控** | Loguru | 结构化日志输出 |
| **容器化** | Docker + Docker Compose | 一键部署与环境隔离 |

---

## 📁 项目结构
```
etl-vector-pipeline/
├── src/
│   ├── collector/
│   │   └── forex_crawler.py      # 外汇牌价爬虫（动态表头 + 重试机制）
│   ├── etl/
│   │   └── forex_etl.py          # ETL 核心（哈希比对 + 增量写入）
│   ├── scheduler/
│   │   └── forex_scheduler.py    # 调度器（定时执行 + 熔断保护）
│   ├── utils/
│   │   └── db_utils.py           # 数据库连接单例
│   └── visualization/
│       └── plot_forex.py         # 历史趋势图绘制
├── scripts/
│   └── init_forex_db.py          # 数据库初始化脚本
├── docker-compose.yml            # 多容器编排
├── Dockerfile                    # Python 应用镜像构建
├── .env.example                  # 环境变量配置模板
├── .gitignore                    # Git 忽略规则
├── pyproject.toml                # uv 项目配置
└── README.md                     # 项目文档（本文件）
```

---

## 🚀 快速启动（Docker Compose 一键部署）

### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/forex-etl-pipeline.git
cd forex-etl-pipeline
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env`，并根据需要修改数据库密码：
```bash
cp .env.example .env
# 编辑 .env 填入正确的密码
```

### 3. 构建并启动所有服务
```bash
docker compose up -d
```
首次启动会自动构建 Python 应用镜像，并拉起 MySQL 数据库。

### 4. 查看运行日志
```bash
docker compose logs -f app
```

### 5. 验证数据入库
```bash
docker exec -it etl-mysql mysql -u root -p你的密码 -e "USE forex_db; SELECT COUNT(*) FROM dwd_forex_rates;"
```

---

## 📊 可视化展示

运行趋势图绘制脚本：
```bash
uv run python -m src.visualization.plot_forex
```

将生成 `usd_trend.png` 图片，展示美元买入/卖出价历史变化曲线。  
支持修改代码中的 `currency_name` 参数绘制其他货币的趋势图。

---

## 🧪 增量同步演示（面试高频亮点）

1. **首次运行** → 全量抓取约 40 种货币，全部写入 DWD 表（新增 40 条）。  
2. **模拟价格变动** → 在 MySQL 中手动修改美元买入价（例如 `UPDATE ... SET buy_rate = '999.99'`）。  
3. **再次运行** → 调度器抓取实时数据，发现美元哈希变化，**仅新增 1 条美元记录**，其余 39 种货币跳过。  

这证明了管道**只处理增量数据**，而非全量重建，具备 **幂等性** 和 **高效性**。

---

## 🗃️ 数据表结构（关键）

| 表名 | 分层 | 核心字段 | 说明 |
| :--- | :--- | :--- | :--- |
| `ods_forex_raw` | ODS | `raw_html`, `fetch_time` | 存储原始 HTML 源码，用于溯源 |
| `dwd_forex_rates` | DWD | `currency_name`, `buy_rate`, `sell_rate`, `hash_key`, `fetch_time` | 清洗后的历史牌价，基于 `hash_key` 去重 |
| `forex_dirty_log` | 日志 | `error_type`, `raw_snippet` | 记录解析异常的数据片段 |
| `forex_sync_metadata` | 元数据 | `inserted_count`, `status` | 记录每次 ETL 执行的统计信息 |

---

## 🛡️ 反爬与鲁棒性设计
- **User-Agent**：模拟真实浏览器请求。
- **随机延迟**：每次请求前随机暂停 1~3 秒，避免规律性被识别。
- **指数退避重试**：遇到 429 或网络超时，等待 60s → 120s → 240s 后重试。
- **熔断机制**：连续失败 5 次后自动停止调度，防止无限循环浪费资源。

---

## 🧠 技术亮点（面试时可重点阐述）
1. **数据分层建模**：严格遵循 ODS → DWD 分层，体现数仓设计思想。
2. **增量同步算法**：基于价格字段的哈希比对，而非全表扫描，高效且准确。
3. **动态表头解析**：不依赖列顺序，自动适配页面结构变化，提升管道健壮性。
4. **历史追溯能力**：DWD 层保留每次价格变化的时间快照，支持任意时点回溯。
5. **工程化交付**：Docker Compose 一键部署，环境一致性保障。

---

## 📦 依赖清单
详见 `pyproject.toml`，主要依赖：
- `requests`
- `beautifulsoup4`
- `pymysql`
- `pandas`
- `matplotlib`
- `loguru`
