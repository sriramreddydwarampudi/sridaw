[app]
title = SriDAW
package.name = sridaw
package.domain = org.example
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
requirements = python3,kivy==2.3.0,pygments,music21,numpy,matplotlib,jnius,android
orientation = portrait
osx.kivy_version = 2.3.0
source.dir = .

[buildozer]
log_level = 2
warn_on_root = 1

[app.android]
# Optional: uncomment to fix version
android.api = 30
android.minapi = 21
android.ndk = 25b
android.gradle_dependencies = 
android.sdk = 24
# Optional: increase if needed
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.add_libs_armeabi_v7a = libfluidsynth.so

# Matplotlib backend configuration
android.env_vars = MPLBACKEND=agg

[app.android.entrypoint]
main = main:Music21DAW().run()

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
