[app]
title = SriDAW
package.name = sridaw
package.domain = org.sridaw
source.dir = .
source.include_exts = py,kv,wav,mp3
version = 0.1
requirements = python3,kivy==2.0.0,setuptools
orientation = landscape

[buildozer]
log_level = 2
warn_on_root = 1

[app.android]
android.api = 30
android.minapi = 21
android.sdk = 24
android.ndk = 21d
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.arch = armeabi-v7a