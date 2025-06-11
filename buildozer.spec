[app]
title = SridawApp
package.name = sridaw
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy

# This can remain 'debug' unless you're signing for release
android.arch = armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1

# IMPORTANT: Set these to prevent Buildozer downloading SDK/NDK
android.sdk_path = $ANDROIDSDK
android.ndk_path = $ANDROIDNDK

# Optional: explicitly specify NDK version
android.ndk = 25b

# Optional: skip downloading android sources and extras
android.accept_sdk_license = True
android.accept_sdk_license_repositories = true
