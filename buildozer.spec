[app]
title = IP Rotator AR
package.name = iprotator
package.domain = org.example
source.dir = .
source.include_exts = py,txt,png,jpg,atlas
version = 2.0
requirements = python3,kivy==2.3.0,requests,urllib3,chardet,idna,certifi,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,CAMERA,ACCESS_FINE_LOCATION,ACCESS_WIFI_STATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
android.release_artifact = iprotator
p4a.branch = master