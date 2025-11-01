# Wan2.2 + ComfyUI on RunPod Serverless (Models in Persistent Storage)

This image provides:
- **WAN 2.2** video generation (I2V, S2V, Animation)
- **ComfyUI** for workflow-based generation
- **Persistent storage** integration for models

## 📚 Documentation

- **[WAN 2.2 Implementation Guide](doc/WAN2.2_Implementation.md)** - Complete setup guide
- **[Storage Strategy](doc/Storage_Strategy_Summary.md)** - Recommended storage approach
- **[Storage Migration](doc/Storage_Migration_Guide.md)** - Migration instructions
- **[Reference Architecture](doc/Ref_Achitecture.md)** - API and architecture details

## 🎯 Quick Start

### Your Current Setup

You have **51GB of production-ready models** including:
- ✅ 4× WAN 2.2 diffusion models (14B parameters, fp8)
- ✅ 5× LightX2V LoRA accelerators (4-step fast generation)
- ✅ Complete support infrastructure (VAE, encoders)

**Capabilities:**
- Image-to-Video (high & low noise variants)
- Sound-to-Video (audio-driven generation)
- Animation (with lighting control)
- Fast generation (5-7× faster with LoRAs)

## 📦 Model Storage

### Recommended Structure: `/workspace/models/`

Store models at `/workspace/models/` on permanent storage (network volume):

```
/workspace/models/                    👈 51GB on network volume
├── diffusion_models/                 (4× 14GB WAN 2.2 models)
├── loras/                            (5× 100MB LoRAs)
├── vae/                              (wan_2.1_vae.safetensors)
├── text_encoders/                    (UmT5-XXL)
├── audio_encoders/                   (Wav2Vec2)
├── clip_vision/                      (CLIP-H)
└── configs/
```

**Why this structure?**
- ✅ Clean separation: models separate from application code
- ✅ Easy upgrades: update ComfyUI without touching models
- ✅ Shared across workers: single copy, multiple containers
- ✅ Standard practice: follows RunPod best practices

### Configuration

The `extra_model_paths.yaml` file (included in repo) tells ComfyUI where to find models:

```yaml
wan2_permanent_storage:
  base_path: /workspace/models
  diffusion_models: diffusion_models/
  vae: vae/
  # ... etc
```

## Model Setup

### Option 1: Auto-Download on First Run (Recommended)
The bootstrap script will automatically download the WAN 2.2 I2V-A14B model from Hugging Face if not found.

**Set the `HF_TOKEN` environment variable in your RunPod template:**
```
HF_TOKEN=hf_your_huggingface_token_here
```

Get your token from: https://huggingface.co/settings/tokens

The model will be downloaded to `${WAN_CKPT_DIR}/Wan2.2-I2V-A14B` on the first worker startup.

### Option 2: Pre-Download Models
If you prefer to pre-download models to your persistent storage:

```bash
pip install "huggingface_hub[cli]"
huggingface-cli download Wan-AI/Wan2.2-I2V-A14B --local-dir /runpod-volume/models/Wan2.2-I2V-A14B --local-dir-use-symlinks False
```

Ensure the model directory contains `models_t5_umt5-xxl-enc-bf16.pth` and other checkpoint files.

## Build & Deploy

### 1. Build Docker Image
```bash
docker build -t <YOUR_REGISTRY>/wan22-runpod-serverless:latest .
docker push <YOUR_REGISTRY>/wan22-runpod-serverless:latest
```

### 2. Configure Environment Variables

Set in your RunPod Serverless template:

| Variable | Value | Purpose |
|----------|-------|---------|
| `HF_TOKEN` | `hf_your_token_here` | Hugging Face authentication |
| `RUNPOD_MAX_CONCURRENCY` | `1` | Single job per worker |
| `COMFYUI_ROOT` | `/workspace/runpod-slim/ComfyUI` | ComfyUI installation path |

### 3. Mount Network Volume

**In RunPod Dashboard:**
- Attach your network volume (ID: `p63c2g0961`)
- **Mount path:** `/workspace/models` ✅ **RECOMMENDED**

Your models should be organized as:
```
/workspace/models/
├── diffusion_models/
│   ├── Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors
│   ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
│   ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
│   └── wan2.2_s2v_14B_fp8_scaled.safetensors
├── loras/ (5 LoRA files)
├── vae/ (wan_2.1_vae.safetensors)
├── text_encoders/ (UmT5-XXL)
├── audio_encoders/ (Wav2Vec2)
└── clip_vision/ (CLIP-H)
```

### 4. Verify Setup

