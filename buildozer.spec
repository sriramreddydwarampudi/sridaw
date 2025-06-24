[app]
title = SriDAW
package.name = sridaw
package.domain = org.sridaw
source.dir = .
version = 0.1
requirements = python3==3.9.9,kivy==2.0.0,music21,setuptools,android
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.arch = armeabi-v7a
orientation = landscape
p4a.branch = master
android.api = 30
android.minapi = 21
android.sdk = 24
android.ndk = 19c
android.gradle_dependencies = 'com.android.support:multidex:1.0.3'
