@echo off
REM Build NeuralGui executable using the local virtual environment.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo ERROR: Virtual environment not found at .venv\Scripts\activate.bat
    echo Please activate your venv manually or create it first.
    pause
    exit /b 1
)

echo Building NeuralGui with PyInstaller...
python -m PyInstaller --clean --noconfirm NeuralGui.spec

if errorlevel 1 (
    echo.
    echo BUILD FAILED.
    pause
    exit /b 1
)
echo.
echo BUILD SUCCEEDED.
echo Executable generated at dist\NeuralGui.exe
pause
