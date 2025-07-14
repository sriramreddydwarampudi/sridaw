[app]

title = Music21DAW
package.name = music21daw
package.domain = org.kivy.music21
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,mid
version = 1.0
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 1
android.api = 33
android.minapi = 24
android.target = 33
android.ndk = 25b
android.ndk_api = 33

# Permissions for saving/loading files
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Include MIDI output
android.add_jars = 
android.add_assets = assets/

# Force pip install of music21 (no wheels)
p4a.extra_args = --extra-pip-args="--no-deps"

# If you're using custom fonts
# android.presplash = presplash.png

# Keep default launcher icon
# icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
