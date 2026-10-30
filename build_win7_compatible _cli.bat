@echo off
setlocal

cd /d "%~dp0"

echo Building Windows 7 compatible EXE.
echo Required: Python 3.8.x and PyInstaller 5.13.2
echo.

py -3.8 --version
if errorlevel 1 (
  echo Python 3.8 not found. Install Python 3.8.x first.
  exit /b 1
)

py -3.8 -m pip install pyinstaller==5.13.2
if errorlevel 1 exit /b 1

py -3.8 -m PyInstaller --clean --onefile^
  --name "DJI_GPX_Extractor" ^
  --icon ikona.ico ^
  --add-data "ikona.ico;." ^
  --version-file dji_gpx_extractor_version_cli.txt ^
  dji_gpx_extractor_cli.py

if errorlevel 1 exit /b 1

echo.
echo Done: dist\DJI_GPX_Extractor.exe
