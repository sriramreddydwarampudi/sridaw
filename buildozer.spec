[app]
title = SriDAW
package.name = sridaw
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
requirements = 
    python3,
    kivy==2.3.0,
    pygments,
    music21==9.1.0,
    numpy,
    matplotlib,
    jnius,
    android,
    chardet,
    webcolors,
    setuptools,
    certifi,
    urllib3
orientation = portrait
osx.kivy_version = 2.3.0

[buildozer]
log_level = 2
warn_on_root = 1

# Corrected source directory setting
p4a.source_dir = ./p4a_cache

[app:android]
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 24
# Corrected architecture setting
android.archs = arm64-v8a,armeabi-v7a
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.add_libs_armeabi_v7a = libfluidsynth.so
android.gradle_dependencies = 
android.env_vars = MPLBACKEND=agg

[app.android.entrypoint]
main = main:Music21DAW().run()

[app:source.exclude_patterns]
license
images/
doc/
*.pyc
*.pyo
*.pyd
.git
.gitignore
