#!/usr/bin/env bash
set -euo pipefail

: "${WAN_HOME:=/workspace/Wan2.2}"
: "${WAN_CKPT_DIR:=/workspace/models}"

echo "[bootstrap] Using models from ${WAN_CKPT_DIR}"
if [ ! -d "${WAN_CKPT_DIR}" ] || [ -z "$(ls -A "${WAN_CKPT_DIR}" 2>/dev/null || true)" ]; then
  echo "[bootstrap] ERROR: No model files found at ${WAN_CKPT_DIR}."
  echo "           Mount your RunPod permanent storage to /workspace/models or set WAN_CKPT_DIR."
  exit 1
fi

python3 -m runpod
