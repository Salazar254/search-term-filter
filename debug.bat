@echo off
REM Quick debug launcher for Search Term Filter
REM This script starts the app in debug mode with logging and developer tools

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║            Search Term Filter - Debug Mode                         ║
echo ║                                                                    ║
echo ║  Starting with:                                                     ║
echo ║    • React Dev Server: http://localhost:5173                        ║
echo ║    • Backend Server: http://localhost:3000                          ║
echo ║    • Electron DevTools enabled                                      ║
echo ║                                                                    ║
echo ║  Press Ctrl+C to stop debugging                                     ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo ✗ Dependencies not installed
    echo.
    echo Run: install.bat
    echo Then choose option [1] Install dependencies
    echo.
    pause
    exit /b 1
)

REM Run debug mode
call npm run dev:electron

if errorlevel 1 (
    echo.
    echo ✗ Debug mode exited with error
    echo.
)

pause
