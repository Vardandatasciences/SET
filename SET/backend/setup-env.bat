@echo off
echo Setting up environment file for Sales Intelligence Tool...
echo.

if exist .env (
    echo .env file already exists!
    echo.
    choice /C YN /M "Do you want to overwrite it"
    if errorlevel 2 goto :end
)

echo.
echo Please enter your Perplexity API key.
echo You can get your API key from: https://www.perplexity.ai/settings/api
echo.
set /p API_KEY="Enter your Perplexity API key: "

if "%API_KEY%"=="" (
    echo.
    echo Error: API key cannot be empty!
    pause
    exit /b 1
)

(
echo PERPLEXITY_API_KEY=%API_KEY%
echo API_HOST=0.0.0.0
echo API_PORT=8000
) > .env

echo.
echo .env file created successfully!
echo.
pause

:end

