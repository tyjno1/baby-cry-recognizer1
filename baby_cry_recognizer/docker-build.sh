#!/bin/bash
# 婴儿哭声识别器 - Docker 构建脚本 (Bash)

set -e

# 默认配置
TAG="latest"
REGISTRY=""
PUSH=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -t, --tag TAG       镜像标签 (默认: latest)"
            echo "  -r, --registry URL  镜像仓库地址"
            echo "  -p, --push          构建后推送到仓库"
            echo "  -h, --help          显示帮助"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            exit 1
            ;;
    esac
done

IMAGE_NAME="baby-cry-recognizer"
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

echo "========================================"
echo "  婴儿哭声识别器 - Docker 构建脚本"
echo "========================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

echo "正在构建镜像: $FULL_IMAGE_NAME"
echo ""

# 构建镜像
docker build -t "$FULL_IMAGE_NAME" .

echo ""
echo "✅ 镜像构建成功!"
echo ""

# 显示镜像信息
echo "镜像信息:"
docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "使用方式:"
echo "  1. 运行容器: docker run -p 8501:8501 -e DEEPSEEK_API_KEY=your_key $FULL_IMAGE_NAME"
echo "  2. 或使用 docker-compose: docker-compose up -d"
echo ""
echo "访问地址: http://localhost:8501"

# 推送镜像
if [ "$PUSH" = true ] && [ -n "$REGISTRY" ]; then
    echo ""
    echo "正在推送到镜像仓库..."
    docker push "$FULL_IMAGE_NAME"
    echo "✅ 推送成功!"
fi
