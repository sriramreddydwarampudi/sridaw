[app]
title = SriDAW
package.name = sridaw
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mid
version = 1.0
orientation = portrait
fullscreen = 1

# Main entry file
entrypoint = sridaw_final_fixed.py

# Requirements
requirements = python3,kivy,music21,pygame

# Optional: Reduce size by stripping music21 if needed
# requirements = python3,kivy,pygame

[buildozer]
log_level = 2
warn_on_root = 1
