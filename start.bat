@echo off
cd /d "%~dp0"

echo Cleaning up node modules...
cd frontend
rmdir /s /q node_modules
del /f /q package-lock.json

echo Installing frontend dependencies...
call npm install

echo Starting CryptoTrader servers...
cd ..
python start_servers.py
pause
