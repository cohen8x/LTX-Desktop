# ========================================================
# LTX-Desktop 纯前端客户端一键启动脚本 (Windows 11)
# 运行前请右键该文件 -> 使用 PowerShell 运行，或在终端里敲入 .\start-client.ps1
# ========================================================

# 1. 填入您在云端 server.sh 中配置的公网/局域网 IP
$env:LTX_EXTERNAL_BACKEND_URL = "http://117.50.248.201:8000"

# 2. 填入您与云端约定的防盗密码
$env:LTX_AUTH_TOKEN = "my_super_secret_auth_token"
$env:LTX_ADMIN_TOKEN = "my_super_secret_admin_token"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🚀 正在启动 LTX-Desktop 远程轻量化瘦客户端..." -ForegroundColor Green
Write-Host "🔗 接入云端后端地址: $env:LTX_EXTERNAL_BACKEND_URL" -ForegroundColor Yellow
Write-Host "🔑 验证加密凭证 (Token): $env:LTX_AUTH_TOKEN" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 返回本脚本所在的项目主目录
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
Set-Location -Path $ScriptDir

# 启动底层框架与界面
pnpm dev
