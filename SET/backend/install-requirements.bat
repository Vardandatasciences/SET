@echo off
echo Installing Python dependencies...
echo.

REM Try to install with pre-built wheels first
echo Attempting to install with pre-built wheels (no compilation required)...
pip install --only-binary :all: -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation with pre-built wheels failed. Trying alternative method...
    echo.
    pip install --upgrade pip
    pip install wheel
    pip install -r requirements.txt
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation still failed. Trying Windows-specific requirements...
    echo.
    pip install -r requirements-windows.txt
)

echo.
echo Installation complete!
pause

