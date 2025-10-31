FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04
# Build: 2025-10-31 - Fix flash-attn for RTX 5090
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

# Try to install flash-attn (prebuilt wheel preferred)
# If it fails, continue - we'll patch WAN code to handle missing flash-attn
RUN pip install flash-attn --no-build-isolation || echo "Flash-attn not available, will use PyTorch fallback"

WORKDIR /workspace
# Wan2.2 (video) – i2v/s2v CLI
RUN git clone https://github.com/Wan-Video/Wan2.2.git && \
    cd Wan2.2 && \
    pip install -r requirements.txt || true

# Patch WAN to make flash-attn optional with PyTorch fallback
RUN python3 -c "
import re
file_path = '/workspace/Wan2.2/wan/modules/attention.py'
with open(file_path, 'r') as f:
    content = f.read()

# Replace the assertion with a fallback
old_code = '    assert FLASH_ATTN_2_AVAILABLE'
new_code = '''    # Fallback if flash-attn not available
    if not FLASH_ATTN_2_AVAILABLE:
        import torch.nn.functional as F
        q_t = q.transpose(1, 2)  # [B, H, N, D]
        k_t = k.transpose(1, 2)
        v_t = v.transpose(1, 2)
        out = F.scaled_dot_product_attention(q_t, k_t, v_t, attn_mask=None, dropout_p=0.0)
        return out.transpose(1, 2).contiguous()
    # assert FLASH_ATTN_2_AVAILABLE - using fallback instead'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print('✅ Applied flash-attn fallback patch')
else:
    print('⚠️ Could not find assertion line to patch')
    exit(1)
"

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
