#!/bin/bash
# LTX-Desktop Cloud Backend Startup Script (Linux)

echo "================================================="
echo "   Starting LTX-Desktop Cloud Compute Server"
echo "================================================="

# 1. Bind to 0.0.0.0 to allow external connections from the Internet
export LTX_HOST="0.0.0.0"

# 2. Configure the port (Frontend/Proxy will connect to this port)
export LTX_PORT="8000"

# 3. Configure the working directory for models and outputs on the cloud
export LTX_APP_DATA_DIR="$(pwd)/ltx_cloud_data"
mkdir -p "$LTX_APP_DATA_DIR"

echo "Host: $LTX_HOST"
echo "Port: $LTX_PORT"
echo "Data Directory: $LTX_APP_DATA_DIR"
echo "Starting backend..."

# Navigate to backend and start the server using the project's 'uv' environment
cd backend
uv run python ltx2_server.py
