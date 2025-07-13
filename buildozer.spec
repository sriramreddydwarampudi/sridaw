[app]
title = SriDAW
package.name = sridaw
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml,mid
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
android.p4a_dir = ./p4a_cache
android.allow_backup = True
android.arch = armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 24
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.add_libs_armeabi_v7a = libfluidsynth.so
android.gradle_dependencies = 
android.env_vars = MPLBACKEND=agg

[app.android.entrypoint]
main = main:Music21DAW().run()

[app:source.exclude_patterns]
*.pyc,*.pyo,*.pyd,*.git,*.md,*.txt,*.bat,*.exe
tests/,examples/,docs/,__pycache__/

[app:android.manifest.intent.filters]
android.manifest.intent_filter = <action android:name="android.intent.action.MAIN"/>
