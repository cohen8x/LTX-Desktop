# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### 修复与增强 (Fixed & Enhanced)
- **Fixed GenSpace Drag-and-Drop Image Loss (无声丢图Bug)**：由于 Chromium 沙盒的安全隔离，前端在 `GenSpace` 拖拽系统文件时会丢失原生的 `File.path`。原代码没有正确接管 Electron 提供的系统特权 API，导致上传的图片全部变成 `null`，后端只能被动进入“纯文本生视频（Text-to-Video）”模式。我们在 `frontend/views/GenSpace.tsx` 的 PromptBar 中重写了所有的 `handleDrop` 和 `handleFileSelect`，强制劫持并透传 `window.electronAPI.getPathForFile()` 的真实物理路径。
- **Fixed Gap Generation (Fill with Video) Payload Logic**：在轨道剪辑的“填充缝隙”面板中，原有的 UI 虽然完美截取了上下文的前后两帧，但仅仅把这几张图发给 Gemini 用来写提示词了，真正的生成请求却还是用的“Text-to-Video”模式发往后端。我们通过大幅度重构 `useGapGeneration.ts` 和 `GapGenerationModal.tsx`，把选中的“Start Frame”完美桥接注入到了最终的 `imagePath` 参数槽中。
- **Fixed Maximum Call Stack Size Exceeded Crash**：在使用纯内存截图（如提取的视频帧）转换为本地临时文件时，原代码极其粗暴地使用了 `btoa(String.fromCharCode(...new Uint8Array(buf)))`。只要用户的屏幕截图稍大（达到 1-2MB），就会瞬间因为数组过大撑爆 JavaScript V8 引擎的函数调用栈导致前端白屏死机。我们采用原生的 `FileReader.readAsDataURL` 异步流完美重写了 Base64 转换器，彻底杜绝了该死机隐患。
- **Fixed Fatal UnicodeEncodeError Logging Crash on Windows**：由于旧版 Windows 命令行（CMD / PowerShell）默认使用 `GBK` (cp936) 字符编码集，如果 Python 后端在此极度脆弱的旧版环境强行打印包含了 Emoji (如 🚀 或 🎬) 的调试日志，会直接触发 `UnicodeEncodeError` 的底层系统崩溃，连带导致正在反向代理握手等待的 ASGI (Uvicorn) 通讯完全阻断断开。现已将代理端与逻辑端日志中的所有非标 Emoji 和特殊字符剔除干净。
- **修复 Electron 底层废弃的物理路径读取Bug**：原项目依赖了较新版本的 Electron (v31+)，由于较强沙箱隔离策略，官方早就废除了拖拽原生 `file.path` 的强访问权限。这导致原本的音频/视频/图片上传总是退化成虚假的假路径（如 `./file.jpg`）进而找不到文件报错。我们利用 `electron/preload.ts` 暴露了官方专门弥盖的特权级接口 `webUtils.getPathForFile`，重构替换了三大文件选取组件，彻底根治了这个埋藏极深的历史遗留拖拽 Bug。
- **重构进度返回载体机制**：修改了云端的 `api_types.py` 与 `generation_handler.py` 的查询接口。现在只要渲染步骤抵达 `100% complete`，不仅返回进度条数据，还会一并抛出底包的 `video_path` 物理坐标供云端到代理的长距精准轮询与收割。
- **代理层的 NAT 掉线生死守护机制 (Fallback Long-Polling)**：原代理发起的同步阻塞 `POST /api/generate` 渲染指令耗时近 5 分钟，在这种长空闲等待期中，请求极易被路由器或宽带运营商 ISP 墙防火墙作僵尸丢包强杀。现在即便最初的原生 `POST` 物理连接被残忍打断中断，`proxy_server.py` 内部会自动无缝退化成高频的长轮询探测状态。不管链路如何断裂，只要云端进度达到百分百，它就能在茫茫星海中把这段视频抓回本地磁盘，呈现给前端毫无知觉的完美完成画卷！

- **Transparent Proxy Architecture**: Introduced `backend/proxy_server.py` to act as a lightweight local middleman on the user's desktop. It fakes GPU and model readiness for the frontend, while transparently forwarding demanding AI generation requests to a heavy cloud computing node configured via `LTX_CLOUD_URL`.
- **Cloud Proxy File Router**: Added `backend/_routes/proxy.py` to handle `POST /api/proxy/upload` and `GET /api/proxy/download`. This provides the essential file transfer pipelines for the proxy to sync payload assets up to Linux and pull generated products down to Windows smoothly.
- **Automated Uplink/Downlink Path Hijacking**: The proxy server now dynamically scans for JSON properties like `imagePath`, `audioPath`, and `video_path` in REST payloads (Generate, Retake, and IC-LoRA). It automatically intercepts files, replaces file paths, performs the uploads/downloads silently, and serves the correct OS-specific absolute paths to trick both the frontend renderer and the backend Python executor.

### Changed
- **Electron Bootstrapper**: `electron/python-backend.ts` now specifically spins up the `proxy_server.py` application daemon rather than attempting to load the heavily GPU-coupled `ltx2_server.py`.
- **Environment Lean-up**: Stripped outdated local ML-specific environment variables (e.g., `PYTORCH_ENABLE_MPS_FALLBACK`) from the Electron app spawn command, drastically lowering startup friction and freeing the host OS from unnecessary overhead.
