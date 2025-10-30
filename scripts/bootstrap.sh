#!/usr/bin/env bash
set -euo pipefail

: "${WAN_HOME:=/workspace/Wan2.2}"
: "${WAN_CKPT_DIR:=/workspace/models}"

echo "[bootstrap] Preferred model path: ${WAN_CKPT_DIR}"

# Fallbacks for common RunPod mounts
if [ ! -d "${WAN_CKPT_DIR}" ] || [ -z "$(ls -A "${WAN_CKPT_DIR}" 2>/dev/null || true)" ]; then
  if [ -d "/runpod-volume/models" ] && [ -n "$(ls -A "/runpod-volume/models" 2>/dev/null || true)" ]; then
    export WAN_CKPT_DIR="/runpod-volume/models"
    echo "[bootstrap] Using fallback: ${WAN_CKPT_DIR}"
  elif [ -d "/runpod-volume" ] && [ -n "$(ls -A "/runpod-volume" 2>/dev/null || true)" ]; then
    export WAN_CKPT_DIR="/runpod-volume"
    echo "[bootstrap] Using fallback root: ${WAN_CKPT_DIR}"
  else
    echo "[bootstrap] WARNING: No model files found at ${WAN_CKPT_DIR}. Continuing to start worker; jobs will fail until models are mounted."
  fi
fi

echo "[bootstrap] Final model path: ${WAN_CKPT_DIR}"

python3 -m runpod
