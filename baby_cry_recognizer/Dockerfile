# 婴儿哭声识别器 - Docker 镜像
# 使用国内镜像源加速构建（如需官方源，可注释掉下面一行）
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置国内镜像源（可选）
ARG USE_CN_MIRROR=false
RUN if [ "$USE_CN_MIRROR" = "true" ]; then \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
        echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list; \
    fi

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libsndfile1 \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用国内镜像源加速）
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir -i $PIP_INDEX_URL -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 暴露 Streamlit 端口
EXPOSE 8501

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# 启动命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
