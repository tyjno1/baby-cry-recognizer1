# 👶 婴儿哭声意图理解器 - Android APK

## 技术栈

- **UI**: [Flet](https://flet.dev)（基于 Flutter 的 Python UI 框架）
- **构建**: `flet build apk`（一行命令打包 APK）
- **Python 嵌入**: serious_python（稳定可靠，无需手动管理 NDK/recipe 版本）

## 📂 文件结构

```
flet_app/
├── main.py           # Flet 主程序（UI + 业务逻辑）
├── config.py         # 配置
├── database.py       # SQLite 数据库
├── audio_processor.py # 音频特征提取
├── ai_client.py      # DeepSeek AI 客户端
├── requirements.txt  # Python 依赖
└── README.md
```

## 🚀 构建 APK

### 方式一：GitHub Actions（推荐，零配置）

1. 将项目推送到 GitHub
2. 进入 Actions → Build Android APK → Run workflow
3. 等待约 15 分钟，下载 artifact 中的 APK

### 方式二：本地构建

```bash
# 1. 安装依赖
pip install flet numpy openai scikit-learn python-dotenv serious_python

# 2. 安装 Flutter SDK
# https://docs.flutter.dev/get-started/install

# 3. 配置 Android SDK
# 设置 ANDROID_HOME 环境变量

# 4. 安装 Android SDK 组件
sdkmanager "platforms;android-34" "build-tools;34.0.0"

# 5. 构建
cd flet_app
flet build apk --verbose

# APK 输出在 build/apk/ 目录
```

### 方式三：Google Colab

```python
# Cell 1: 安装环境
!sudo apt update -qq
!sudo apt install -y -qq openjdk-17-jdk
!pip install flet numpy openai scikit-learn python-dotenv serious_python

# Cell 2: 安装 Flutter
!git clone https://github.com/flutter/flutter.git /opt/flutter
import os; os.environ["PATH"] += ":/opt/flutter/bin"
!flutter config --no-analytics
!flutter precache

# Cell 3: 安装 Android SDK
!mkdir -p /opt/android-sdk
!wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
!unzip -q commandlinetools-linux-11076708_latest.zip -d /opt/android-sdk/cmdline-tools
!mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest
os.environ["ANDROID_HOME"] = "/opt/android-sdk"
!yes | /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses
!/opt/android-sdk/cmdline-tools/latest/bin/sdkmanager "platforms;android-34" "build-tools;34.0.0"

# Cell 4: 构建
os.chdir('/content/drive/MyDrive/baby_cry_recognizer/flet_app')
!flet build apk --verbose

# Cell 5: 下载
from google.colab import files
files.download('build/apk/app-release.apk')
```

## 📱 安装到手机

1. 将 APK 传到 Android 手机
2. 设置 → 安全 → 允许安装未知来源应用
3. 点击安装
4. 打开后配置 DeepSeek API Key

## 🆚 与 Buildozer/Kivy 方案对比

| | Buildozer + Kivy | Flet + serious_python |
|---|---|---|
| 构建命令 | 复杂 | `flet build apk` |
| 版本兼容 | 经常冲突 | 自动管理 |
| NDK 管理 | 手动 | 自动 |
| Recipe 问题 | 常见 | 不存在 |
| 构建速度 | 慢(全量编译) | 快(预编译) |
| 维护状况 | 老旧 | 活跃 |
