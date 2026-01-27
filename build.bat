@echo off
REM Build script for creating Windows executables

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║         Search Term Filter - Build Windows Executable              ║
echo ║                                                                    ║
echo ║  Choose build type:                                                 ║
echo ║    [1] Full installer (setup wizard, recommended)                   ║
echo ║    [2] Portable executable (standalone .exe)                        ║
echo ║    [3] Both                                                          ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

set /p BUILD_TYPE="Enter choice (1-3): "

if "%BUILD_TYPE%"=="1" (
    call npm run package:installer
) else if "%BUILD_TYPE%"=="2" (
    call npm run package:portable
) else if "%BUILD_TYPE%"=="3" (
    call npm run package
) else (
    echo Invalid choice
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ✗ Build failed
    echo.
) else (
    echo.
    echo ✓ Build completed! Check the 'dist' folder for .exe files
    echo.
)

pause
