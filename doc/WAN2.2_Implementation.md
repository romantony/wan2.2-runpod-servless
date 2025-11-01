# WAN 2.2 Implementation Guide

> **Complete guide for WAN 2.2 I2V, S2V, T2V, and Image Generation models**

---

## Table of Contents
1. [Overview](#overview)
2. [Model Architecture](#model-architecture)
3. [Required Models by Type](#required-models-by-type)
4. [Network Volume Configuration](#network-volume-configuration)
5. [Model Download Instructions](#model-download-instructions)
6. [ComfyUI Directory Structure](#comfyui-directory-structure)
7. [Using Existing Network Drive Models](#using-existing-network-drive-models)
8. [Workflow Integration](#workflow-integration)
9. [Storage Requirements](#storage-requirements)

---

## Overview

WAN 2.2 is a unified video generation framework supporting multiple modalities:

- **I2V (Image-to-Video)**: Animate static images into videos (High Noise & Low Noise variants)
- **S2V (Sound-to-Video)**: Create videos from audio inputs
- **Animation**: Animate with lighting and style controls
- **LightX2V**: Fast 4-step distilled models for quick generation

All variants share common components (VAE, text encoders, audio encoders) but use different diffusion models.

**Your Current Setup:** You have all models saved on the network drive with complete I2V, Sound-to-Video, and Animation capabilities including LoRA accelerators.

---

## Model Architecture

### Shared Components (Already on Your Network Drive)

These models are used across all WAN 2.2 workflows:

| Component | Location | Filename | Purpose | Size |
|-----------|----------|----------|---------|------|
| **VAE** | `vae/` | `wan_2.1_vae.safetensors` | Video encoder/decoder | ~160MB |
| **Text Encoder** | `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | Text understanding | ~4.5GB |
| **Audio Encoder** | `audio_encoders/` | `wav2vec2_large_english_fp16.safetensors` | Sound-to-video encoding | ~630MB |
| **CLIP Vision** | `clip_vision/` | `clip_vision_h.safetensors` | Image understanding | ~3.7GB |

### Available Diffusion Models (14B fp8 variants)

Your network drive contains these high-quality 14B parameter models:

| Workflow | Location | Filename | Purpose | Size |
|----------|----------|----------|---------|------|
| **I2V (High Noise)** | `diffusion_models/` | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | Image-to-video (high motion) | ~14GB |
| **I2V (Low Noise)** | `diffusion_models/` | `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | Image-to-video (subtle motion) | ~14GB |
| **S2V (Sound-to-Video)** | `diffusion_models/` | `wan2.2_s2v_14B_fp8_scaled.safetensors` | Audio-driven video generation | ~14GB |
| **Animation** | `diffusion_models/` | `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors` | Advanced animation control | ~14GB |

### Available LoRA Accelerators

For fast generation (4-step inference):

| LoRA | Location | Filename | Purpose | Size |
|------|----------|----------|---------|------|
| **I2V LightX2V (High Noise)** | `loras/` | `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` | 4-step I2V acceleration | ~100MB |
| **I2V LightX2V (Low Noise)** | `loras/` | `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors` | 4-step I2V acceleration | ~100MB |
| **T2V LightX2V** | `loras/` | `wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors` | 4-step T2V acceleration | ~100MB |
| **Animation Relight** | `loras/` | `WanAnimate_relight_lora_fp16.safetensors` | Lighting control | ~100MB |
| **LightX2V I2V 480p** | `loras/` | `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` | Optimized 480p generation | ~100MB |

---

## Required Models by Type

### Your Current Model Inventory

Based on your network drive file structure, here's what you have:

### 1. WAN 2.2 Image-to-Video (I2V)

**High Noise Variant** (For dynamic, high-motion videos):
| Model File | Directory | Size | Status |
|------------|-----------|------|--------|
| `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` | ~14GB | ✅ Available |
| `wan_2.1_vae.safetensors` | `vae/` | ~160MB | ✅ Available |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | ~4.5GB | ✅ Available |
| `clip_vision_h.safetensors` | `clip_vision/` | ~3.7GB | ✅ Available |

**Low Noise Variant** (For subtle, smooth motion):
| Model File | Directory | Size | Status |
|------------|-----------|------|--------|
| `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` | ~14GB | ✅ Available |
| *(Same shared components as above)* | | | ✅ Available |

**Fast Generation (4-Step LoRAs)**:
| Model File | Directory | Size | Status |
|------------|-----------|------|--------|
| `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` | `loras/` | ~100MB | ✅ Available |
| `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors` | `loras/` | ~100MB | ✅ Available |
| `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` | `loras/` | ~100MB | ✅ Available |

---

### 2. WAN 2.2 Sound-to-Video (S2V)

| Model File | Directory | Size | Status |
|------------|-----------|------|--------|
| `wan2.2_s2v_14B_fp8_scaled.safetensors` | `diffusion_models/` | ~14GB | ✅ Available |
| `wav2vec2_large_english_fp16.safetensors` | `audio_encoders/` | ~630MB | ✅ Available |
| `wan_2.1_vae.safetensors` | `vae/` | ~160MB | ✅ Available |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | ~4.5GB | ✅ Available |

**Requirements:**
- Audio input in WAV format
- Optional text prompts for guidance
- Supports music, speech, and ambient sounds

---

### 3. WAN 2.2 Animation

| Model File | Directory | Size | Status |
|------------|-----------|------|--------|
| `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors` | `diffusion_models/` | ~14GB | ✅ Available |
| `WanAnimate_relight_lora_fp16.safetensors` | `loras/` | ~100MB | ✅ Available |
| `wan_2.1_vae.safetensors` | `vae/` | ~160MB | ✅ Available |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | `text_encoders/` | ~4.5GB | ✅ Available |

**Features:**
- Advanced character animation
- Lighting control via relight LoRA
- Style transfer capabilities
- Motion control

---

### 4. Text-to-Video with LightX2V Acceleration

| Model File | Directory | Size | Status |
|------------|-----------|------|--------|
| `wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors` | `loras/` | ~100MB | ✅ Available |

**Note:** You have the T2V LoRA but may need the base T2V diffusion model:
- Missing: `wan2.2_t2v_14B_fp8_scaled.safetensors` (would need to download if you want T2V)
- Currently: Only fast-generation LoRA is available

---

## Network Volume Configuration

### Recommended: Permanent Storage at `/workspace/models`

**Best Practice:** Store models in `/workspace/models` on permanent storage, separate from the ComfyUI installation.

#### Recommended Directory Structure

```
/workspace/models/                    👈 On permanent storage (network volume)
├── audio_encoders/
│   ├── wav2vec2_large_english_fp16.safetensors        ✅ (630MB)
│   └── put_audio_encoder_models_here
│
├── checkpoints/
│   └── put_checkpoints_here                            (Empty - for image models)
│
├── clip/
│   └── put_clip_or_text_encoder_models_here           (Empty)
│
├── clip_vision/
│   ├── clip_vision_h.safetensors                      ✅ (3.7GB)
│   └── put_clip_vision_models_here
│
├── configs/
│   ├── anything_v3.yaml
│   ├── v1-inference*.yaml
│   └── v2-inference*.yaml                              ✅ (Config files)
│
├── controlnet/
│   └── put_controlnets_and_t2i_here                   (Empty)
│
├── diffusion_models/
│   ├── Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors        ✅ (14GB)
│   ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors           ✅ (14GB)
│   ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors            ✅ (14GB)
│   ├── wan2.2_s2v_14B_fp8_scaled.safetensors                      ✅ (14GB)
│   └── put_diffusion_model_files_here
│
├── loras/
│   ├── WanAnimate_relight_lora_fp16.safetensors                                   ✅ (100MB)
│   ├── lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors            ✅ (100MB)
│   ├── wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors                 ✅ (100MB)
│   ├── wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors                  ✅ (100MB)
│   ├── wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors               ✅ (100MB)
│   └── put_loras_here
│
├── text_encoders/
│   ├── umt5_xxl_fp8_e4m3fn_scaled.safetensors         ✅ (4.5GB)
│   └── put_text_encoder_files_here
│
├── vae/
│   ├── wan_2.1_vae.safetensors                        ✅ (160MB)
│   └── put_vae_here
│
└── [other directories...]
    ├── embeddings/
    ├── upscale_models/
    ├── unet/
    └── etc.
```

**Total Storage Used: ~51GB**
- 4× 14B diffusion models: 56GB
- 5× LoRA models: ~500MB
- VAE: 160MB
- Text encoder: 4.5GB
- Audio encoder: 630MB
- CLIP Vision: 3.7GB

---

### Why `/workspace/models` Instead of `/workspace/runpod-slim/ComfyUI/models`?

| Aspect | `/workspace/models` ✅ | `/workspace/runpod-slim/ComfyUI/models` |
|--------|------------------------|------------------------------------------|
| **Portability** | Works with any ComfyUI version | Tied to specific installation path |
| **Flexibility** | Easy to reconfigure | Locked to directory structure |
| **Clarity** | Clear separation: code vs data | Models mixed with application |
| **Upgrades** | Update ComfyUI without touching models | Risk of overwriting models |
| **Standard** | RunPod best practice | Non-standard approach |
| **Configuration** | Requires `extra_model_paths.yaml` | No config needed (if paths match) |

---

### Required: extra_model_paths.yaml Configuration

Create `extra_model_paths.yaml` in your ComfyUI root to point to permanent storage:

```yaml
# /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml

wan2_permanent_storage:
  base_path: /workspace/models
  
  # Model directories (relative to base_path)
  diffusion_models: diffusion_models/
  vae: vae/
  text_encoders: text_encoders/
  audio_encoders: audio_encoders/
  clip_vision: clip_vision/
  loras: loras/
  checkpoints: checkpoints/
  clip: clip/
  controlnet: controlnet/
  embeddings: embeddings/
  upscale_models: upscale_models/
  unet: unet/
  configs: configs/
```

**Add to your project:**
```bash
# In your repository root
touch extra_model_paths.yaml
# Copy the YAML content above
```

**Add to Dockerfile:**
```dockerfile
# Copy the configuration file
COPY extra_model_paths.yaml /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml
```

### Mounting Network Volume

**In Dockerfile:**
```dockerfile
# Create mount point for permanent storage
RUN mkdir -p /workspace/models

# Copy extra_model_paths.yaml to tell ComfyUI where models are
COPY extra_model_paths.yaml /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml
```

**In docker-compose.yml:**
```yaml
services:
  comfyui:
    image: your-image:latest
    volumes:
      # Mount permanent storage to /workspace/models
      - ./data/models:/workspace/models
      # OR for RunPod network volume:
      - /runpod-volume:/workspace/models
    ports:
      - "8188:8188"
```

**In RunPod Dashboard:**
1. Create or attach a Network Volume
2. Upload models to the volume at `/models/` (subdirectories: diffusion_models/, vae/, etc.)
3. In your Serverless Endpoint settings:
   - **Volume mount path:** `/workspace/models`
   - Ensure `extra_model_paths.yaml` is in your Docker image

**For RunPod CLI:**
```bash
runpod deploy \
  --volume-mount /path/to/network/volume:/workspace/models \
  your-image:latest
```

---

### Migration Guide: Moving from Old to New Structure

If you currently have models at `/workspace/runpod-slim/ComfyUI/models/`:

#### Option 1: Move Models (Recommended)
```bash
# On your storage system or inside container
mv /workspace/runpod-slim/ComfyUI/models/* /workspace/models/
```

#### Option 2: Create Symlink (Quick Fix)
```bash
# Inside container
ln -s /workspace/models /workspace/runpod-slim/ComfyUI/models
```

#### Option 3: Keep Current Structure (Not Recommended)
If you want to keep models at `/workspace/runpod-slim/ComfyUI/models/`, you can:
- Mount storage directly there
- No `extra_model_paths.yaml` needed
- **Downside:** Less flexible, harder to upgrade ComfyUI

---

### Verification After Setup

```bash
# 1. Check models directory is accessible
ls -lh /workspace/models/diffusion_models/

# 2. Check ComfyUI can see the config
cat /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml

# 3. Start ComfyUI and test model detection
curl http://127.0.0.1:8188/object_info | jq '.UNETLoader.input.required.unet_name[0]'

# Expected: Your 4 diffusion models listed
```

---

## ComfyUI Directory Structure

### Your Current Setup

```
/workspace/models/                    👈 Permanent storage (recommended)
├── audio_encoders/                   # Audio processing for S2V ✅
│   └── wav2vec2_large_english_fp16.safetensors
│
├── checkpoints/                      # For future image generation models (empty)
│
├── clip/                            # CLIP text encoders (empty - using text_encoders/)
│
├── clip_vision/                     # CLIP vision models ✅
│   └── clip_vision_h.safetensors
│
├── configs/                         # Model configuration files ✅
│   └── various .yaml files
│
├── controlnet/                      # For future ControlNet support (empty)
│
├── diffusion_models/                # Main WAN 2.2 models ✅
│   ├── Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors
│   ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
│   ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
│   └── wan2.2_s2v_14B_fp8_scaled.safetensors
│
├── embeddings/                      # Text embeddings (empty)
│
├── loras/                          # Fast generation accelerators ✅
│   ├── WanAnimate_relight_lora_fp16.safetensors
│   ├── lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors
│   ├── wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
│   ├── wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
│   └── wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors
│
├── text_encoders/                   # Text encoding models ✅
│   └── umt5_xxl_fp8_e4m3fn_scaled.safetensors
│
├── unet/                           # Alternative diffusion model location (empty)
│
├── upscale_models/                 # For future upscaling (empty)
│
├── vae/                            # Video encoder/decoder ✅
│   └── wan_2.1_vae.safetensors
│
└── vae_approx/                     # Fast VAE approximations (empty)
```

**ComfyUI Installation:** `/workspace/runpod-slim/ComfyUI/`  
**Models Storage:** `/workspace/models/` (separate, permanent)  
**Configuration:** `/workspace/runpod-slim/ComfyUI/extra_model_paths.yaml`

**Total: 51GB of production-ready models for I2V, S2V, and Animation workflows**

---

## Model Download Instructions

### ✅ Your Current Status: ALL MODELS AVAILABLE!

You already have all necessary models on your network drive. **No downloads needed!**

### What You Have:

✅ **I2V (Image-to-Video)** - Both high and low noise variants  
✅ **S2V (Sound-to-Video)** - Full audio-driven generation  
✅ **Animation** - Advanced character animation with lighting control  
✅ **LightX2V LoRAs** - Fast 4-step generation for all workflows  
✅ **Shared Components** - VAE, text encoder, audio encoder, CLIP vision

**Total Storage:** ~51GB

---

### Optional: Add Image Generation Models (If Needed)

You currently have an empty `checkpoints/` directory. If you want to add image generation capabilities (Flux, SDXL, etc.), you can download these:

#### Flux 1-dev (for high-quality image generation)

```dockerfile
# Add to Dockerfile or run manually
RUN wget -O /workspace/runpod-slim/ComfyUI/models/checkpoints/flux1-dev-fp8.safetensors \
  https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors

RUN wget -O /workspace/runpod-slim/ComfyUI/models/clip/clip_l.safetensors \
  https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors

RUN wget -O /workspace/runpod-slim/ComfyUI/models/clip/t5xxl_fp8_e4m3fn.safetensors \
  https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors

RUN wget -O /workspace/runpod-slim/ComfyUI/models/vae/ae.safetensors \
  https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors
```

**Additional Storage:** ~22GB

---

### Optional: Add Base T2V Model (If Needed)

You have T2V LoRAs but not the base T2V model. If you need text-to-video:

```bash
wget -O /workspace/runpod-slim/ComfyUI/models/diffusion_models/wan2.2_t2v_14B_fp8_scaled.safetensors \
  https://huggingface.co/Wan-Lab/Wan2.2/resolve/main/wan2.2_t2v_14B_fp8_scaled.safetensors
```

**Additional Storage:** ~14GB

---

### Model Verification Commands

Check all your models are accessible:

```bash
# List all diffusion models
ls -lh /workspace/runpod-slim/ComfyUI/models/diffusion_models/

# List all LoRAs
ls -lh /workspace/runpod-slim/ComfyUI/models/loras/

# List encoders
ls -lh /workspace/runpod-slim/ComfyUI/models/text_encoders/
ls -lh /workspace/runpod-slim/ComfyUI/models/audio_encoders/

# List VAE
ls -lh /workspace/runpod-slim/ComfyUI/models/vae/

# List CLIP vision
ls -lh /workspace/runpod-slim/ComfyUI/models/clip_vision/
```

Expected output should match your file list above.

---

## Using Existing Network Drive Models

### ✅ RECOMMENDED SETUP: `/workspace/models`

Store your models at **`/workspace/models`** on permanent storage, separate from ComfyUI installation.

### Advantages of This Approach

- ✅ **Clean separation**: Models independent from application code
- ✅ **Easy upgrades**: Update ComfyUI without touching models
- ✅ **Portability**: Works with any ComfyUI installation path
- ✅ **Standard practice**: RunPod best practice pattern
- ✅ **Shared across workers**: Single copy, multiple containers
- ✅ **Persistent**: Models survive container rebuilds
- ✅ **Future-proof**: Easy to reconfigure or migrate

### Setup Process

1. **Organize your models on permanent storage:**
   ```bash
   /workspace/models/
   ├── diffusion_models/
   │   ├── Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors
   │   ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
   │   ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
   │   └── wan2.2_s2v_14B_fp8_scaled.safetensors
   ├── vae/
   │   └── wan_2.1_vae.safetensors
   ├── text_encoders/
   │   └── umt5_xxl_fp8_e4m3fn_scaled.safetensors
   ├── audio_encoders/
   │   └── wav2vec2_large_english_fp16.safetensors
   ├── clip_vision/
   │   └── clip_vision_h.safetensors
   └── loras/
       └── (5 LoRA files)
   ```

2. **Create `extra_model_paths.yaml` in your project root:**
   ```yaml
   wan2_permanent_storage:
     base_path: /workspace/models
     
     diffusion_models: diffusion_models/
     vae: vae/
     text_encoders: text_encoders/
     audio_encoders: audio_encoders/
     clip_vision: clip_vision/
     loras: loras/
     checkpoints: checkpoints/
     clip: clip/
     controlnet: controlnet/
     embeddings: embeddings/
     upscale_models: upscale_models/
     unet: unet/
     configs: configs/
   ```

3. **Update Dockerfile to copy config:**
   ```dockerfile
   # Copy configuration to ComfyUI directory
   COPY extra_model_paths.yaml /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml
   
   # Create mount point for models
   RUN mkdir -p /workspace/models
   ```

4. **Mount the volume when deploying:**
   
   **Docker:**
   ```bash
   docker run -v /path/to/models:/workspace/models your-image:latest
   ```
   
   **Docker Compose:**
   ```yaml
   volumes:
     - ./models:/workspace/models
   ```
   
   **RunPod:**
   - Attach network volume
   - Mount path: `/workspace/models`

5. **Verify models are detected:**
   ```bash
   # Inside container
   curl http://127.0.0.1:8188/object_info | jq '.UNETLoader.input.required.unet_name[0]'
   ```

### Model Resolution Priority

ComfyUI searches for models in this order:
1. **Built-in path**: `/workspace/runpod-slim/ComfyUI/models/{type}/`
2. **External paths**: `/workspace/models/{type}/` (via extra_model_paths.yaml)

If a model exists in both locations, the built-in version is used first.

**Recommendation:** Keep all large models on permanent storage (`/workspace/models/`), only use built-in for small, frequently-updated models.

---

## Workflow Integration

### Model References in ComfyUI Workflows

Each workflow type loads models using specific node classes:

#### 1. Image-to-Video (High Noise) Workflow
```json
{
  "diffusion_model_loader": {
    "inputs": {
      "unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
    },
    "class_type": "UNETLoader"
  },
  "vae_loader": {
    "inputs": {
      "vae_name": "wan_2.1_vae.safetensors"
    },
    "class_type": "VAELoader"
  },
  "text_encoder": {
    "inputs": {
      "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    },
    "class_type": "CLIPLoader"
  },
  "image_input": {
    "inputs": {
      "image": "input_image.png"
    },
    "class_type": "LoadImage"
  },
  "clip_vision": {
    "inputs": {
      "clip_name": "clip_vision_h.safetensors"
    },
    "class_type": "CLIPVisionLoader"
  }
}
```

#### 2. Image-to-Video (Low Noise - Subtle Motion) Workflow
```json
{
  "diffusion_model_loader": {
    "inputs": {
      "unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
    },
    "class_type": "UNETLoader"
  },
  "lora_loader": {
    "inputs": {
      "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
      "strength": 1.0
    },
    "class_type": "LoRALoader"
  }
}
```

#### 3. Sound-to-Video Workflow
```json
{
  "diffusion_model_loader": {
    "inputs": {
      "unet_name": "wan2.2_s2v_14B_fp8_scaled.safetensors"
    },
    "class_type": "UNETLoader"
  },
  "audio_encoder": {
    "inputs": {
      "audio_encoder_name": "wav2vec2_large_english_fp16.safetensors"
    },
    "class_type": "AudioEncoderLoader"
  },
  "audio_input": {
    "inputs": {
      "audio": "input_audio.wav"
    },
    "class_type": "LoadAudio"
  },
  "text_encoder": {
    "inputs": {
      "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    },
    "class_type": "CLIPLoader"
  }
}
```

#### 4. Animation with Lighting Control
```json
{
  "diffusion_model_loader": {
    "inputs": {
      "unet_name": "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors"
    },
    "class_type": "UNETLoader"
  },
  "lora_loader": {
    "inputs": {
      "lora_name": "WanAnimate_relight_lora_fp16.safetensors",
      "strength": 0.8
    },
    "class_type": "LoRALoader"
  }
}
```

#### 5. Fast Generation with LightX2V (4-step)
```json
{
  "diffusion_model_loader": {
    "inputs": {
      "unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
    },
    "class_type": "UNETLoader"
  },
  "lora_loader": {
    "inputs": {
      "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
      "strength": 1.0
    },
    "class_type": "LoRALoader"
  },
  "sampler": {
    "inputs": {
      "steps": 4,
      "cfg": 1.0
    },
    "class_type": "KSampler"
  }
}
```

### Filename Requirements
- **Must match exactly** (case-sensitive)
- **Include .safetensors extension**
- **No spaces in model references**
- **Use forward slashes** in paths (Linux-style)

### Model Selection Guide

| Use Case | Base Model | Optional LoRA | Steps | Quality | Speed |
|----------|------------|---------------|-------|---------|-------|
| **High motion I2V** | `wan2.2_i2v_high_noise_14B_fp8_scaled` | None | 20-30 | ⭐⭐⭐⭐⭐ | 🐢 Slow |
| **Fast high motion** | `wan2.2_i2v_high_noise_14B_fp8_scaled` | `lightx2v_4steps_high_noise` | 4 | ⭐⭐⭐⭐ | 🚀 Fast |
| **Subtle motion I2V** | `wan2.2_i2v_low_noise_14B_fp8_scaled` | None | 20-30 | ⭐⭐⭐⭐⭐ | 🐢 Slow |
| **Fast subtle motion** | `wan2.2_i2v_low_noise_14B_fp8_scaled` | `lightx2v_4steps_low_noise` | 4 | ⭐⭐⭐⭐ | 🚀 Fast |
| **Audio-driven** | `wan2.2_s2v_14B_fp8_scaled` | None | 20-30 | ⭐⭐⭐⭐⭐ | 🐢 Slow |
| **Character animation** | `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ` | `WanAnimate_relight` | 20-30 | ⭐⭐⭐⭐⭐ | 🐢 Slow |
| **480p optimized** | Any I2V model | `lightx2v_I2V_14B_480p` | 4 | ⭐⭐⭐ | 🚀🚀 Very Fast |

---

## Storage Requirements

### Your Current Setup

| Category | Models | Total Size |
|----------|--------|------------|
| **Diffusion Models** | 4× 14B models | ~56GB |
| **LoRA Accelerators** | 5 LoRAs | ~500MB |
| **VAE** | 1 model | ~160MB |
| **Text Encoder** | UmT5-XXL | ~4.5GB |
| **Audio Encoder** | Wav2Vec2 | ~630MB |
| **CLIP Vision** | CLIP-H | ~3.7GB |
| **Configs** | YAML files | ~1MB |
| **Total Used** | | **~51GB** |

### Breakdown by Workflow

| Workflow Type | Required Models | Storage |
|--------------|-----------------|---------|
| **I2V (High Noise)** | Diffusion + VAE + Text Encoder + CLIP Vision | ~22.4GB |
| **I2V (Low Noise)** | Diffusion + VAE + Text Encoder + CLIP Vision | ~22.4GB |
| **S2V (Sound-to-Video)** | Diffusion + VAE + Text Encoder + Audio Encoder | ~19.3GB |
| **Animation** | Diffusion + VAE + Text Encoder | ~18.7GB |

*Note: Shared components (VAE, encoders) are counted once across all workflows*

### With Optional Additions

If you add image generation capabilities:

| Addition | Storage | Total New Size |
|----------|---------|----------------|
| **Current Setup** | ~51GB | |
| **+ Flux 1-dev** | +~22GB | ~73GB |
| **+ T2V Base Model** | +~14GB | ~65GB |
| **+ Both** | +~36GB | ~87GB |

### Storage Optimization Tips

1. **Use fp8 quantized models** ✅ (You're already doing this!)
   - 14B fp8 = ~14GB vs 14B fp16 = ~28GB
   - 50% storage savings with minimal quality loss

2. **Share VAE and encoders** ✅ (Already configured)
   - Single VAE for all video workflows
   - Single text encoder for all workflows

3. **Use LightX2V LoRAs for production**
   - 4-step inference vs 20-30 steps
   - Same model quality, 5-7× faster
   - Tiny storage overhead (~100MB per LoRA)

4. **Keep only needed diffusion models**
   - High noise I2V: Dynamic scenes, dancing, action
   - Low noise I2V: Portraits, subtle expressions, smooth motion
   - S2V: Music videos, rhythm-based animations
   - Animation: Character animation, lighting control

---

## Quick Start Checklist

### ✅ Your Setup Status

- [x] **Models on network drive** - All 4 diffusion models + LoRAs present
- [x] **Shared components available** - VAE, text encoder, audio encoder, CLIP vision
- [x] **Fast generation LoRAs** - 5 LightX2V LoRAs ready
- [x] **Directory structure correct** - Default ComfyUI paths used
- [x] **Storage allocated** - ~51GB used, production-ready

### Next Steps

1. **Verify container access to models:**
   ```bash
   docker exec -it <container> ls -lh /workspace/runpod-slim/ComfyUI/models/diffusion_models/
   ```

2. **Start ComfyUI server:**
   ```bash
   # Usually started automatically in your container
   # Or manually:
   python /workspace/runpod-slim/ComfyUI/main.py --listen 0.0.0.0 --port 8188
   ```

3. **Test model detection:**
   ```bash
   # Wait for ComfyUI to start, then:
   curl http://127.0.0.1:8188/object_info | jq '.UNETLoader.input.required.unet_name[0]'
   ```

4. **Test a simple workflow:**
   - Load I2V workflow JSON
   - Upload test image
   - Queue workflow
   - Check outputs

5. **Monitor performance:**
   ```bash
   # GPU memory usage
   nvidia-smi -l 1
   
   # Container logs
   docker logs -f <container>
   ```

### Configuration Checklist

For Docker deployment:

- [ ] Mount models directory: `-v /path/to/models:/workspace/runpod-slim/ComfyUI/models`
- [ ] Expose ComfyUI port: `-p 8188:8188`
- [ ] Allocate sufficient GPU memory (recommend 24GB+ VRAM for 14B models)
- [ ] Set CUDA environment variables if needed

For RunPod Serverless:

- [ ] Network volume attached with models
- [ ] Mount point configured: `/workspace/runpod-slim/ComfyUI/models`
- [ ] GPU tier selected (A40/A100 recommended)
- [ ] Handler configured for ComfyUI API
- [ ] Timeout settings appropriate for video generation

---

## Testing Model Availability

### Verify Models Are Loaded

Once ComfyUI is running on port 8188:

```bash
# 1. Check ComfyUI server is up
curl http://127.0.0.1:8188/
# Expected: HTML response or { "status": "ok" }

# 2. List all available diffusion models
curl -s http://127.0.0.1:8188/object_info | jq '.UNETLoader.input.required.unet_name[0]'
# Expected output:
# [
#   "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors",
#   "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
#   "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
#   "wan2.2_s2v_14B_fp8_scaled.safetensors"
# ]

# 3. List all available LoRAs
curl -s http://127.0.0.1:8188/object_info | jq '.LoraLoader.input.required.lora_name[0]'
# Expected: Array with your 5 LoRA files

# 4. Check VAE models
curl -s http://127.0.0.1:8188/object_info | jq '.VAELoader.input.required.vae_name[0]'
# Expected: ["wan_2.1_vae.safetensors"]

# 5. Check text encoders
curl -s http://127.0.0.1:8188/object_info | jq '.DualCLIPLoader'
# Expected: Configuration for text encoder loading

# 6. Check audio encoders
curl -s http://127.0.0.1:8188/object_info | jq '.AudioEncoderLoader'
# Expected: Audio encoder configuration

# 7. Check CLIP vision models
curl -s http://127.0.0.1:8188/object_info | jq '.CLIPVisionLoader.input.required.clip_name[0]'
# Expected: ["clip_vision_h.safetensors"]
```

### Test Workflow Execution

Create a test request file:

```bash
# test_i2v_request.json
{
  "input": {
    "workflow": {
      "1": {
        "inputs": {
          "unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
        },
        "class_type": "UNETLoader"
      },
      "2": {
        "inputs": {
          "vae_name": "wan_2.1_vae.safetensors"
        },
        "class_type": "VAELoader"
      }
    }
  }
}
```

Submit and monitor:

```bash
# Queue the workflow
PROMPT_ID=$(curl -s -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  -d @test_i2v_request.json | jq -r '.prompt_id')

echo "Workflow queued with ID: $PROMPT_ID"

# Check status
curl -s http://127.0.0.1:8188/history/$PROMPT_ID | jq

# View outputs
curl -s http://127.0.0.1:8188/history/$PROMPT_ID | jq '.[$PROMPT_ID].outputs'
```

### Performance Benchmarks

Expected generation times (on A100 80GB):

| Workflow | Resolution | Frames | Steps | With LoRA | Without LoRA |
|----------|------------|--------|-------|-----------|--------------|
| I2V High Noise | 512×512 | 16 | 4 | ~15s | ~60s |
| I2V High Noise | 512×512 | 16 | 20 | - | ~5min |
| I2V Low Noise | 832×480 | 33 | 4 | ~30s | ~2min |
| I2V Low Noise | 832×480 | 33 | 20 | - | ~10min |
| S2V | 512×512 | 16 | 20 | - | ~6min |
| Animation | 512×512 | 16 | 20 | - | ~6min |

**Recommendation:** Use LightX2V LoRAs for production to achieve 5-7× speedup with minimal quality loss.

---

## Additional Resources

- [WAN 2.2 HuggingFace Repository](https://huggingface.co/Wan-Lab/Wan2.2)
- [Reference Architecture](./Ref_Achitecture.md)
- [ComfyUI Documentation](https://github.com/comfyanonymous/ComfyUI)
- [RunPod Network Volume Guide](https://docs.runpod.io/pods/storage/create-network-volumes)
- [LightX2V Paper](https://arxiv.org/abs/lightx2v) - Fast video generation
- [WAN 2.2 Model Card](https://huggingface.co/Wan-Lab/Wan2.2) - Official model documentation

---

**Document Version:** 2.0  
**Last Updated:** November 1, 2025  
**Repository:** wan2.2-runpod-servless  
**Author:** romantony

---

## Summary

### ✅ You're Ready to Go!

**Your network drive setup is complete and production-ready!**

### What You Have:

✅ **4 Diffusion Models (14B each)**
- High-noise I2V for dynamic motion
- Low-noise I2V for subtle animation  
- Sound-to-video for audio-driven generation
- Animation model with lighting control

✅ **5 LightX2V LoRA Accelerators**
- 4-step fast generation for all workflows
- 5-7× faster than standard 20-30 step generation
- Optimized 480p variant included

✅ **Complete Supporting Infrastructure**
- VAE encoder/decoder
- UmT5-XXL text encoder
- Wav2Vec2 audio encoder
- CLIP-H vision encoder
- Config files

**Total: ~51GB of production-ready models**

### Models Location:
```
/workspace/models/  👈 RECOMMENDED (permanent storage, separate from ComfyUI)
```

**Configuration Required:** `extra_model_paths.yaml` (already created in your repo root)

### Alternative (Not Recommended):
```
/workspace/runpod-slim/ComfyUI/models/  ❌ Ties models to ComfyUI installation path
```

### No Additional Configuration Needed IF:
✅ You use the recommended `/workspace/models/` path  
✅ You copy `extra_model_paths.yaml` to ComfyUI directory in Dockerfile  
✅ You mount your network volume to `/workspace/models/`

### Model Summary Table

| Model File | Type | Size | Workflow | Status |
|------------|------|------|----------|--------|
| `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | Diffusion | 14GB | Dynamic I2V | ✅ |
| `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | Diffusion | 14GB | Subtle I2V | ✅ |
| `wan2.2_s2v_14B_fp8_scaled.safetensors` | Diffusion | 14GB | Sound-to-Video | ✅ |
| `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors` | Diffusion | 14GB | Animation | ✅ |
| `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` | LoRA | 100MB | Fast I2V | ✅ |
| `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors` | LoRA | 100MB | Fast I2V | ✅ |
| `wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors` | LoRA | 100MB | Fast T2V | ✅ |
| `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` | LoRA | 100MB | Fast 480p | ✅ |
| `WanAnimate_relight_lora_fp16.safetensors` | LoRA | 100MB | Lighting | ✅ |
| `wan_2.1_vae.safetensors` | VAE | 160MB | All video | ✅ |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | Text Encoder | 4.5GB | All workflows | ✅ |
| `wav2vec2_large_english_fp16.safetensors` | Audio Encoder | 630MB | S2V | ✅ |
| `clip_vision_h.safetensors` | Vision Encoder | 3.7GB | I2V | ✅ |

### Optional Additions (If Needed):
- ❌ T2V base model - You have LoRA only, download base model if you need full text-to-video
- ❌ Image generation models (Flux/SDXL) - Download if you need static image generation

---

**Your setup supports:**
- ✅ Image-to-Video (I2V) - Both high and low noise variants
- ✅ Sound-to-Video (S2V) - Audio-driven video generation
- ✅ Animation - Character animation with lighting control
- ✅ Fast Generation - 4-step inference with LightX2V LoRAs
- ❌ Text-to-Video (T2V) - LoRA available, base model missing (optional)
- ❌ Image Generation - No models (optional)
