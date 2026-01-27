Write-Host "Starting Backend Server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd web/server; node index.js"

Write-Host "Starting Frontend Client..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd web/client; npm run dev"

Write-Host "App is launching in two new windows."
