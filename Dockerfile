# 选择轻量 Python 基础镜像
FROM python:3.10-slim-bullseye

# 安装系统级依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 创建工作目录和缓存目录
RUN mkdir -p /sandbox /tmp/pip_cache /tmp/sandbox/output

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_CACHE_DIR=/tmp/pip_cache

# 升级 pip
RUN pip install --upgrade pip setuptools wheel \
    -v $(pwd)/output:/sandbox/output

# 创建非root用户
#RUN useradd -m sandboxuser
#USER sandboxuser

# 设置工作目录
WORKDIR /sandbox