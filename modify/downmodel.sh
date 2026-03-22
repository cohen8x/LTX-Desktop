#!/bin/bash

# 1. 使用超快的 uv 在系统全局极速安装官方下载器
uv tool install huggingface_hub

# 2. 设置国内高速镜像源与目标存储根目录
export HF_ENDPOINT=https://hf-mirror.com
# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MODELS_DIR="$SCRIPT_DIR/models"

# 创建文件夹
mkdir -p "$MODELS_DIR"


# ========= 开始全自动高速拉取 =========

echo "==========================================="
echo "⚡ 即将开始使用 国内高速镜像节点 全局下载大模型 ⚡"
echo "==========================================="

echo -e "\n[1/4] 正在下载 核心生成与放大模型 (最占用硬盘，约45G)..."
hf download Lightricks/LTX-2.3 ltx-2.3-22b-distilled.safetensors --local-dir "$MODELS_DIR"
hf download Lightricks/LTX-2.3 ltx-2.3-spatial-upscaler-x2-1.0.safetensors --local-dir "$MODELS_DIR"

echo -e "\n[2/4] 正在下载 控制与微调 LoRA 集合..."
hf download Lightricks/LTX-2 ltx-2-19b-distilled-lora-384.safetensors --local-dir "$MODELS_DIR"
hf download Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors --local-dir "$MODELS_DIR"

echo -e "\n[3/4] 正在下载 姿态检测模型组..."
hf download hr16/yolox-onnx yolox_l.torchscript.pt --local-dir "$MODELS_DIR"
hf download hr16/DWPose-TorchScript-BatchSize5 dw-ll_ucoco_384_bs5.torchscript.pt --local-dir "$MODELS_DIR"


# [文件夹区]：这几个必须分别放在专属的子文件夹中
echo -e "\n[4/4] 正在下载 场景处理预设模型文件夹 (含31G大动作库)..."
hf download Tongyi-MAI/Z-Image-Turbo --local-dir "$MODELS_DIR/Z-Image-Turbo"
hf download Intel/dpt-hybrid-midas --local-dir "$MODELS_DIR/dpt-hybrid-midas"


# ⚠️ 可选项：(如果您不使用外部的加速 API、而是想靠本机硬啃文本生成的话，可以把最前面那个 # 删去执行)
# echo -e "\n[额外] 正在下载 文本编码器 (这东西单独占 25G 硬盘)..."
# hf download Lightricks/gemma-3-12b-it-qat-q4_0-unquantized --local-dir "$MODELS_DIR/gemma-3-12b-it-qat-q4_0-unquantized"

echo "==========================================="
echo "✅ 所有下载/校验均已执行完毕！"
echo "您可以放心地通过在 LTX_APP_DATA_DIR 指定 $MODELS_DIR 的上级目录 来启动后端了！"
