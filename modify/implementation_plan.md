# LTX-Desktop 端云分离实施计划

本计划概述了实现端云分离所需的更改，允许前端连接到远程后端，同时绕过本地的硬件检查。

## 需要用户检查
未对默认行为引入不兼容的破坏性修改（Breaking Changes）。新行为完全是通过环境变量选择性开启的（Opt-in）。

## 拟议的更改

### Electron 主进程

#### [MODIFY] [python-backend.ts](file:///c:\prj\gith\LTX-Desktop\electron\python-backend.ts)
- **目标**：允许注入外部后端 URL 并绕过启动本地 Python 进程。
- **改动**：
  - 更新 `BackendOwnership` 类型，加入 `'external'`。
  - 在 `startPythonBackend()` 中，如果设置了 `process.env.LTX_EXTERNAL_BACKEND_URL`，则提前返回。如果已设置，则从环境变量中获取并分配 `backendUrl`、`authToken` 和 `adminToken`，将控制权类型设置为 `'external'`，并发布状态为 `'alive'`（存活）的后端健康检查结果。
  - 在 `stopPythonBackend()` 中，增加一项检查：如果 `backendOwnership === 'external'`，则直接清理状态而无需结束任何后端进程。

### Python 后端

#### [MODIFY] [ltx2_server.py](file:///c:\prj\gith\LTX-Desktop\backend\ltx2_server.py)
- **目标**：当在没有独立显卡的机器上运行后端（或希望覆盖强制策略）时，绕过将前端强制置于纯 API 模式的硬件/显存 (VRAM) 检查。
- **改动**：
  - 在 `_resolve_force_api_generations()` 中，增加对环境变量 `LTX_FORCE_LOCAL_MODE` 的检查。
  - 如果 `os.environ.get("LTX_FORCE_LOCAL_MODE") == "1"`，立刻返回 `False` 告诉前端解锁完整的本地界面，无视实际的硬件检测结果。
  - 检查 `LTX_HOST`，如果被设置为 `0.0.0.0`，则分配 `allowed_origins=["*"]`，以防止外部前端由于跨域策略被拦截。

### 安全控制配置

#### [MODIFY] [csp.ts](file:///c:\prj\gith\LTX-Desktop\electron\csp.ts)
- **目标**：允许前端绕过严格的内容安全策略 (CSP)，该策略默认从根本上禁止了非 localhost 的网络请求。
- **改动**：
  - 在运行时动态解析，并将 `process.env.LTX_EXTERNAL_BACKEND_URL`（包括 HTTP 和 WS 协议）注入到 `connect-src` 规则中。

## 验证与测试计划

### 手动验证
1. **单独启动后端**：
   - 使用 `LTX_FORCE_LOCAL_MODE=1` 独立运行 Python 后端，确保它启动并汇报 `force_api_generations=False`。
   - 命令 (PowerShell): `$env:LTX_FORCE_LOCAL_MODE="1"; $env:LTX_APP_DATA_DIR="$env:APPDATA\ltx-desktop"; cd backend; uv run python ltx2_server.py`
2. **单独启动前端**：
   - 为前端设置 `LTX_EXTERNAL_BACKEND_URL` 并指向已经剥离出去的后端。
   - 命令: `cross-env LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT> pnpm dev`
   - 或者，在项目根目录创建一个 `.env` 文件:
     
     ```env
     LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT>
     # (可选) 如果你的后端需要鉴权:
     LTX_AUTH_TOKEN=my_secret_token
     LTX_ADMIN_TOKEN=my_admin_token
     ```
     
     然后运行: `pnpm dev`
   - 验证前端能够顺利加载完整的本地 UI 界面，并且不会尝试启动 Python 的子进程。
