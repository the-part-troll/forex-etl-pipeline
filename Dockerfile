FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（用于 mysqlclient 等）
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制项目依赖文件
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖
RUN uv sync --frozen

# 复制项目源代码（排除 .dockerignore 中的文件）
COPY . .

# 设置 Python 路径
ENV PYTHONPATH=/app

# 运行调度器
CMD ["uv", "run", "python", "-m", "src.scheduler.forex_scheduler"]
