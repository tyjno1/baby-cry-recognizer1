# 🔧 Android APK 构建指南

## 📁 项目结构

```
android_app/
├── main.py                  # Kivy 主程序（替代了 Streamlit UI）
├── android_audio.py         # Android 原生录音模块（基于 AudioRecord API）
├── config.py                # 全局配置
├── database.py              # SQLite 数据库管理
├── audio_processor.py       # 音频特征提取
├── ai_client.py             # DeepSeek AI 客户端
├── buildozer.spec           # Buildozer 打包配置
├── requirements_android.txt # Android 平台依赖
└── BUILD_GUIDE.md           # 本文档
```

## 🛠️ 构建方式一：使用 WSL2 + Buildozer（推荐，Windows 用户）

### 1. 安装 WSL2 Ubuntu

```powershell
# 在 PowerShell（管理员）中运行：
wsl --install -d Ubuntu-22.04
```

### 2. 在 WSL 中安装 Buildozer

```bash
# 进入 WSL
wsl

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Buildozer 依赖
sudo apt install -y python3-pip python3-dev build-essential git \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev \
    openjdk-17-jdk

# 安装 Buildozer
pip3 install --user buildozer cython

# 将 ~/.local/bin 加入 PATH
echo 'export PATH=${HOME}/.local/bin:${PATH}' >> ~/.bashrc
source ~/.bashrc
```

### 3. 复制项目到 WSL

```bash
# 在 WSL 中，复制项目到 Linux 文件系统
cp -r /mnt/f/coding/babylijie/baby_cry_recognizer ~/baby_cry_recognizer
cd ~/baby_cry_recognizer/android_app
```

### 4. 构建 APK

```bash
# 首次构建（会下载 SDK、NDK 等，约需 10-20 分钟）
buildozer android debug

# 后续构建
buildozer android debug

# 构建 release 版本（需要签名）
buildozer android release
```

### 5. 获取 APK

构建成功后，APK 会生成在：
```
~/baby_cry_recognizer/android_app/bin/babycryrecognizer-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

---

## 🏗️ 构建方式二：使用 GitHub Actions（云端构建）

创建 `.github/workflows/build_apk.yml`：

```yaml
name: Build Android APK
on: [push, workflow_dispatch]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Buildozer
        run: |
          sudo apt update
          sudo apt install -y python3-pip openjdk-17-jdk
          pip3 install --user buildozer

      - name: Copy source files
        run: |
          cd baby_cry_recognizer/android_app
          cp ../config.py .
          cp ../database.py .
          cp ../audio_processor.py .
          cp ../ai_client.py .

      - name: Build APK
        run: |
          cd baby_cry_recognizer/android_app
          ~/.local/bin/buildozer android debug

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: baby-cry-apk
          path: baby_cry_recognizer/android_app/bin/*.apk
```

---

## 🏗️ 构建方式三：使用 Google Colab

在 Colab Notebook 中运行以下代码：

```python
# Cell 1: 安装 Buildozer
!sudo apt update
!sudo apt install -y python3-pip openjdk-17-jdk git autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev cmake libffi-dev libssl-dev
!pip install buildozer cython

# Cell 2: 克隆项目
!git clone <your-repo-url> baby_cry_recognizer
# 或者从 Google Drive 挂载
# from google.colab import drive
# drive.mount('/content/drive')

# Cell 3: 构建
import os
os.chdir('/content/baby_cry_recognizer/android_app')
!buildozer android debug

# Cell 4: 下载 APK
from google.colab import files
!ls bin/
files.download('bin/babycryrecognizer-*.apk')
```

---

## ⚠️ 常见问题

### 1. 录音权限
首次运行 APK 时，系统会弹窗请求录音权限，请点击「允许」。

### 2. API Key 配置
在应用内的设置区域输入你的 DeepSeek API Key。

### 3. 首次构建慢
首次构建需要下载 Android SDK (~1GB)、NDK (~1GB) 和编译 Python 及依赖库，约需 15-30 分钟。

### 4. 构建失败排查
```bash
# 清理缓存后重试
buildozer android clean
buildozer android debug

# 查看详细日志
buildozer android debug 2>&1 | tee build.log
```

### 5. 关于 librosa
Android 上无法直接使用 `librosa` 和 `sounddevice`，因此：
- 录音使用 Android 原生 `AudioRecord` API（通过 `pyjnius`）
- 特征提取自动回退到纯 numpy 实现

---

## 📱 安装测试

1. 将 APK 复制到 Android 手机
2. 打开「设置 → 安全 → 允许安装未知来源应用」
3. 点击 APK 文件安装
4. 打开应用，配置 API Key，开始使用！

---

## 🎯 与 Streamlit 原版的功能对比

| 功能 | Streamlit 版 | Kivy/Android 版 |
|------|-------------|-----------------|
| 录音分析 | ✅ sounddevice | ✅ Android AudioRecord |
| 特征提取 | ✅ librosa/numpy | ✅ numpy（自动回退） |
| DeepSeek AI | ✅ | ✅ |
| 本地历史匹配 | ✅ | ✅ |
| 反馈纠错 | ✅ | ✅ |
| 行为选择 | ✅ | ✅ |
| 参考资料 | ✅ | ✅ |
| 反馈历史 | ✅ | ✅ |
| 云端部署 | ✅ Docker | ❌ |
