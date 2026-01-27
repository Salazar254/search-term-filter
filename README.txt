## Search Term Filter - Windows Desktop Application

### Quick Start (3 Steps)

#### Step 1: Install Dependencies
**Double-click:** `install.bat`
- Select option **[1] Install dependencies**
- This installs everything needed to run the app

#### Step 2: Debug Before Building
**Double-click:** `debug.bat`
- This launches the app in debug mode
- You can see all errors and logs in real-time
- Press `Ctrl+C` to stop

#### Step 3: Build Windows Executable
**Double-click:** `install.bat`
- Select option **[3] Build Windows executable** or **[4] Build portable executable**
- The .exe file will be created in the `dist/` folder
- Ready to share with others!

---

### All Available Commands

| File | Purpose |
|------|---------|
| `install.bat` | Main installation and management tool (all-in-one) |
| `debug.bat` | Quick debug launcher |
| `build.bat` | Quick build launcher |

---

### install.bat Options

1. **Install dependencies** - First time setup only
2. **Debug mode** - Run with developer tools and logging
3. **Build Windows installer** - Creates professional installer (.exe with setup wizard)
4. **Build portable executable** - Creates standalone .exe (no installation needed)
5. **Clean and reinstall** - Start fresh (deletes all dependencies)
6. **Exit**

---

### Understanding the Files

```
search-term-filter/
├── install.bat           ← Main installation tool (double-click this!)
├── debug.bat            ← Quick debug launcher
├── build.bat            ← Quick build launcher
├── web/
│   ├── main.js          ← Electron main process
│   ├── preload.js       ← Security bridge
│   ├── client/          ← React frontend
│   └── server/          ← Node.js backend
├── src/                 ← Python backend
├── package.json         ← Dependencies and build scripts
└── electron-builder.json5 ← Windows build configuration
```

---

### Workflow Examples

**First Time Setup:**
```
1. Double-click install.bat
2. Choose option [1]
3. Wait for completion
```

**Testing Before Release:**
```
1. Double-click debug.bat
2. Test the app
3. Press Ctrl+C to stop
4. Fix any issues
5. Repeat
```

**Creating Installer for Distribution:**
```
1. Double-click install.bat
2. Choose option [3] for professional installer
   (or option [4] for portable standalone .exe)
3. Find .exe files in the dist/ folder
4. Share the .exe with users
```

---

### Build Outputs

After building, you'll find in the `dist/` folder:

**Option 3 - Full Installer:**
- `Search Term Filter Setup 1.0.0.exe` - Professional installer
  - Includes setup wizard
  - Creates Start Menu shortcuts
  - Creates Desktop shortcut
  - Includes uninstaller

**Option 4 - Portable Executable:**
- `Search Term Filter 1.0.0.exe` - Standalone executable
  - No installation required
  - Can run from USB drive
  - Can run from any location

---

### Troubleshooting

**"Node.js is not installed"**
- Download and install from: https://nodejs.org/
- Make sure to check "Add to PATH" during installation
- Restart your computer after installing

**"Port 3000 or 5173 already in use"**
- Another app is using these ports
- Close other applications or restart your computer
- Or edit `web/server/index.js` and `web/client/vite.config.ts` to use different ports

**"Debug mode crashes or shows errors"**
- This is expected during development! See the error messages
- Fix the code that's causing the error
- Save the file and the app will auto-reload
- If it doesn't reload, stop (Ctrl+C) and start debug again

**"Build fails with 'command not found'"**
- Make sure dependencies are installed (run install.bat option 1)
- Try Clean and Reinstall (option 5)

**Permission Denied Errors**
- Try running `install.bat` as Administrator
- Right-click install.bat → "Run as administrator"

---

### Advanced Usage

**For Developers:**
- Edit `web/main.js` to customize the desktop window
- Edit `electron-builder.json5` to change installer appearance
- Edit `web/client/src/` for React frontend changes
- Edit `web/server/index.js` for backend API changes

**Custom Icon:**
1. Create a 256x256 pixel icon as `icon.ico`
2. Place it in the project root folder
3. Edit `electron-builder.json5` and add: `"icon": "icon.ico"`
4. Rebuild with `install.bat` option 3

**Change App Name:**
1. Edit `electron-builder.json5`
2. Change `"productName": "Search Term Filter"` to your desired name
3. Rebuild

---

### How It Works

1. **Electron Framework** - Wraps your React app as a Windows desktop application
2. **React Frontend** - Your user interface (built with Vite)
3. **Node.js Backend** - API server and business logic
4. **electron-builder** - Automatically packages everything into a .exe installer
5. **Parse** - The build process compiles all components together

---

### System Requirements for End Users

Once built, your app requires:
- Windows 7 or later (for 32-bit) or Windows 8+ (for 64-bit)
- ~300MB disk space
- No Node.js or Python installation needed (bundled in app)

---

### Need Help?

- **General Questions:** Read the comments in `install.bat`
- **React Issues:** https://react.dev/
- **Electron Issues:** https://www.electronjs.org/docs
- **Node.js Issues:** https://nodejs.org/docs/

---

**Created:** January 27, 2026  
**Status:** Ready for development and distribution ✓
