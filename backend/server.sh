#!/bin/bash

# 自动获取当前 server.sh 脚本所在的 backend 目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 因为 downmodel.sh 存放在 ../modify/ 中，下载的模型被放入了 ../modify/models
# 后端寻找模型的逻辑是 LTX_APP_DATA_DIR/models，因此只需要将 LTX_APP_DATA_DIR 指向 modify 即可
export LTX_APP_DATA_DIR="$(cd "$SCRIPT_DIR/../modify" && pwd)"

# 强制解锁本地模式，禁用本地硬件限制
export LTX_FORCE_LOCAL_MODE="1"

# 允许外网访问，绑定到 0.0.0.0
export LTX_HOST="0.0.0.0"

# 指定暴露的端口号
export LTX_PORT="8000"

# 设置接口调用身份验证 (强烈建议保留并修改为您自己的密码)
export LTX_AUTH_TOKEN="my_super_secret_auth_token"
export LTX_ADMIN_TOKEN="my_super_secret_admin_token"

echo "==========================================="
echo "🚀 正在启动 LTX-Desktop 远程云端后端服务..."
echo "📂 模型检索目录定位于: $LTX_APP_DATA_DIR"
echo "==========================================="

# 使用项目的 uv 虚拟环境启动 FastAPI 服务器
uv run python "$SCRIPT_DIR/ltx2_server.py"
