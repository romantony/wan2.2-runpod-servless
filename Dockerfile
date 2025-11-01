FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04
# Build: 2025-10-31 - Use devel image for flash-attn compilation, make it optional
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    WAN_HOME=/workspace/Wan2.2 \
    WAN_CKPT_DIR=/runpod-volume/models \
    COMFYUI_ROOT=/workspace/runpod-slim/ComfyUI \
    COMFYUI_HOST=127.0.0.1 \
    COMFYUI_PORT=8188 \
    TINI_SUBREAPER=1 \
    RUNPOD_MAX_CONCURRENCY=1

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

# ComfyUI (for image and video pipelines)
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /workspace/runpod-slim/ComfyUI && \
    python3 -m pip install -r /workspace/runpod-slim/ComfyUI/requirements.txt || true

# Install ComfyUI Custom Nodes for Video Generation
RUN cd /workspace/runpod-slim/ComfyUI/custom_nodes && \
    # Video Helper Suite - Essential for video generation (VHS_VideoCombine, etc.)
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    pip install -r ComfyUI-VideoHelperSuite/requirements.txt && \
    # AnimateDiff Evolved - Advanced video animation
    git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git && \
    pip install -r ComfyUI-AnimateDiff-Evolved/requirements.txt || true && \
    # Advanced ControlNet - For better control
    git clone https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git && \
    pip install -r ComfyUI-Advanced-ControlNet/requirements.txt || true

# Copy extra_model_paths.yaml to configure model locations
COPY extra_model_paths.yaml /workspace/extra_model_paths.yaml

# Create model mount point
RUN mkdir -p /workspace/models

COPY requirements.txt /workspace/requirements.txt
RUN pip install -r /workspace/requirements.txt

COPY src /workspace/src
COPY scripts /workspace/scripts
RUN chmod +x /workspace/scripts/bootstrap.sh

ENV RUNPOD_MAX_CONCURRENCY=1

ENTRYPOINT ["/usr/bin/tini","-s","--"]
CMD ["/bin/bash","/workspace/scripts/bootstrap.sh"]
