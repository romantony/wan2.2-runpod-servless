# API Documentation - WAN 2.2 + ComfyUI RunPod Serverless

> Complete API reference for video generation with WAN 2.2 and ComfyUI workflows

---

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [WAN 2.2 API](#wan-22-api)
5. [ComfyUI API](#comfyui-api)
6. [Request Examples](#request-examples)
7. [Response Format](#response-format)
8. [Error Handling](#error-handling)

---

## Overview

This serverless worker provides two execution modes:
1. **WAN 2.2 CLI**: Direct video generation using WAN 2.2 Python scripts
2. **ComfyUI Workflows**: Workflow-based generation using ComfyUI nodes

Both modes share:
- Model storage at `/workspace/models/`
- GPU processing on RTX 5090 Pro
- Async job execution with status tracking

---

## Authentication

Use RunPod API keys for authentication. Include in request headers:

```http
Authorization: Bearer YOUR_RUNPOD_API_KEY
```

---

## Endpoints

### Base Endpoint
```
https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/
```

### Health Check
```http
POST /runsync
Content-Type: application/json

{
  "input": {
    "health": true
  }
}
```

**Response:**
```json
{
  "ok": true,
  "wan_home": "/workspace/Wan2.2",
  "ckpt_dir": "/workspace/models",
  "comfyui_url": "http://127.0.0.1:8188",
  "comfyui_status": "online"
}
```

---

## WAN 2.2 API

### Generate Video (I2V/S2V/T2V)

**Endpoint:** `POST /runsync` or `POST /run` (async)

**Request:**
```json
{
  "input": {
    "action": "generate",
    "task": "i2v-A14B",
    "reference_image_url": "https://example.com/image.png",
    "prompt": "A beautiful sunset over the ocean",
    "size": "1280*720",
    "frame_num": 16,
    "sample_steps": 20,
    "sample_guide_scale": 7.0,
    "seed": 42,
    "use_lora": true,
    "offload_model": true,
    "return_video": true
  }
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | string | - | `"generate"`, `"request"`, or `"create"` |
| `task` | string | `"i2v-A14B"` | WAN task: `i2v-A14B`, `s2v-14B`, `t2v-A14B`, `animate-14B` |
| `reference_image_url` | string | - | URL to input image (for I2V) |
| `reference_image_base64` | string | - | Base64-encoded image (for I2V) |
| `prompt` | string | `""` | Text prompt for generation |
| `size` | string | `"1280*720"` | Output size (e.g., `"512*512"`, `"832*480"`) |
| `frame_num` | int | - | Number of frames to generate |
| `sample_steps` | int | - | Sampling steps |
| `sample_guide_scale` | float | - | CFG scale |
| `seed` | int | - | Random seed |
| `offload_model` | bool | `true` | Offload model to CPU when not in use |
| `return_video` | bool | `true` | Return video as base64 in response |

**Response:**
```json
{
  "request_id": "uuid-here",
  "status": {
    "status": "COMPLETED",
    "started": 1234567890.0,
    "completed_at": 1234567895.0,
    "outputs": ["/workspace/outputs/uuid.mp4"]
  },
  "result": {
    "filename": "uuid.mp4",
    "data": "data:video/mp4;base64,..."
  }
}
```

---

### Check Status

**Request:**
```json
{
  "input": {
    "action": "status",
    "request_id": "uuid-here",
    "return_video": true
  }
}
```

**Response:**
```json
{
  "request_id": "uuid-here",
  "status": {
    "status": "COMPLETED",
    "outputs": ["/workspace/outputs/uuid.mp4"]
  },
  "result": {
    "filename": "uuid.mp4",
    "data": "data:video/mp4;base64,..."
  }
}
```

---

## ComfyUI API

### Execute Workflow

**Request:**
```json
{
  "input": {
    "action": "comfyui_workflow",
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
    },
    "images": [
      {
        "name": "input.png",
        "data": "data:image/png;base64,..."
      }
    ],
    "timeout": 600,
    "return_base64": true
  }
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | string | - | `"comfyui_workflow"` |
| `workflow` | object | - | ComfyUI workflow JSON |
| `images` | array | `[]` | Images to upload before execution |
| `timeout` | int | `600` | Max execution time in seconds |
| `return_base64` | bool | `false` | Return outputs as base64 |

**Response:**
```json
{
  "request_id": "uuid-here",
  "status": "completed",
  "outputs": [
    {
      "filename": "output.mp4",
      "data": "base64-encoded-data",
      "size": 1234567
    }
  ]
}
```

---

### Image-to-Video (ComfyUI Mode)

**Request:**
```json
{
  "input": {
    "action": "comfyui_i2v",
    "reference_image_url": "https://example.com/image.png",
    "prompt": "A beautiful animation",
    "diffusion_model": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
    "vae_model": "wan_2.1_vae.safetensors",
    "steps": 20,
    "cfg_scale": 7.0,
    "seed": 42,
    "use_lora": true,
    "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
    "lora_strength": 1.0,
    "timeout": 600,
    "return_video": true
  }
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | string | - | `"comfyui_i2v"` |
| `reference_image_url` | string | - | URL to input image |
| `reference_image_base64` | string | - | Base64-encoded image |
| `prompt` | string | `""` | Text prompt |
| `diffusion_model` | string | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | Diffusion model |
| `vae_model` | string | `wan_2.1_vae.safetensors` | VAE model |
| `steps` | int | `20` | Sampling steps |
| `cfg_scale` | float | `7.0` | CFG scale |
| `seed` | int | `-1` | Random seed (-1 for random) |
| `use_lora` | bool | `false` | Enable LoRA for fast generation |
| `lora_name` | string | - | LoRA model filename |
| `lora_strength` | float | `1.0` | LoRA strength |
| `timeout` | int | `600` | Max execution time |
| `return_video` | bool | `true` | Return video as base64 |

**Response:**
```json
{
  "request_id": "uuid-here",
  "status": "completed",
  "result": {
    "filename": "uuid_i2v_output.mp4",
    "data": "data:video/mp4;base64,..."
  }
}
```

---

### List Available Models

**Request:**
```json
{
  "input": {
    "action": "comfyui_models"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "models": {
    "diffusion_models": [
      "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors",
      "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
      "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
      "wan2.2_s2v_14B_fp8_scaled.safetensors"
    ],
    "vae": [
      "wan_2.1_vae.safetensors"
    ],
    "loras": [
      "WanAnimate_relight_lora_fp16.safetensors",
      "lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors",
      "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
      "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
      "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors"
    ]
  }
}
```

---

## Request Examples

### Example 1: High-Quality I2V (20 steps)

```python
import requests

url = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

payload = {
    "input": {
        "action": "generate",
        "task": "i2v-A14B",
        "reference_image_url": "https://example.com/portrait.jpg",
        "prompt": "person smiling and waving",
        "size": "832*480",
        "frame_num": 33,
        "sample_steps": 20,
        "sample_guide_scale": 7.5,
        "seed": 123,
        "return_video": True
    }
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

# Save video
import base64
video_data = result["result"]["data"].split(",")[1]
with open("output.mp4", "wb") as f:
    f.write(base64.b64decode(video_data))
```

---

### Example 2: Fast I2V with LoRA (4 steps)

```python
payload = {
    "input": {
        "action": "comfyui_i2v",
        "reference_image_url": "https://example.com/scene.jpg",
        "prompt": "dynamic motion, high energy",
        "diffusion_model": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
        "steps": 4,  # Fast generation
        "cfg_scale": 1.0,  # Low CFG for distilled models
        "use_lora": True,
        "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
        "seed": 42,
        "return_video": True
    }
}

response = requests.post(url, json=payload, headers=headers)
# ~5-7x faster than 20-step generation!
```

---

### Example 3: Custom ComfyUI Workflow

```python
payload = {
    "input": {
        "action": "comfyui_workflow",
        "workflow": {
            "1": {
                "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"},
                "class_type": "UNETLoader"
            },
            "2": {
                "inputs": {"vae_name": "wan_2.1_vae.safetensors"},
                "class_type": "VAELoader"
            },
            "3": {
                "inputs": {"image": "input.png"},
                "class_type": "LoadImage"
            }
        },
        "images": [
            {
                "name": "input.png",
                "data": "data:image/png;base64,iVBORw0KGgo..."
            }
        ],
        "return_base64": True
    }
}

response = requests.post(url, json=payload, headers=headers)
```

---

## Response Format

### Success Response
```json
{
  "request_id": "uuid",
  "status": "completed",
  "result": {
    "filename": "output.mp4",
    "data": "data:video/mp4;base64,..."
  }
}
```

### Error Response
```json
{
  "request_id": "uuid",
  "error": "Error message here",
  "status": "ERROR"
}
```

### Status Codes

| Status | Description |
|--------|-------------|
| `RUNNING` | Job is currently executing |
| `COMPLETED` | Job finished successfully |
| `ERROR` | Job failed with error |
| `NO_OUTPUT` | Job completed but no output found |
| `TIMEOUT` | Job exceeded timeout limit |

---

## Error Handling

### Common Errors

**Missing Image:**
```json
{
  "error": "Missing reference image (url/base64/path) for i2v task."
}
```

**Model Not Found:**
```json
{
  "error": "Model 'xyz.safetensors' not found in /workspace/models/"
}
```

**ComfyUI Offline:**
```json
{
  "error": "ComfyUI server is not responding"
}
```

**Timeout:**
```json
{
  "status": "timeout",
  "error": "Execution did not complete within 600s"
}
```

---

## Performance Tips

### For Fastest Generation:
- Use 4-step LoRAs: `wan2.2_i2v_lightx2v_4steps_lora_v1_*.safetensors`
- Set `cfg_scale=1.0` with distilled models
- Use 480p variant for even faster: `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors`
- Lower resolution: `512*512` instead of `832*480`
- Fewer frames: `16` instead of `33`

### For Best Quality:
- Use 20-30 sampling steps
- High-noise model for dynamic motion: `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- Low-noise model for subtle motion: `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`
- Higher CFG scale: `7.0-7.5`
- Higher resolution: `832*480` or `1280*720`

---

## Model Selection Guide

| Use Case | Model | LoRA | Steps | Speed |
|----------|-------|------|-------|-------|
| **Fast I2V (high motion)** | `wan2.2_i2v_high_noise_14B_fp8_scaled` | `lightx2v_4steps_high_noise` | 4 | 🚀 Very Fast |
| **Fast I2V (subtle motion)** | `wan2.2_i2v_low_noise_14B_fp8_scaled` | `lightx2v_4steps_low_noise` | 4 | 🚀 Very Fast |
| **Quality I2V (dynamic)** | `wan2.2_i2v_high_noise_14B_fp8_scaled` | None | 20 | 🐢 Slow |
| **Quality I2V (smooth)** | `wan2.2_i2v_low_noise_14B_fp8_scaled` | None | 20 | 🐢 Slow |
| **Sound-to-Video** | `wan2.2_s2v_14B_fp8_scaled` | None | 20 | 🐢 Slow |
| **Animation** | `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ` | `WanAnimate_relight` | 20 | 🐢 Slow |
| **480p optimized** | Any I2V | `lightx2v_I2V_14B_480p` | 4 | 🚀🚀 Fastest |

---

## Support

For issues or questions:
- GitHub: https://github.com/romantony/wan2.2-runpod-servless
- Documentation: `/doc/` directory
- RunPod Support: https://discord.gg/runpod

---

**Document Version:** 1.0  
**Last Updated:** November 1, 2025  
**Repository:** wan2.2-runpod-servless
