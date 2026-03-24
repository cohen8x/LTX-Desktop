@echo off
echo =================================================
echo    Starting LTX-Desktop Local Client (Windows)
echo =================================================

:: 1. Configure the IP and Port of your Linux Cloud Server here
:: Make sure this perfectly matches the IP of where you ran start_cloud_server.sh
set "LTX_CLOUD_URL=http://117.50.248.201:8000"

echo Using Cloud Server: %LTX_CLOUD_URL%
echo Booting Electron Frontend and Local Proxy...

:: 2. Boot the app. The python-backend.ts will automatically read LTX_CLOUD_URL
:: and pass it down to your local proxy_server.py
pnpm dev
