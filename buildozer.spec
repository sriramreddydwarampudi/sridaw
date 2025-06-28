[app]
title = Music21DAW
package.name = music21daw
package.domain = org.sriram
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,wav,mp3
version = 1.0
requirements = python3,kivy==2.3.0,music21,pygame,pygments
orientation = landscape
fullscreen = 1
entrypoint = mu.py

# Permissions (pygame playback might need audio)
android.permissions = INTERNET

# Android settings
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.arch = arm64-v8a

# Optional: icon
icon.filename = %(source.dir)s/icon.png

# Avoid asking yes/no during GitHub Actions
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
pip_upgrade = true
