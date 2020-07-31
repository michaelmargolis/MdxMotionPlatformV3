@echo off
echo NoLimits Platform Ride Controller - Starting NoLimits...
cd /d %~dp0
start "" "D:\Program Files\NoLimits 2\64bit\nolimits2app.exe" --telemetry --vr --openpark ".\CoasterParks\MdxLogoCoaster\MdxLogoCoaster.nl2park" --openpaused
rem start  /B python platform_controller.py