Once deployed, test model detection:
```bash
curl http://127.0.0.1:8188/object_info | jq '.UNETLoader.input.required.unet_name[0]'
```

Expected: List of your 4 WAN 2.2 diffusion models

Mount your RunPod permanent storage and ensure your models are placed in one of these locations:

- Wan2.2 weights:
  - Preferred: `/workspace/models` (or set `WAN_CKPT_DIR`)
  - Fallbacks auto-detected: `/runpod-volume` or `/runpod-volume/models`

- ComfyUI models (for FLUX, etc.): any one of
  - `/runpod-volume/comfyui-models`
  - `/runpod-volume/ComfyUI/models`
  - `/workspace/ComfyUI/models` (if directly mounted)

At startup, the bootstrap script links `COMFYUI_MODELS_DIR` to the first matching persistent path.

## GPU/CUDA Compatibility
- Base image: CUDA 12.8.0 + cuDNN (Ubuntu 22.04)
- PyTorch stack: cu128 wheels (latest available for torch/vision/audio)
- Target GPUs: RTX 5090 (default in runpod.yaml), RTX 4090, A100.
- If you see device/driver mismatches, ensure host drivers support CUDA 12.8. If necessary, rebuild after upgrading drivers.

## API (Serverless Handler)
### Request
```json
{
  "action": "request",
  "params": {
    "task": "i2v-A14B",
    "reference_image_url": "https://.../img.png",
    "prompt": "cinematic winter summit, steady pan, subtle parallax",
    "size": "1280*720",
    "seed": 42,
    "offload_model": true,
    "t5_cpu": true
  },
  "return_video": true
}
```

### Status
```json
{ "action": "status", "request_id": "UUID", "return_video": true }
```

Outputs save to `/workspace/outputs/<request_id>.mp4` (and can be returned as base64 when `return_video=true`).

### Tasks
- `t2v-A14B`: text-to-video (requires only `prompt`)
- `i2v-A14B`: image-to-video (requires `reference_image_*` + `prompt`)
- `s2v-14B`: speech-to-video (requires `audio` + `image` + `prompt`)
- `ti2v-5B`: text/image-to-video hybrid (optional `image`)

## Testing

### Text-to-Video (T2V)
```bash
python scripts/test_t2v_endpoint.py \
  --api-url https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  --api-key YOUR_API_KEY \
  --prompt "Two anthropomorphic cats in boxing gear fighting on a stage" \
  --frames 49 \
  --steps 24 \
  --cfg 6.0
```

### Image-to-Video (I2V)
```bash
python scripts/test_endpoint.py \
  --api-url https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  --api-key YOUR_API_KEY \
  --image-url https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=1024 \
  --prompt "cinematic slow pan" \
  --frames 49 \
  --steps 24 \
  --cfg 6.0
```

## Parameters
These inputs are forwarded to Wan2.2’s `generate.py` (aligned to the upstream CLI). Defaults shown are from the wrapper or upstream where noted; ranges are recommended, not strict.

- reference_image_url | reference_image_base64 | reference_image_path
  - For i2v tasks: Required. One of URL, base64, or absolute path.
- size
  - Default (upstream): `1280*720` (`WIDTH*HEIGHT`).
- prompt
  - Default (upstream): `None`.
- seed (alias for `base_seed`)
  - Default (upstream): `-1` → random.
- frame_num (alias: `num_frames`)
  - Must satisfy `4n+1` (e.g., 33, 49, 81).
- sample_solver | sample_steps | sample_guide_scale | sample_shift
  - Typical ranges: steps ~20–36, guidance 3.0–9.0.
- offload_model | t5_cpu | convert_model_dtype
  - On serverless, keep enabled to reduce VRAM.
- save_file
  - Automatically set to `/workspace/outputs/<request_id>.mp4` unless overridden.
- extra_args
  - Advanced passthrough to the WAN CLI; accepts string or array (first 50 tokens used).

Notes
- Only supported flags are forwarded. See `src/handler.py` for aliased mappings.
- If `WAN_CKPT_DIR` (`/workspace/models` by default) is missing but `/runpod-volume` exists, the handler falls back to `/runpod-volume`.

## ComfyUI usage (FLUX.1-dev image models)
- The container installs ComfyUI in `COMFYUI_ROOT`.
- Place image model weights in your persistent storage under one of the ComfyUI model paths above (e.g. `checkpoints`, `diffusers`).
- This repo does not expose a ComfyUI HTTP API worker by default; it prepares the environment so other workers or flows can use ComfyUI with pre-mounted weights.

