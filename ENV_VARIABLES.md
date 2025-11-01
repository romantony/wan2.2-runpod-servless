# Environment Variables Configuration

> **Critical configuration for WAN 2.2 + ComfyUI RunPod Serverless**

---

## Required Environment Variables

### In Dockerfile (Build-time)

These are baked into the Docker image:

```dockerfile
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
```

### In RunPod Dashboard (Runtime)

Set these in your Serverless Endpoint configuration:

| Variable | Value | Purpose |
|----------|-------|---------|
| `WAN_CKPT_DIR` | `/runpod-volume/models` | ✅ **Model storage location** |
| `RUNPOD_MAX_CONCURRENCY` | `1` | Limit to 1 job per worker (GPU memory) |
| `COMFYUI_ROOT` | `/workspace/runpod-slim/ComfyUI` | ComfyUI installation path |
| `COMFYUI_HOST` | `127.0.0.1` | ComfyUI server host |
| `COMFYUI_PORT` | `8188` | ComfyUI server port |

---

## ✅ Model Path Configuration

### Confirmed Setup

Your models are stored at:
```
/runpod-volume/models
```

This matches the Dockerfile configuration:
```dockerfile
ENV WAN_CKPT_DIR=/runpod-volume/models
```

### Configuration Status

✅ All configuration files point to correct location:
- `Dockerfile`: `WAN_CKPT_DIR=/runpod-volume/models`
- `extra_model_paths.yaml`: `base_path: /runpod-volume/models`
- `runpod.yaml`: `WAN_CKPT_DIR=/runpod-volume/models`
- `handler.py`: Uses `WAN_CKPT_DIR` environment variable

**All paths aligned!**

---

## Complete Environment Variable Reference

### System Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBIAN_FRONTEND` | `noninteractive` | Prevent apt-get prompts |
| `PIP_NO_CACHE_DIR` | `1` | Reduce Docker image size |
| `PYTHONUNBUFFERED` | `1` | Real-time Python output |
| `TINI_SUBREAPER` | `1` | Proper signal handling |

### WAN 2.2 Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `WAN_HOME` | `/workspace/Wan2.2` | WAN source code location |
| `WAN_CKPT_DIR` | `/runpod-volume/models` | Model storage location |
| `WAN_OUT_DIR` | `/workspace/outputs` | Output directory (optional) |

### ComfyUI Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `COMFYUI_ROOT` | `/workspace/runpod-slim/ComfyUI` | ComfyUI installation |
| `COMFYUI_HOST` | `127.0.0.1` | Server bind address |
| `COMFYUI_PORT` | `8188` | Server port |

### RunPod Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `RUNPOD_MAX_CONCURRENCY` | `1` | Max concurrent jobs per worker |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_DOWNLOAD_I2V` | `false` | Auto-download models if missing |
| `HF_TOKEN` | - | Hugging Face token for gated models |
| `COMFY_API_AVAILABLE_MAX_RETRIES` | `500` | ComfyUI startup retries |
| `COMFY_API_AVAILABLE_INTERVAL_MS` | `50` | Retry interval |
| `WEBSOCKET_RECONNECT_ATTEMPTS` | `5` | WebSocket reconnection attempts |
| `WEBSOCKET_RECONNECT_DELAY_S` | `3` | Delay between reconnects |

---

## How to Update Environment Variables

### Standard Configuration (Already Set)

All environment variables are correctly configured:
- `Dockerfile` has `WAN_CKPT_DIR=/runpod-volume/models` ✅
- `extra_model_paths.yaml` points to `/runpod-volume/models` ✅
- `runpod.yaml` has `WAN_CKPT_DIR=/runpod-volume/models` ✅

### If You Need to Override (Advanced)

**Method 1: RunPod Dashboard Override**

If you need to use a different path temporarily:

1. Go to: https://www.runpod.io/console/serverless
2. Find endpoint: `c5tcnbrax0chts`
3. Click "Edit"
4. Scroll to "Environment Variables"
5. Add override (will override Dockerfile value)
6. Save and restart workers

**Method 2: Update runpod.yaml**

For permanent changes via configuration file:
```yaml
env:
  - key: WAN_CKPT_DIR
    value: "/runpod-volume/models"
  - key: RUNPOD_MAX_CONCURRENCY
    value: "1"
  - key: COMFYUI_ROOT
    value: "/workspace/runpod-slim/ComfyUI"
```

Then redeploy using RunPod CLI.

---

## Verification

Test that models are detected correctly:

```python
import requests

r = requests.post(
    'https://api.runpod.ai/v2/c5tcnbrax0chts/runsync',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={'input': {'health': True}}
)

result = r.json()
print('Model directory:', result['output']['ckpt_dir'])
# Should show: /runpod-volume/models
```

Then test model detection:

```python
r = requests.post(
    'https://api.runpod.ai/v2/c5tcnbrax0chts/runsync',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={'input': {'action': 'comfyui_models'}}
)

models = r.json()['output']['models']
print('Diffusion models found:', len(models.get('diffusion_models', [])))
# Should show: 4 (your WAN 2.2 models)
```

---

## Recommended Settings for Production

### Dockerfile
```dockerfile
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    WAN_HOME=/workspace/Wan2.2 \
    WAN_CKPT_DIR=/runpod-volume/models \
    WAN_OUT_DIR=/workspace/outputs \
    COMFYUI_ROOT=/workspace/runpod-slim/ComfyUI \
    COMFYUI_HOST=127.0.0.1 \
    COMFYUI_PORT=8188 \
    TINI_SUBREAPER=1 \
    RUNPOD_MAX_CONCURRENCY=1
```

### RunPod Dashboard (Optional Overrides)
- `HF_TOKEN` - If using gated models
- `AUTO_DOWNLOAD_I2V=false` - Disable auto-download (use pre-loaded models)
- Custom timeout values if needed

---

## Environment Variable Priority

1. **RunPod Dashboard** (highest priority)
2. **runpod.yaml**
3. **Dockerfile ENV**
4. **Application defaults** (lowest priority)

---

## Current Status Summary

✅ **All Configuration Correct:**
- System variables configured correctly
- ComfyUI variables correct
- RunPod concurrency set
- Model path correctly set to `/runpod-volume/models`
- `extra_model_paths.yaml` points to correct location
- `runpod.yaml` aligned with Dockerfile

✅ **Ready for Testing:**
- All paths aligned
- Configuration complete
- Ready to test model detection

---

## Files Status

1. ✅ `Dockerfile` - `WAN_CKPT_DIR=/runpod-volume/models` (correct)
2. ✅ `extra_model_paths.yaml` - `base_path: /runpod-volume/models` (correct)
3. ✅ `runpod.yaml` - `WAN_CKPT_DIR=/runpod-volume/models` (correct)
4. ✅ `handler.py` - Uses environment variable (correct)

---

## Next Steps

1. **Commit:** Push updated configuration files to trigger rebuild
2. **Test:** Verify model detection after rebuild completes (~15-20 minutes)
3. **Validate:** Confirm all 4 diffusion models + 5 LoRAs detected
4. **Deploy:** Test end-to-end I2V generation with LoRA acceleration

---

**Last Updated:** November 1, 2025  
**Status:** Configuration updated to `/runpod-volume/models`, ready to commit and rebuild
