FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04
# Build: 2025-10-30 - Auto-download WAN models + python3-dev fix
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

# Install flash-attn after torch so torch is available in the build environment
# Use --no-build-isolation so the build can see the already-installed torch package.
RUN PIP_NO_BUILD_ISOLATION=1 pip install --no-build-isolation flash-attn==2.8.3 || PIP_NO_BUILD_ISOLATION=1 pip install --no-build-isolation flash-attn || true

WORKDIR /workspace
# Wan2.2 (video) – i2v/s2v CLI
RUN git clone https://github.com/Wan-Video/Wan2.2.git && \
    cd Wan2.2 && \
    pip install -r requirements.txt || true

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
