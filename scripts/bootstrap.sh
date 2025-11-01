#!/usr/bin/env bash
set -euo pipefail

: "${WAN_HOME:=/workspace/Wan2.2}"
: "${WAN_CKPT_DIR:=/workspace/models}"
: "${COMFYUI_ROOT:=/workspace/runpod-slim/ComfyUI}"
: "${COMFYUI_HOST:=127.0.0.1}"
: "${COMFYUI_PORT:=8188}"

echo "[bootstrap] ===== WAN 2.2 + ComfyUI Setup ====="
echo "[bootstrap] WAN models directory: ${WAN_CKPT_DIR}"
echo "[bootstrap] ComfyUI root: ${COMFYUI_ROOT}"

# Fallbacks for common RunPod mounts
if [ ! -d "${WAN_CKPT_DIR}" ] || [ -z "$(ls -A "${WAN_CKPT_DIR}" 2>/dev/null || true)" ]; then
  if [ -d "/runpod-volume/models" ] && [ -n "$(ls -A "/runpod-volume/models" 2>/dev/null || true)" ]; then
    export WAN_CKPT_DIR="/runpod-volume/models"
    echo "[bootstrap] Using fallback: ${WAN_CKPT_DIR}"
  elif [ -d "/runpod-volume" ] && [ -n "$(ls -A "/runpod-volume" 2>/dev/null || true)" ]; then
    export WAN_CKPT_DIR="/runpod-volume"
    echo "[bootstrap] Using fallback root: ${WAN_CKPT_DIR}"
  else
    echo "[bootstrap] WARNING: No WAN model files found at ${WAN_CKPT_DIR}. Continuing; WAN jobs may fail until models are mounted."
  fi
fi

echo "[bootstrap] Final WAN model path: ${WAN_CKPT_DIR}"

# Optional: Check if WAN I2V model exists, download if AUTO_DOWNLOAD_MODELS=true
# Users can pre-download models or download manually to avoid this
if [ "${AUTO_DOWNLOAD_I2V:-false}" = "true" ]; then
  WAN_MODEL_DIR="${WAN_CKPT_DIR}/Wan2.2-I2V-A14B"
  WAN_T5_CHECK="${WAN_MODEL_DIR}/models_t5_umt5-xxl-enc-bf16.pth"

  if [ ! -f "${WAN_T5_CHECK}" ]; then
    echo "[bootstrap] WAN I2V model not found at ${WAN_MODEL_DIR}"
    echo "[bootstrap] Downloading Wan2.2-I2V-A14B model from Hugging Face..."
    
    # Set Hugging Face token if provided via environment
    if [ -n "${HF_TOKEN:-}" ]; then
      export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
      echo "[bootstrap] Using HF_TOKEN for authentication"
    fi
    
    mkdir -p "${WAN_MODEL_DIR}"
    
    # Download using huggingface-cli
    if command -v huggingface-cli &> /dev/null; then
      huggingface-cli download Wan-AI/Wan2.2-I2V-A14B --local-dir "${WAN_MODEL_DIR}" --local-dir-use-symlinks False || {
        echo "[bootstrap] WARNING: Model download failed. Jobs may fail until models are available."
      }
    else
      echo "[bootstrap] WARNING: huggingface-cli not found. Install with: pip install huggingface_hub[cli]"
      echo "[bootstrap] Jobs may fail until models are manually downloaded to ${WAN_MODEL_DIR}"
    fi
  else
    echo "[bootstrap] WAN I2V model found at ${WAN_MODEL_DIR}"
  fi
else
  echo "[bootstrap] Skipping auto-download (set AUTO_DOWNLOAD_I2V=true to enable)"
  # List available models
  if [ -d "${WAN_CKPT_DIR}" ]; then
    echo "[bootstrap] Available models in ${WAN_CKPT_DIR}:"
    ls -1 "${WAN_CKPT_DIR}" | grep -i "Wan2.2" || echo "  (none found)"
  fi
fi

# Setup ComfyUI model paths
echo "[bootstrap] Setting up ComfyUI model configuration..."

# Create/update extra_model_paths.yaml from permanent storage or template
if [ -f "/workspace/models/extra_model_paths.yaml" ]; then
  echo "[bootstrap] Using extra_model_paths.yaml from permanent storage"
  ln -sf /workspace/models/extra_model_paths.yaml "${COMFYUI_ROOT}/extra_model_paths.yaml"
elif [ -f "/workspace/extra_model_paths.yaml" ]; then
  echo "[bootstrap] Using extra_model_paths.yaml from image"
  cp /workspace/extra_model_paths.yaml "${COMFYUI_ROOT}/extra_model_paths.yaml"
else
  echo "[bootstrap] Creating default extra_model_paths.yaml"
  cat > "${COMFYUI_ROOT}/extra_model_paths.yaml" << 'EOF'
wan2_permanent_storage:
  base_path: /workspace/models
  
  diffusion_models: diffusion_models/
  unet: unet/
  vae: vae/
  text_encoders: text_encoders/
  clip: clip/
  audio_encoders: audio_encoders/
  clip_vision: clip_vision/
  loras: loras/
  checkpoints: checkpoints/
  controlnet: controlnet/
  embeddings: embeddings/
  upscale_models: upscale_models/
  configs: configs/
EOF
fi

echo "[bootstrap] ComfyUI model paths configured"
cat "${COMFYUI_ROOT}/extra_model_paths.yaml"

# Start ComfyUI in background
echo "[bootstrap] Starting ComfyUI server on ${COMFYUI_HOST}:${COMFYUI_PORT}..."
cd "${COMFYUI_ROOT}"
python3 main.py --listen ${COMFYUI_HOST} --port ${COMFYUI_PORT} > /tmp/comfyui.log 2>&1 &
COMFYUI_PID=$!
echo "[bootstrap] ComfyUI started with PID: ${COMFYUI_PID}"

# Wait for ComfyUI to be ready
echo "[bootstrap] Waiting for ComfyUI to start..."
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
  if curl -s http://${COMFYUI_HOST}:${COMFYUI_PORT}/ > /dev/null 2>&1; then
    echo "[bootstrap] ComfyUI is ready!"
    break
  fi
  sleep 2
  WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
  echo "[bootstrap] WARNING: ComfyUI did not start within ${MAX_WAIT}s"
  echo "[bootstrap] ComfyUI logs:"
  tail -50 /tmp/comfyui.log
fi

# Start RunPod serverless worker directly (avoid python -m runpod)
echo "[bootstrap] Starting RunPod handler..."
export PYTHONPATH="/workspace:${PYTHONPATH:-}"
exec python3 /workspace/src/handler.py
