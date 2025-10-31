FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04
# Build: 2025-10-31 - Use devel image for flash-attn compilation, make it optional
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    WAN_HOME=/workspace/Wan2.2 \
    WAN_CKPT_DIR=/workspace/models \
    COMFYUI_ROOT=/workspace/ComfyUI \
    COMFYUI_MODELS_DIR=/workspace/ComfyUI/models \
    TINI_SUBREAPER=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs python3 python3-pip python3-venv python3-dev curl wget ca-certificates tini ffmpeg libsndfile1 \
    build-essential cmake ninja-build \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip && \
    pip install --index-url https://download.pytorch.org/whl/cu128 \
        torch torchvision torchaudio

# Try to install flash-attn (prebuilt wheel or compile)
# If compilation fails, continue - we have a fallback in the patch
RUN pip install packaging ninja && \
    (pip install flash-attn --no-build-isolation || echo "⚠️ Flash-attn compilation failed, will use PyTorch fallback")

WORKDIR /workspace
# Wan2.2 (video) – i2v/s2v CLI
RUN git clone https://github.com/Wan-Video/Wan2.2.git && \
    cd Wan2.2 && \
    pip install -r requirements.txt || true

# Copy and apply patch to make flash-attn optional with PyTorch fallback
COPY scripts/patch_attention.py /workspace/
RUN python3 /workspace/patch_attention.py

# ComfyUI (for image pipelines like FLUX dev)
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git ${COMFYUI_ROOT} && \
    python3 -m pip install -r ${COMFYUI_ROOT}/requirements.txt || true

COPY requirements.txt /workspace/requirements.txt
RUN pip install -r /workspace/requirements.txt

COPY src /workspace/src
COPY scripts /workspace/scripts
RUN chmod +x /workspace/scripts/bootstrap.sh

ENV RUNPOD_MAX_CONCURRENCY=1

ENTRYPOINT ["/usr/bin/tini","-s","--"]
CMD ["/bin/bash","/workspace/scripts/bootstrap.sh"]
