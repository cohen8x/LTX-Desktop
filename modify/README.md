# LTX-Desktop 端云分离部署指南

本文档包含了如何将 LTX-Desktop 的“前端客户端”与“云端服务端”进行彻底分离部署的完整全方位说明。

## 架构原理

在使用端云分离模式时，前端应用将变成一个纯粹的 GUI 客户端，跳过所有本地的显卡/VRAM 检测，并跳过强制的模型下载初始化页面。
后端服务可以通过开放 `0.0.0.0` 接口并在云端运行，同时支持配置 Token 来防止接口被公众滥用。

---

## 步骤一：云端服务器部署 (Backend)

### 1. 模型预下载配置与清单

LTX-Desktop 完全依赖本地模型，因此您的云端服务器必须先拥有模型。
以下是完整的预下载模型清单（数据来源于后端源码文件：`backend/runtime_config/model_download_specs.py` 中的 `DEFAULT_MODEL_DOWNLOAD_SPECS` 配置）：

| 模型种类 | 仓库 (repo_id) | 对应文件名 / 文件夹 | 预估大小 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| **主视频生成** | `Lightricks/LTX-2.3` | `ltx-2.3-22b-distilled.safetensors` | 43 GB | 核心 Transformer (必选) |
| **空间放大器** | `Lightricks/LTX-2.3` | `ltx-2.3-spatial-upscaler-x2-1.0.safetensors` | 1.9 GB | 2x 画质放大器 (必选) |
| **静态图生成** | `Tongyi-MAI/Z-Image-Turbo` | `Z-Image-Turbo/` (文件夹) | 31 GB | ZIT 静态图引擎 (必选) |
| **文本编码器** | `Lightricks/gemma-3-12b-it-qat-q4_0...` | `gemma-3-12b-it-qat-q4_0-unquantized/` | 25 GB | Gemma 文本理解引擎 (可选)* |
| **控制模型** | `Lightricks/LTX-2.3-22b-IC-LoRA...` | `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors` | 654 MB | IC-LoRA 动作控制 |
| **微调模型** | `Lightricks/LTX-2` | `ltx-2-19b-distilled-lora-384.safetensors` | 400 MB | 基础 LoRA |
| **深度处理器** | `Intel/dpt-hybrid-midas` | `dpt-hybrid-midas/` (文件夹) | 500 MB | MiDaS 景深预测处理器 |
| **人物检测器** | `hr16/yolox-onnx` | `yolox_l.torchscript.pt` | 217 MB | YOLOX 人物检测 |
| **姿态处理器** | `hr16/DWPose-TorchScript-BatchSize5` | `dw-ll_ucoco_384_bs5.torchscript.pt` | 135 MB | DWPose 姿态提取 |

> **提示：** 如果您决定在前端填入 LTX 的云端 API Key，则标有星号(*)的 **文本编码器** 可以不下载。

假设您将所有 AI 模型数据统一存放于云端的 `/data/ai_models/models` 目录下，那么以上列出的所有具体文件或文件夹，都必须直接存放在这个 `models/` 目录中。

### 2. 国内网络加速下载建议 (针对中国大陆用户)

由于后端代码底层使用的是官方的 `huggingface_hub` 库来进行模型拉取（源码见 `backend/services/model_downloader/hugging_face_downloader.py`），它是强绑定 HuggingFace 代码库格式的，因此**无法直接将地址改为 ModelScope（魔搭社区）**，两者的 SDK 和模型组织结构并不兼容。

但是，您可以直接使用国内极为成熟的 HuggingFace 镜像站（如 `hf-mirror.com`）来达成跑满宽带的下载速度！
您只需要在启动后端服务前，额外声明一条 `HF_ENDPOINT` 环境变量即可，后端的自动下载器会自动识别并走国内镜像高速下载。

### 3. 环境变量设置

在云端的终端（Terminal）中，进入到原项目源码的 `backend` 目录下，并设置以下环境变量启动服务：

```bash
cd backend/

# 1. 设置模型存放的父目录 (必填)
export LTX_APP_DATA_DIR="/data/ai_models"

# 2. 强制解锁本地模式，禁用本地硬件限制 (必填)
export LTX_FORCE_LOCAL_MODE="1"

# 3. 允许外网访问，绑定到 0.0.0.0 (必填)
export LTX_HOST="0.0.0.0"

# 4. 指定端口号 (可选，默认随机或自动顺延)
export LTX_PORT="8000"

# 5. 设置接口调用身份验证，防止服务器被白嫖 (强烈建议！)
export LTX_AUTH_TOKEN="my_super_secret_auth_token"
export LTX_ADMIN_TOKEN="my_super_secret_admin_token"

# 启动 FastAPI 后端服务器
uv run python ltx2_server.py
```

*提示：配置了 Token 后，任何没有携带此 Token 的请求都会被拦截。服务器启动后，请确保云服务商控制台中的安全组防火墙已放行 `8000` 端口的 TCP 流量。*

---

## 步骤二：本地电脑配置 (Frontend)

您的本地电脑不需要出色的显卡，也不需要庞大的硬盘，只需要运行前端界面。

### 1. 创建 `.env` 配置文件
在您本地电脑的 `LTX-Desktop` 项目**根目录**下，新建一个名为 `.env` 的文件。
在文件中填入刚才配置的对接信息：

```env
# 云端服务器的公网 IP 及端口
LTX_EXTERNAL_BACKEND_URL=http://<您的云服务公网IP>:8000

# 与云端服务器保持一致的认证 Token
LTX_AUTH_TOKEN=my_super_secret_auth_token
LTX_ADMIN_TOKEN=my_super_secret_admin_token
```

### 2. 启动前端
随后，您只需要在终端里正常运行项目的开发者模式即可：

```bash
pnpm dev
```

启动后，系统会自动读取 `.env` 配置：

1. 它绝对不会在本地悄悄为您启动备用 Python 进程。
2. 它会直接跳过那繁琐的 70GB 模型下载确认安装屏。
3. 如果 `LTX_AUTH_TOKEN` 匹配成功，它会立刻无缝接管云端算力，为您呈现解锁了全部完整功能的视频编辑与控制界面。

---

如果需要在图形界面里为云端添置缺失的模型，您随时可以点击前端界面的 **Settings (齿轮)** -> **Model Status**，在那里点击 **Download All**，前端便会指挥云端在后台执行缺失文件的下载补充任务。
