# 操作演练说明：LTX-Desktop 的端云分离

关于分离前端与本地 Python 后端、以及绕开本地硬件检查的计划，我已经完成了具体的代码实现。

## 作出的更改

### 前端自定义后端配置

- **修改的文件：** [python-backend.ts](file:///c:\prj\gith\LTX-Desktop\electron\python-backend.ts)
- **更改内容：** 强化了 Electron 后端管理模块，允许跳过本地 Python 进程的创建步骤。通过引入 `external` (外部) 控制状态，应用在后端启动时将检查 `LTX_EXTERNAL_BACKEND_URL` 环境变量。如果提供了该变量，进程会立刻报告自身为“存活 (alive)”状态，并将界面挂钩到指定的 URL，同时附带可选的鉴权令牌 (`LTX_AUTH_TOKEN`, `LTX_ADMIN_TOKEN`)，从而运行在纯粹的独立客户端模式下。

### 绕过后端硬件检查

- **修改的文件：** [ltx2_server.py](file:///c:\prj\gith\LTX-Desktop\backend\ltx2_server.py)
  - 在 `_resolve_force_api_generations()` 函数内添加了对 `LTX_FORCE_LOCAL_MODE` 环境变量的判定。只要设置了它，就会纯粹地绕过 VRAM 和 CUDA 架构算力的容量检查，解锁完整的桌面端 APP 界面——哪怕后端位于无 GPU 的机器或者远程的云端服务器上。
  - 调整了 CORS (跨域资源共享) 初始化策略，当 `LTX_HOST` 明确绑定在 `0.0.0.0` 时自动指定 `allowed_origins=["*"]`，从而允许本地应用环境或外部局域网设备无缝地进行网络通讯。

### 客户端安全策略调整

- **修改的文件：** [csp.ts](file:///c:\prj\gith\LTX-Desktop\electron\csp.ts)
- **更改内容：** 追加了相关逻辑：在侦测到设置了 `LTX_EXTERNAL_BACKEND_URL` 之后，会提取出原生主机地址，并将它强制显式注入到 Electron 的 `connect-src` 白名单内，从而避免 Chromium 渲染进程掐断对外发往外部主机的网络连线。

### 项目文档

- **修改的文件：** [CHANGELOG.md](file:///c:\prj\gith\LTX-Desktop\CHANGELOG.md) (新建/更新)
- **更改内容：** 将这些新增的环境变量与架构功能悉数录入文档。

## 验证结果

- ✔️ `pnpm typecheck` 测试已成功通过，确认并保证了新增的 TS 类型 `BackendOwnership` 集成与 Python 的语法规范（如 `os` 的各种用法）全部合法，没有静态代码分析层面的违规。

## 运行架构

为了利用好这些新功能架构，您现在可以通过以下参数来拉起您的实例：

**远程云后端启动**
```powershell
cd backend
$env:LTX_FORCE_LOCAL_MODE="1"
$env:LTX_APP_DATA_DIR="$env:APPDATA\ltx-desktop"
uv run python ltx2_server.py
```

**本地客户端启动 (指向云端)**

选项 1：使用内联(单次)环境变量
```bash
cross-env LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT> pnpm dev
```

选项 2：使用 `.env` 配置文件
您可以在项目的根目录下建立一个 `.env` 文件，这样就无需每次在命令行里手敲环境变量了：

```env
LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT>
# 如果你在自建云后端上也配置了身份验证，以下的这些 Token 令牌才需要被一并填上：
LTX_AUTH_TOKEN=<YOUR_GENERATED_TOKEN>
LTX_ADMIN_TOKEN=<YOUR_GENERATED_ADMIN_TOKEN>
```

接着只要正常运行：`pnpm dev`
