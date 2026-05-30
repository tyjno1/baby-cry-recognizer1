# Cell 1: 挂载 Google Drive & 解压项目
from google.colab import drive
drive.mount('/content/drive')

import zipfile, os
with zipfile.ZipFile('/content/drive/MyDrive/android_app_build.zip', 'r') as zf:
    zf.extractall('/content/android_app')

os.chdir('/content/android_app')
print("项目文件:")
for f in sorted(os.listdir('.')):
    print(f"  {f}")

# Cell 2: 安装 Buildozer 及系统依赖
!sudo apt update -qq
!sudo apt install -y -qq python3-pip openjdk-17-jdk git autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev unzip
!pip install --quiet buildozer cython
!buildozer --version
print("环境准备完成")

# Cell 3: 修复 spec & 构建 APK（约 20-30 分钟）
import os, time

spec_path = '/content/android_app/buildozer.spec'
# utf-8-sig 自动处理 BOM 头
with open(spec_path, 'r', encoding='utf-8-sig') as f:
    spec = f.read()

if 'android.gradle_version' not in spec:
    spec += '\nandroid.gradle_version = 8.4'

with open(spec_path, 'w', encoding='utf-8') as f:
    f.write(spec)

print("开始构建 APK（约 20-30 分钟）...")
start = time.time()
!buildozer android debug
elapsed = time.time() - start
print(f"构建耗时: {elapsed:.0f} 秒")
!find . -name "*.apk" -ls 2>/dev/null

# Cell 4: 下载 APK
from google.colab import files
import glob

apks = glob.glob('bin/*.apk')
if apks:
    size_mb = os.path.getsize(apks[0]) / 1024 / 1024
    print(f"下载 APK: {apks[0]} ({size_mb:.1f} MB)")
    files.download(apks[0])
else:
    print("未找到 APK，请检查构建日志")
