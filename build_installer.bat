@echo off
echo ========================================
echo   Html To Video Pixie v1.0.0 Build Script
echo ========================================

REM Clean old files
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist installer_build rmdir /s /q installer_build
if exist *.spec del *.spec

echo.
echo [1/2] Building main program...
pyinstaller --onefile --windowed --name "HtmlToVideoPixie" ^
    --icon logo.ico ^
    --add-data "logo.png;." ^
    --add-data "logo.ico;." ^
    --add-data "config;config" ^
    --add-data "ffmpeg.exe;." ^
    main_tkinter.py

if errorlevel 1 (
    echo Main program build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Building installer (with all files)...
pyinstaller --onefile --windowed --name "HtmlToVideoPixieInstaller" ^
    --icon logo.ico ^
    --add-data "logo.png;." ^
    --add-data "logo.ico;." ^
    --add-data "README.md;." ^
    --add-data "LICENSE;." ^
    --add-data "config;config" ^
    --add-data "core;core" ^
    --add-data "dist\HtmlToVideoPixie.exe;." ^
    --add-data "ffmpeg.exe;." ^
    installer.py

if errorlevel 1 (
    echo Installer build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Organizing output files...

REM Create installer_build directory
mkdir installer_build

REM Copy installer only
copy dist\HtmlToVideoPixieInstaller.exe installer_build\

REM Clean build directories
rmdir /s /q build
rmdir /s /q dist
del *.spec 2>nul

echo.
echo ========================================
echo   Build completed!
echo   Output: installer_build\HtmlToVideoPixieInstaller.exe
echo ========================================
echo.
pause
