@echo off
setlocal enabledelayedexpansion
cls

REM ============================================================================
REM Search Term Filter - Windows Installation & Build Script
REM ============================================================================

set VERSION=1.0.0
set APP_NAME=Search Term Filter
set INSTALL_DIR=%cd%

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                                                                    ║
echo ║              %APP_NAME% - Installation Manager                ║
echo ║                      Version %VERSION%                                 ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Check for Node.js
echo [*] Checking prerequisites...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ✗ ERROR: Node.js is not installed or not in PATH
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo (Select "Add to PATH" during installation)
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js found: %NODE_VERSION%

npm --version >nul 2>&1
if errorlevel 1 (
    echo ✗ ERROR: npm not found
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo ✓ npm found: %NPM_VERSION%

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                    What would you like to do?                     ║
echo ╠════════════════════════════════════════════════════════════════════╣
echo ║                                                                    ║
echo ║  [1] Install dependencies (first time setup)                      ║
echo ║  [2] Debug mode (run with logging and developer tools)            ║
echo ║  [3] Build Windows executable (.exe)                              ║
echo ║  [4] Build portable executable (no installer needed)              ║
echo ║  [5] Clean and reinstall everything                               ║
echo ║  [6] Exit                                                          ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

set /p CHOICE="Enter your choice (1-6): "

if "%CHOICE%"=="1" goto install
if "%CHOICE%"=="2" goto debug
if "%CHOICE%"=="3" goto build_installer
if "%CHOICE%"=="4" goto build_portable
if "%CHOICE%"=="5" goto clean_install
if "%CHOICE%"=="6" goto end

echo Invalid choice. Please try again.
timeout /t 2
cls
goto :EOF

REM ============================================================================
REM INSTALL - Setup all dependencies
REM ============================================================================
:install
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                     Installing Dependencies                        ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

echo [1/3] Installing root dependencies...
call npm install
if errorlevel 1 (
    echo ✗ Failed to install root dependencies
    pause
    exit /b 1
)
echo ✓ Root dependencies installed

echo.
echo [2/3] Installing client dependencies...
cd web\client
call npm install
if errorlevel 1 (
    echo ✗ Failed to install client dependencies
    cd ..\..
    pause
    exit /b 1
)
echo ✓ Client dependencies installed
cd ..\..

echo.
echo [3/3] Installing server dependencies...
cd web\server
call npm install
if errorlevel 1 (
    echo ✗ Failed to install server dependencies
    cd ..\..
    pause
    exit /b 1
)
echo ✓ Server dependencies installed
cd ..\..

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║             ✓ Installation completed successfully!                 ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.
echo You can now:
echo   - Run in debug mode: install.bat (then choose option 2)
echo   - Build executable: install.bat (then choose option 3 or 4)
echo.
pause
goto :EOF

REM ============================================================================
REM DEBUG - Run in debug mode with logging and developer tools
REM ============================================================================
:debug
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                    Starting Debug Mode                             ║
echo ║                                                                    ║
echo ║  • React Dev Server on http://localhost:5173                       ║
echo ║  • Backend Server on http://localhost:3000                         ║
echo ║  • Electron with DevTools enabled                                  ║
echo ║                                                                    ║
echo ║  Press Ctrl+C to stop                                              ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo ✗ Dependencies not installed. Running install first...
    call :install
    if errorlevel 1 exit /b 1
)

REM Start debug mode
call npm run dev:electron

if errorlevel 1 (
    echo.
    echo ✗ Debug mode failed
    echo.
    echo Troubleshooting:
    echo   - Ensure ports 3000, 5173 are not in use
    echo   - Check that all dependencies are installed
    echo   - Try: npm install
    echo.
)
pause
goto :EOF

REM ============================================================================
REM BUILD INSTALLER - Create Windows installer (.exe with setup wizard)
REM ============================================================================
:build_installer
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║              Building Windows Installer (.exe setup)                ║
echo ║                                                                    ║
echo ║  This will create a professional installer with:                   ║
echo ║    • Setup wizard                                                   ║
echo ║    • Start menu shortcuts                                           ║
echo ║    • Desktop shortcut                                               ║
echo ║    • Uninstall option                                               ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

if not exist "node_modules" (
    echo ✗ Dependencies not installed. Running install first...
    call :install
    if errorlevel 1 exit /b 1
)

echo [1/4] Cleaning previous builds...
if exist "dist" rmdir /s /q dist >nul 2>&1
if exist "web\client\dist" rmdir /s /q web\client\dist >nul 2>&1
echo ✓ Cleaned

echo.
echo [2/4] Building React frontend...
cd web\client
call npm run build
if errorlevel 1 (
    echo ✗ Frontend build failed
    cd ..\..
    pause
    exit /b 1
)
cd ..\..
echo ✓ Frontend built

echo.
echo [3/4] Parsing and creating executable...
call npx electron-builder --win --nsis

if errorlevel 1 (
    echo.
    echo ✗ Build failed
    echo.
    echo Troubleshooting:
    echo   - Check that all dependencies are installed
    echo   - Ensure you have write permissions in this directory
    echo   - Try running as Administrator
    echo.
    pause
    exit /b 1
)

echo ✓ Executable created

