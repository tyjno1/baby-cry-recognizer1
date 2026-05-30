# 🔧 婴儿哭声意图理解器 - Google Colab 一键构建 APK

> **前提**: 确保你已有 Google 账号。全程免费，无需本地配置任何环境。

---

## 📦 第一步：上传项目文件到 Google Drive

1. 打开 [Google Drive](https://drive.google.com)
2. 将 `android_app_build.zip`（位于项目根目录）**上传到 Google Drive 根目录**
3. 确认文件名是 `android_app_build.zip`

---

## 🚀 第二步：运行 Colab 构建

打开 [Google Colab](https://colab.research.google.com/)，**依次执行以下单元格**：

### Cell 1：挂载 Google Drive & 解压项目

```python
from google.colab import drive
drive.mount('/content/drive')

import zipfile, os
with zipfile.ZipFile('/content/drive/MyDrive/android_app_build.zip', 'r') as zf:
    zf.extractall('/content/android_app')

os.chdir('/content/android_app')
print("项目文件:")
for f in sorted(os.listdir('.')):
    print(f"  {f}")
```

### Cell 2：安装 Buildozer 及系统依赖

```python
!sudo apt update -qq
!sudo apt install -y -qq python3-pip openjdk-17-jdk git autoconf libtool     pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev     libtinfo5 cmake libffi-dev libssl-dev unzip
!pip install --quiet buildozer cython
!buildozer --version
```

### Cell 3：构建 APK（约 20-30 分钟）

```python
import os, time

spec_path = '/content/android_app/buildozer.spec'
with open(spec_path, 'r') as f:
    spec = f.read()
if 'android.gradle_version' not in spec:
    spec += '\nandroid.gradle_version = 8.4'
with open(spec_path, 'w') as f:
    f.write(spec)

print("开始构建 APK，请耐心等待...")
start = time.time()
!buildozer android debug
elapsed = time.time() - start
print(f"\n构建耗时: {elapsed:.0f} 秒")
!find . -name "*.apk" -ls 2>/dev/null
```

### Cell 4：下载 APK

```python
from google.colab import files
import glob

apks = glob.glob('bin/*.apk')
if apks:
    print(f"下载 APK: {apks[0]}")
    files.download(apks[0])
else:
    print("未找到 APK，请检查构建日志")
```

---

## 📱 安装到手机

1. 下载 APK 后传到 Android 手机
2. 在手机「设置 → 安全」中开启「允许安装未知来源应用」
3. 点击 APK 文件安装
4. 首次打开会请求录音权限，点击「允许」
