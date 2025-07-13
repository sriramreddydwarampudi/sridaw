[app]

# Basic app information
title = SriDAW
package.name = sridaw
package.domain = org.example
source.dir = .
version = 1.0
orientation = portrait

# Requirements with pinned versions for stability
requirements = 
    python3,
    kivy==2.3.0,
    pygments,
    music21==8.1.0,
    numpy==1.24.4,
    matplotlib==3.7.4,
    jnius,
    android,
    setuptools,
    chardet,
    joblib,
    more-itertools,
    webcolors,
    requests,
    urllib3

# Additional files to include
source.include_exts = py,png,jpg,kv,atlas,ttf

# Android specific configuration
[android]
# SDK versions
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 24

# Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET,RECORD_AUDIO

# Required libraries
android.add_libs_armeabi_v7a = libfluidsynth.so,libopenblas.so,libgfortran.so
android.add_libs_arm64_v8a = libfluidsynth.so,libopenblas.so,libgfortran.so
android.add_libs_x86 = libfluidsynth.so,libopenblas.so,libgfortran.so
android.add_libs_x86_64 = libfluidsynth.so,libopenblas.so,libgfortran.so

# Gradle dependencies
android.gradle_dependencies =
    implementation 'org.jetbrains.kotlin:kotlin-stdlib:1.8.0'

# Matplotlib backend configuration
android.env_vars = MPLBACKEND=agg

# Entry point
[app.android.entrypoint]
main = main:Music21DAW().run()

# Buildozer settings
[buildozer]
log_level = 2
warn_on_root = 1

# Exclude patterns
[app:source.exclude_patterns]
license
images/
doc/
*.pyc
*.pyo
*.pyd
.git
.gitignore
