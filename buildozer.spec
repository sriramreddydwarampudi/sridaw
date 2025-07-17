[app]
title = SriDAW
package.name = sridaw
package.domain = org.example
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,md
version = 1.0
orientation = portrait
source.dir = .
requirements = python3,kivy==2.2.1,pyjnius,android
source.exclude_patterns = license,*.pyc,*.pyo,*.pyd,.git,.gitignore,.github/,build.sh,debug_tools.py,build_instructions.md,troubleshoot.py,simple_build.py,test_minimal.py,Dockerfile.build,docker_build.sh

[buildozer]
log_level = 2
warn_on_root = 1

[app.android]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.arch = arm64-v8a
android.add_src = music21
android.gradle_dependencies = 
android.java_options = -Xms512m -Xmx2048m