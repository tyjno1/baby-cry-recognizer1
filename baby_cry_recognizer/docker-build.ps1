# 婴儿哭声识别器 - Docker 构建脚本 (PowerShell)
param(
    [string]$Tag = "latest",
    [switch]$Push,
    [string]$Registry = ""
)

$ImageName = "baby-cry-recognizer"
$FullImageName = if ($Registry) { "$Registry/$ImageName`:$Tag" } else { "$ImageName`:$Tag" }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  婴儿哭声识别器 - Docker 构建脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否安装
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "错误: Docker 未安装或未添加到 PATH"
    exit 1
}

Write-Host "正在构建镜像: $FullImageName" -ForegroundColor Yellow
Write-Host ""

# 构建 Docker 镜像
docker build -t $FullImageName .

if ($LASTEXITCODE -ne 0) {
    Write-Error "错误: Docker 构建失败"
    exit 1
}

Write-Host ""
Write-Host "✅ 镜像构建成功!" -ForegroundColor Green
Write-Host ""

# 显示镜像信息
Write-Host "镜像信息:" -ForegroundColor Cyan
docker images $FullImageName --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

Write-Host ""
Write-Host "使用方式:" -ForegroundColor Cyan
Write-Host "  1. 运行容器: docker run -p 8501:8501 -e DEEPSEEK_API_KEY=your_key $FullImageName"
Write-Host "  2. 或使用 docker-compose: docker-compose up -d"
Write-Host ""
Write-Host "访问地址: http://localhost:8501" -ForegroundColor Green

# 可选：推送到镜像仓库
if ($Push) {
    if (!$Registry) {
        Write-Warning "警告: 未指定镜像仓库地址，跳过推送"
    } else {
        Write-Host ""
        Write-Host "正在推送到镜像仓库..." -ForegroundColor Yellow
        docker push $FullImageName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 推送成功!" -ForegroundColor Green
        } else {
            Write-Error "错误: 推送失败"
        }
    }
}
