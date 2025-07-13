[app]

title = Music21 DAW
package.name = music21daw
package.domain = org.yourdomain
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,mid
version = 1.0
requirements = python3,kivy==2.2.1,music21,git+https://github.com/kivy/pyjnius.git@master
android.gradle_dependencies = androidx.core:core:1.10.1
orientation = portrait
fullscreen = 0
osx.kivy_version = 2.2.1
cython_directives = language_level=3

android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 33
android.archs = arm64-v8a

# Include MIDI file handling and optional SoundFont if needed
android.allow_backup = 1

# Ensure external storage access works
android.private_storage = False
android.additional_jars = 



# For Android storage access (internal app dir or external SDCard)
android.use_android_support = True

# Avoid stripping music21 and matplotlib-related data
android.add_python_site_packages_subdirectories = True

# Optional: speed up builds
# android.disable_wheels = 0

# Extra packaging options if required
# (You can copy the `.mid` files or SoundFont here)
# source.include_patterns = assets/*

# Application icon (optional)
# icon.filename = %(source.dir)s/icon.png

[buildozer]

log_level = 2
warn_on_root = 1
