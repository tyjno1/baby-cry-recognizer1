# 婴儿哭声识别器 - Docker 部署指南

## 📋 概述

本文档介绍如何使用 Docker 将婴儿哭声识别器打包成容器镜像并部署。

## 🐳 文件说明

| 文件 | 说明 |
|------|------|
| `Dockerfile` | Docker 镜像构建配置 |
| `docker-compose.yml` | Docker Compose 部署配置 |
| `.dockerignore` | Docker 构建忽略文件列表 |
| `docker-build.ps1` | Windows PowerShell 构建脚本 |
| `docker-build.sh` | Linux/macOS Bash 构建脚本 |

## 🚀 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 1. 进入项目目录
cd baby_cry_recognizer

# 2. 配置环境变量（可选）
# 编辑 .env 文件，设置你的 DeepSeek API Key

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 访问应用
# 打开浏览器访问 http://localhost:8501
```

### 方式二：使用 Docker 命令

```bash
# 1. 构建镜像
docker build -t baby-cry-recognizer:latest .

# 2. 运行容器
docker run -d \
  --name baby-cry-recognizer \
  -p 8501:8501 \
  -e DEEPSEEK_API_KEY=your_api_key_here \
  -v $(pwd)/data:/app/data \
  baby-cry-recognizer:latest

# 3. 访问应用
# 打开浏览器访问 http://localhost:8501
```

### 方式三：使用构建脚本

**Windows (PowerShell):**
```powershell
.\docker-build.ps1 -Tag v1.0
```

**Linux/macOS (Bash):**
```bash
chmod +x docker-build.sh
./docker-build.sh --tag v1.0
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | （必填） |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | https://api.deepseek.com |
| `DEEPSEEK_MODEL` | 使用的模型 | deepseek-v4-pro |
| `MATCH_THRESHOLD` | 本地匹配阈值 | 0.85 |
| `MAX_HISTORY` | 最大历史记录数 | 1000 |

### 使用国内镜像源加速构建

如果网络较慢，可以使用国内镜像源：

```bash
# 使用清华镜像源构建
docker build \
  --build-arg USE_CN_MIRROR=true \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  -t baby-cry-recognizer:latest .
```

## 📦 导出/导入镜像

### 导出镜像为文件

```bash
# 保存镜像为 tar 文件
docker save -o baby-cry-recognizer-v1.0.tar baby-cry-recognizer:latest

# 压缩镜像文件（可选）
gzip baby-cry-recognizer-v1.0.tar
```

### 导入镜像

```bash
# 解压（如果压缩过）
gunzip baby-cry-recognizer-v1.0.tar.gz

# 加载镜像
docker load -i baby-cry-recognizer-v1.0.tar

# 运行容器
docker run -d -p 8501:8501 -e DEEPSEEK_API_KEY=your_key baby-cry-recognizer:latest
```

## 🔧 常用命令

```bash
# 查看运行中的容器
docker ps

# 查看容器日志
docker logs -f baby-cry-recognizer

# 停止容器
docker stop baby-cry-recognizer

# 启动容器
docker start baby-cry-recognizer

# 重启容器
docker restart baby-cry-recognizer

# 进入容器内部
docker exec -it baby-cry-recognizer /bin/bash

# 删除容器
docker rm -f baby-cry-recognizer

# 删除镜像
docker rmi baby-cry-recognizer:latest
```

## 🌐 部署到服务器

### 推送到 Docker Hub

```bash
# 1. 登录 Docker Hub
docker login

# 2. 标记镜像
docker tag baby-cry-recognizer:latest yourusername/baby-cry-recognizer:v1.0

# 3. 推送镜像
docker push yourusername/baby-cry-recognizer:v1.0
```

### 推送到阿里云容器镜像服务

```bash
# 1. 登录阿里云
docker login --username=your_username registry.cn-hangzhou.aliyuncs.com

# 2. 标记镜像
docker tag baby-cry-recognizer:latest registry.cn-hangzhou.aliyuncs.com/your_namespace/baby-cry-recognizer:v1.0

# 3. 推送镜像
docker push registry.cn-hangzhou.aliyuncs.com/your_namespace/baby-cry-recognizer:v1.0
```

## 📝 注意事项

1. **API Key 安全**: 请勿将包含真实 API Key 的镜像推送到公共仓库
2. **数据持久化**: 使用 `-v` 参数挂载数据卷，防止容器删除后数据丢失
3. **端口冲突**: 如果 8501 端口被占用，可以修改为其他端口，如 `-p 8080:8501`
4. **内存限制**: 建议为容器分配至少 512MB 内存

## 🔍 故障排查

### 容器无法启动

```bash
# 查看容器日志
docker logs baby-cry-recognizer

# 检查端口占用
netstat -ano | findstr 8501
```

### 构建失败

```bash
# 清理 Docker 缓存
docker builder prune

# 使用 --no-cache 重新构建
docker build --no-cache -t baby-cry-recognizer:latest .
```

### 网络问题

如果拉取基础镜像失败，可以尝试：
1. 配置 Docker 使用代理
2. 使用国内镜像源
3. 手动拉取基础镜像后再构建

## 📞 支持

如有问题，请查看项目文档或提交 Issue。
