# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### 修复与增强 (Fixed & Enhanced)
- **修复 Electron 底层废弃的物理路径读取Bug**：原项目依赖了较新版本的 Electron (v31+)，由于较强沙箱隔离策略，官方早就废除了拖拽原生 `file.path` 的强访问权限。这导致原本的音频/视频/图片上传总是退化成虚假的假路径（如 `./file.jpg`）进而找不到文件报错。我们利用 `electron/preload.ts` 暴露了官方专门弥盖的特权级接口 `webUtils.getPathForFile`，重构替换了三大文件选取组件，彻底根治了这个埋藏极深的历史遗留拖拽 Bug。
- **重构进度返回载体机制**：修改了云端的 `api_types.py` 与 `generation_handler.py` 的查询接口。现在只要渲染步骤抵达 `100% complete`，不仅返回进度条数据，还会一并抛出底包的 `video_path` 物理坐标供云端到代理的长距精准轮询与收割。
- **代理层的 NAT 掉线生死守护机制 (Fallback Long-Polling)**：原代理发起的同步阻塞 `POST /api/generate` 渲染指令耗时近 5 分钟，在这种长空闲等待期中，请求极易被路由器或宽带运营商 ISP 墙防火墙作僵尸丢包强杀。现在即便最初的原生 `POST` 物理连接被残忍打断中断，`proxy_server.py` 内部会自动无缝退化成高频的长轮询探测状态。不管链路如何断裂，只要云端进度达到百分百，它就能在茫茫星海中把这段视频抓回本地磁盘，呈现给前端毫无知觉的完美完成画卷！

- **Transparent Proxy Architecture**: Introduced `backend/proxy_server.py` to act as a lightweight local middleman on the user's desktop. It fakes GPU and model readiness for the frontend, while transparently forwarding demanding AI generation requests to a heavy cloud computing node configured via `LTX_CLOUD_URL`.
- **Cloud Proxy File Router**: Added `backend/_routes/proxy.py` to handle `POST /api/proxy/upload` and `GET /api/proxy/download`. This provides the essential file transfer pipelines for the proxy to sync payload assets up to Linux and pull generated products down to Windows smoothly.
- **Automated Uplink/Downlink Path Hijacking**: The proxy server now dynamically scans for JSON properties like `imagePath`, `audioPath`, and `video_path` in REST payloads (Generate, Retake, and IC-LoRA). It automatically intercepts files, replaces file paths, performs the uploads/downloads silently, and serves the correct OS-specific absolute paths to trick both the frontend renderer and the backend Python executor.

### Changed
- **Electron Bootstrapper**: `electron/python-backend.ts` now specifically spins up the `proxy_server.py` application daemon rather than attempting to load the heavily GPU-coupled `ltx2_server.py`.
- **Environment Lean-up**: Stripped outdated local ML-specific environment variables (e.g., `PYTORCH_ENABLE_MPS_FALLBACK`) from the Electron app spawn command, drastically lowering startup friction and freeing the host OS from unnecessary overhead.
