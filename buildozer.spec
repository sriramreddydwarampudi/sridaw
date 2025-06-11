[app]
# In buildozer.spec
android.api = 34
android.ndk = 25.1.8937393
android.sdk = 36.0.0
title = Sridaw
package.name = sridaw
package.domain = org.sridaw
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,music21
orientation = portrait
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
