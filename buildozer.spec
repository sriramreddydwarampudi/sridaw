[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy
orientation = portrait
osx.kivy_version = 2.3.0

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
android.permissions = INTERNET

# Optional: uncomment if your app needs to stay awake, etc.
# android.permissions = INTERNET,WAKE_LOCK

# Optional: if using Java modules
# android.add_jars = libs/my-lib.jar

# Optional: icon and presplash
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/splash.png
