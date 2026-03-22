#!/bin/bash

# ========================================================
# LTX-Desktop 纯前端客户端一键启动脚本 (Ubuntu / Mac)
# ========================================================

# 1. 填入您在云端 server.sh 中配置的公网/局域网 IP
export LTX_EXTERNAL_BACKEND_URL="http://您的云端IP:8000"

# 2. 填入您与云端约定的防盗密码
export LTX_AUTH_TOKEN="my_super_secret_auth_token"
export LTX_ADMIN_TOKEN="my_super_secret_admin_token"

echo "=========================================================="
echo "🚀 正在启动 LTX-Desktop 远程轻量化瘦客户端..."
echo "🔗 接入云端后端地址: $LTX_EXTERNAL_BACKEND_URL"
echo "🔑 验证加密凭证 (Token): $LTX_AUTH_TOKEN"
echo "=========================================================="

# 切换到脚本所在的项目根目录，启动 Vite + Electron 环境
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

pnpm dev
