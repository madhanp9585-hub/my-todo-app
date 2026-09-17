[app]
title = My Tasks
package.name = todolistapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,setuptools
presplash.filename = %(source.dir)s/t.png
icon.filename = %(source.dir)s/t.png
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.ndk = 25b
p4a.branch = develop
android.api = 33
android.minapi = 21