echo.
echo [4/4] Verifying output...
if exist "dist\*.exe" (
    echo ✓ Found .exe files in dist\ folder
    echo.
    echo ╔════════════════════════════════════════════════════════════════════╗
    echo ║             ✓ Build completed successfully!                        ║
    echo ╠════════════════════════════════════════════════════════════════════╣
    echo ║                                                                    ║
    echo ║  Your installers are ready in the 'dist' folder:                  ║
    echo ║                                                                    ║
    for %%f in (dist\*.exe) do (
        echo ║    • %%~nxf
    )
    echo ║                                                                    ║
    echo ║  To install on this or another computer:                          ║
    echo ║    1. Double-click the .exe file                                   ║
    echo ║    2. Follow the setup wizard                                      ║
    echo ║    3. Launch from Start Menu or Desktop                            ║
    echo ║                                                                    ║
    echo ╚════════════════════════════════════════════════════════════════════╝
) else (
    echo ✗ No .exe files found. Build may have failed.
)

echo.
pause
goto :EOF

REM ============================================================================
REM BUILD PORTABLE - Create standalone executable (no installation)
REM ============================================================================
:build_portable
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║            Building Portable Executable (standalone)                ║
echo ║                                                                    ║
echo ║  This creates a single .exe file that:                              ║
echo ║    • Requires no installation                                        ║
echo ║    • Can be run from any location                                    ║
echo ║    • Can be run from USB drive                                       ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

if not exist "node_modules" (
    echo ✗ Dependencies not installed. Running install first...
    call :install
    if errorlevel 1 exit /b 1
)

echo [1/4] Cleaning previous builds...
if exist "dist" rmdir /s /q dist >nul 2>&1
if exist "web\client\dist" rmdir /s /q web\client\dist >nul 2>&1
echo ✓ Cleaned

echo.
echo [2/4] Building React frontend...
cd web\client
call npm run build
if errorlevel 1 (
    echo ✗ Frontend build failed
    cd ..\..
    pause
    exit /b 1
)
cd ..\..
echo ✓ Frontend built

echo.
echo [3/4] Parsing and creating portable executable...
call npx electron-builder --win --portable

if errorlevel 1 (
    echo.
    echo ✗ Build failed
    echo.
    echo Troubleshooting:
    echo   - Check that all dependencies are installed
    echo   - Ensure you have write permissions in this directory
    echo   - Try running as Administrator
    echo.
    pause
    exit /b 1
)

echo ✓ Portable executable created

echo.
echo [4/4] Verifying output...
if exist "dist\*.exe" (
    echo ✓ Found .exe files in dist\ folder
    echo.
    echo ╔════════════════════════════════════════════════════════════════════╗
    echo ║             ✓ Build completed successfully!                        ║
    echo ╠════════════════════════════════════════════════════════════════════╣
    echo ║                                                                    ║
    echo ║  Your portable executable is ready:                                ║
    echo ║                                                                    ║
    for %%f in (dist\*.exe) do (
        echo ║    • %%~nxf
    )
    echo ║                                                                    ║
    echo ║  To use:                                                           ║
    echo ║    1. Just double-click the .exe file                              ║
    echo ║    2. No installation needed!                                       ║
    echo ║    3. Can be moved to any location or USB drive                    ║
    echo ║                                                                    ║
    echo ╚════════════════════════════════════════════════════════════════════╝
) else (
    echo ✗ No .exe files found. Build may have failed.
)

echo.
pause
goto :EOF

REM ============================================================================
REM CLEAN INSTALL - Remove everything and start fresh
REM ============================================================================
:clean_install
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                     Clean Reinstall                                ║
echo ║                                                                    ║
echo ║  This will:                                                         ║
echo ║    • Delete all node_modules folders                                ║
echo ║    • Delete package-lock.json files                                 ║
echo ║    • Delete dist and build folders                                  ║
echo ║    • Reinstall everything from scratch                              ║
echo ║                                                                    ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

set /p CONFIRM="Are you sure? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    goto :EOF
)

echo.
echo [1/5] Deleting root node_modules...
if exist "node_modules" rmdir /s /q node_modules >nul 2>&1
if exist "package-lock.json" del package-lock.json >nul 2>&1
echo ✓ Deleted

echo.
echo [2/5] Deleting client node_modules...
if exist "web\client\node_modules" rmdir /s /q web\client\node_modules >nul 2>&1
if exist "web\client\package-lock.json" del web\client\package-lock.json >nul 2>&1
echo ✓ Deleted

echo.
echo [3/5] Deleting server node_modules...
if exist "web\server\node_modules" rmdir /s /q web\server\node_modules >nul 2>&1
if exist "web\server\package-lock.json" del web\server\package-lock.json >nul 2>&1
echo ✓ Deleted

echo.
echo [4/5] Deleting build artifacts...
if exist "dist" rmdir /s /q dist >nul 2>&1
if exist "web\client\dist" rmdir /s /q web\client\dist >nul 2>&1
echo ✓ Deleted

echo.
echo [5/5] Reinstalling everything...
call :install

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║             ✓ Clean reinstall completed!                           ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.
pause
goto :EOF

REM ============================================================================
REM EXIT
REM ============================================================================
:end
echo.
echo Goodbye!
echo.
exit /b 0
