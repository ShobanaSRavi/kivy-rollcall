[app]
# Name of your app
title = RollCallApp

# Package name (only lowercase letters, numbers, and underscores)
package.name = rollcallapp

# Unique package domain (reverse domain style is best practice)
package.domain = org.hariom

# Source code location (default is . for current folder)
source.dir = .

# Main Python file (entry point)
source.main = main.py

# Supported orientations: landscape, portrait, all
orientation = portrait

# Version of your app
version = 1.0

# Requirements (all Python packages you use)
requirements = python3,kivy,kivymd,sqlite3,plyer,pillow

# Files to include in the APK
source.include_exts = py,kv,png,jpg,db

# Permissions (only if needed)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Target Android version
android.api = 33
android.minapi = 21
android.ndk_api = 21

# (Optional) Icon & Presplash
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

# If your app doesn’t need Internet, remove this:
# android.permissions = INTERNET

# If using full screen
fullscreen = 0

# If you want to support both ARM and x86:
android.archs = armeabi-v7a, arm64-v8a

[buildozer]
# Directory where the .apk will be stored
log_level = 2
warn_on_root = 1
