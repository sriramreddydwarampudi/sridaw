[app]
title = SriDAW
package.name = sridaw
package.domain = org.example
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
orientation = portrait
source.dir = .
requirements = python3,kivy==2.2.1,pyjnius

[buildozer]
log_level = 2
warn_on_root = 1

[app:source.exclude_patterns]
# Exclude unnecessary files
license
images/
doc/
*.pyc
*.pyo
*.pyd
.git
.gitignore
.github/

[app.android]
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 30
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.gradle_dependencies = 
android.add_libs_armeabi_v7a = 
android.env_vars = MPLBACKEND=agg