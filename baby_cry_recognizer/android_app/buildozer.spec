[app]
title = 婴儿哭声意图理解器
package.name = babycryrecognizer
package.domain = com.babylijie
source.dir = android_app
source.include_exts = py,png,jpg,kv,atlas,db
source.exclude_exts = spec
source.exclude_dirs = venv,__pycache__,.venv
version = 1.0.0
orientation = portrait
android.permissions = INTERNET,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.features = android.hardware.microphone
android.api = 33
android.minapi = 26
android.sdk = 33
android.ndk = 25b
android.private_storage = True
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity
p4a.bootstrap = sdl2
android.archs = arm64-v8a,armeabi-v7a
android.androidx = True
android.gradle_version = 8.4
requirements = python3,kivy,numpy,scikit-learn,openai,python-dotenv,pyjnius,android

[buildozer]
log_level = 2
warn_on_root = 1