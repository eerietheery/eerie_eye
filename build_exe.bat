@echo off
REM Build Eerie Eye 2.1 as a Windows executable using PyInstaller
REM Run this from the project root

REM Install PyInstaller if not present
pip install pyinstaller

REM Build the exe (single folder, with icon if you have one)
pyinstaller --noconfirm --clean --onefile --windowed --name "EerieEye2.1" main.py

REM Output will be in the dist\EerieEye2.1 folder
pause
