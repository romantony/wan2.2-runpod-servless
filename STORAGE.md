# RunPod Persistent Storage Configuration

## Volume Information
- **Volume ID**: `p63c2g0961`
- **Mount Point**: `/runpod-volume` (in container)
- **Models Path**: `/runpod-volume/models/`

## Stored Models

### WAN Video Generation Models
Located in: `/runpod-volume/models/`

1. **Image-to-Video (i2v-A14B)**
   - Task: `i2v-A14B`
   - Purpose: Convert images to videos with motion
   - Required for: Image-to-video generation requests

2. **Speech-to-Video (s2v-*)**
   - Task: `s2v-*` variants
   - Purpose: Generate videos from speech/audio
   - Required for: Speech-to-video generation requests

### ComfyUI Models
Located in: `/runpod-volume/models/` (or subdirectories)

3. **FLUX.1-dev**
   - Purpose: Image generation/enhancement pipeline
   - Used by: ComfyUI workflows
   - Type: Diffusion model

## How Bootstrap Finds Your Models

The `bootstrap.sh` script automatically detects models:

### For WAN Models:
1. Checks `WAN_CKPT_DIR` (default: `/workspace/models`)
2. Falls back to `/runpod-volume/models` ✅ **Your models are here**
3. Falls back to `/runpod-volume`

### For ComfyUI Models:
Checks in order:
1. `/runpod-volume/comfyui-models`
2. `/runpod-volume/ComfyUI/models`
3. `/runpod-volume/models/ComfyUI`
4. `/runpod-volume/ComfyUI_models`
5. `/runpod-volume/ComfyUI`

Then symlinks to `/workspace/ComfyUI/models`

## Expected Directory Structure

```
/runpod-volume/
└── models/
    ├── i2v-A14B/              # WAN Image-to-Video checkpoints
    │   ├── model_*.safetensors
    │   └── config.yaml
    ├── s2v-*/                 # WAN Speech-to-Video checkpoints
    │   ├── model_*.safetensors
    │   └── config.yaml
    └── flux1-dev/             # FLUX.1-dev for ComfyUI
        ├── checkpoints/
        ├── vae/
        └── ...
```

## Deployment Checklist

- [x] Volume `p63c2g0961` mounted to `/runpod-volume`
- [x] WAN i2v models stored in `/runpod-volume/models/`
- [x] WAN s2v models stored in `/runpod-volume/models/`
- [x] FLUX.1-dev models stored in `/runpod-volume/models/`
- [x] Bootstrap script configured to find models
- [x] All Python dependencies installed (including `decord`)

## Verification

After deployment, check container logs for:
```
[bootstrap] Final WAN model path: /runpod-volume/models
[bootstrap] ComfyUI models: /workspace/ComfyUI/models
```

If you see these paths, your models are correctly mounted and accessible!
