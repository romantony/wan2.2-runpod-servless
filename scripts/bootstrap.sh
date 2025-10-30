#!/usr/bin/env bash
set -euo pipefail

: "${WAN_HOME:=/workspace/Wan2.2}"
: "${WAN_CKPT_DIR:=/workspace/models}"
: "${COMFYUI_ROOT:=/workspace/ComfyUI}"
: "${COMFYUI_MODELS_DIR:=/workspace/ComfyUI/models}"

echo "[bootstrap] Preferred WAN model path: ${WAN_CKPT_DIR}"

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

# ComfyUI models symlink to persistent storage if available
mkdir -p "${COMFYUI_ROOT}" "${COMFYUI_MODELS_DIR}"
PERSIST_ROOT=""
if [ -d "/runpod-volume" ]; then
  PERSIST_ROOT="/runpod-volume"
elif [ -d "${WAN_CKPT_DIR}" ]; then
  PERSIST_ROOT="${WAN_CKPT_DIR}"
fi

if [ -n "${PERSIST_ROOT}" ]; then
  # Preferred structured locations under persistent storage
  for CAND in \
    "${PERSIST_ROOT}/comfyui-models" \
    "${PERSIST_ROOT}/ComfyUI/models" \
    "${PERSIST_ROOT}/models/ComfyUI" \
    "${PERSIST_ROOT}/ComfyUI_models" \
    "${PERSIST_ROOT}/ComfyUI"; do
    if [ -d "${CAND}" ]; then
      if [ -L "${COMFYUI_MODELS_DIR}" ] || [ -d "${COMFYUI_MODELS_DIR}" ]; then
        # Replace empty dir with symlink
        if [ -d "${COMFYUI_MODELS_DIR}" ] && [ -z "$(ls -A "${COMFYUI_MODELS_DIR}" 2>/dev/null || true)" ]; then
          rmdir "${COMFYUI_MODELS_DIR}" || true
        fi
      fi
      if [ ! -e "${COMFYUI_MODELS_DIR}" ]; then
        ln -s "${CAND}" "${COMFYUI_MODELS_DIR}"
        echo "[bootstrap] Linked ComfyUI models -> ${CAND}"
      fi
      break
    fi
  done
fi

echo "[bootstrap] ComfyUI root: ${COMFYUI_ROOT}"
echo "[bootstrap] ComfyUI models: ${COMFYUI_MODELS_DIR}"

# Start RunPod serverless worker directly (avoid python -m runpod)
export PYTHONPATH="/workspace:${PYTHONPATH:-}"
exec python3 /workspace/src/handler.py
