@echo off
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Installing frontend dependencies...
cd frontend
npm install

echo.
echo Setup complete! You can now run start.bat to launch the application.
