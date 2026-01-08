# MaterialSearch Server - Production Dockerfile
# 支持新模块化架构和 Supabase 集成
#
# 构建参数:
#   MODEL_NAME = "OFA-Sys/chinese-clip-vit-base-patch16"
#   USE_SUPABASE = false (默认) 或 true

FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_OFFLINE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    poppler-utils \
    libmagic1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 预下载模型 (可选，减小运行时延迟)
ARG PRELOAD_MODEL=true
RUN if [ "$PRELOAD_MODEL" = "true" ]; then \
    python -c '\
from transformers import AutoModelForZeroShotImageClassification, AutoProcessor; \
AutoModelForZeroShotImageClassification.from_pretrained("OFA-Sys/chinese-clip-vit-base-patch16"); \
AutoProcessor.from_pretrained("OFA-Sys/chinese-clip-vit-base-patch16");'; \
    fi

# 复制应用代码
# 先复制变动较少的文件以利用缓存
COPY config.py main.py routes.py ./
COPY models.py database.py search.py scan.py ./
COPY process_assets.py project_manager.py utils.py ./

# 复制新模块化架构
COPY app/ ./app/

# 复制静态文件和工具
COPY static/ ./static/
COPY supabase/ ./supabase/
COPY tools/ ./tools/

# 创建数据目录
RUN mkdir -p /app/instance /app/tmp /app/backups

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 暴露端口
EXPOSE 5000

# 默认环境变量
ENV HOST=0.0.0.0
ENV PORT=5000
ENV USE_SUPABASE=false
ENV ENABLE_LOGIN=false
ENV LOG_LEVEL=INFO

# 启动命令
ENTRYPOINT ["python", "main.py"]
