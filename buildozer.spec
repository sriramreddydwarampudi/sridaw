[app]
title = MIDI Piano Roll
package.name = miditools
package.domain = org.midi
version = 1.0

source.dir = .
source.include_exts = py,png,npy,ogg,mid
source.include_dirs = corpus

requirements = 
    python3,
    kivy,
    music21,
    mido,
    matplotlib,
    numpy

# Permissions (optional)
android.permissions = 

# Architecture
android.archs = arm64-v8a

# Entry point
entrypoint = main.py

# Hide the title bar (optional)
fullscreen = 0

# Orientation (optional: portrait | landscape | sensor)
orientation = portrait

# Optional icon
# icon.filename = %(source.dir)s/icon.png

# Minimum Android API level (21 is safe for most)
android.minapi = 21

# Target SDK (optional but recommended)
android.api = 31

# Disable logcat spam (optional)
log_level = 2


[buildozer]
# Clean temp files between builds (optional)
# clean_build = 1

# Avoid errors related to path spaces
storage_dir = /tmp/build_storage

# Location to put the final APK
bin_dir = ./bin

# Use develop branch of python-for-android
p4a.branch = develop
