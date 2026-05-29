FROM python:3.11-slim AS base

LABEL org.opencontainers.image.source="https://github.com/Adsryen/GitPorter"
LABEL org.opencontainers.image.description="GitPorter - Git 代码仓批量迁移工具"

# 环境变量优化
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GIT_TERMINAL_PROMPT=0

# 安装 git
RUN apt-get update \
    && apt-get install -y --no-install-recommends git openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码并安装
COPY . .
RUN pip install --no-cache-dir . \
    && rm -rf /app/.git

# 缓存目录（增量同步用）
VOLUME ["/app/.gitporter"]

ENTRYPOINT ["gitporter"]
CMD ["sync", "-y"]
