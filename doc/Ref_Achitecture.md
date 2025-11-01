# Model Storage and API Reference Guide

> **Complete reference for model storage locations, API endpoints, and ComfyUI integration**

---

## Table of Contents
1. [Model Storage Architecture](#model-storage-architecture)
2. [Directory Structure](#directory-structure)
3. [Model Requirements by Workflow Type](#model-requirements-by-workflow-type)
4. [API Endpoints](#api-endpoints)
5. [API Configuration](#api-configuration)
6. [Workflow Integration](#workflow-integration)
7. [Network Volume Support](#network-volume-support)
8. [Troubleshooting](#troubleshooting)

---

## Model Storage Architecture

### Container Model Paths

ComfyUI expects models in specific directories under `/comfyui/models/`. The worker is configured to support both:
- **Built-in models** (baked into the Docker image)
- **Network volume models** (shared across workers via RunPod network storage)

### Primary Model Directory
```
/comfyui/models/
├── checkpoints/         # Main model files (Flux, SDXL, SD3, etc.)
├── vae/                 # VAE decoder models
├── unet/                # UNet/diffusion models (for split architectures)
├── clip/                # CLIP text encoder models
├── text_encoders/       # Alternative text encoder location
├── loras/               # LoRA enhancement models
├── controlnet/          # ControlNet models
├── clip_vision/         # CLIP vision models
├── embeddings/          # Text embeddings
├── upscale_models/      # Upscaling models
├── configs/             # Model configuration files
└── diffusion_models/    # Additional diffusion models
```

---

## Directory Structure

### 1. Built-in Models (Docker Image)

Models are downloaded during Docker build and stored at:
```
/comfyui/models/
```

**Dockerfile Configuration:**
```dockerfile
WORKDIR /comfyui
RUN mkdir -p models/checkpoints models/vae models/unet models/clip
```

**Example: Flux Model Download**
```dockerfile
RUN wget -q -O models/checkpoints/flux1-dev-fp8.safetensors \
    https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors
```

**Example: SD3 Model Download (requires authentication)**
```dockerfile
RUN wget -q --header="Authorization: Bearer ${HUGGINGFACE_ACCESS_TOKEN}" \
    -O models/checkpoints/sd3_medium_incl_clips_t5xxlfp8.safetensors \
    https://huggingface.co/stabilityai/stable-diffusion-3-medium/resolve/main/sd3_medium_incl_clips_t5xxlfp8.safetensors
```

### 2. Network Volume Models (Shared Storage)

Configuration file: `/comfyui/extra_model_paths.yaml`

```yaml
runpod_worker_comfy:
  base_path: /runpod-volume
  checkpoints: models/checkpoints/
  clip: models/clip/
  clip_vision: models/clip_vision/
  configs: models/configs/
  controlnet: models/controlnet/
  embeddings: models/embeddings/
  loras: models/loras/
  upscale_models: models/upscale_models/
  vae: models/vae/
  unet: models/unet/
  text_encoders: models/text_encoders/
  diffusion_models: models/diffusion_models/
```

**Full Path Resolution:**
- Checkpoints: `/runpod-volume/models/checkpoints/`
- CLIP: `/runpod-volume/models/clip/`
- VAE: `/runpod-volume/models/vae/`
- LoRAs: `/runpod-volume/models/loras/`
- etc.

---

## Model Requirements by Workflow Type

### Image Generation Workflows

#### Flux 1-dev (flux1-dev-fp8)
**Location:** `/comfyui/models/`

| Model Type | Directory | Filename | Size | Purpose |
|------------|-----------|----------|------|---------|
| Checkpoint | `checkpoints/` | `flux1-dev-fp8.safetensors` | ~17GB | Main diffusion model (8-bit quantized) |
| CLIP L | `clip/` | `clip_l.safetensors` | ~246MB | Text encoding |
| T5-XXL | `clip/` or `text_encoders/` | `t5xxl_fp8_e4m3fn.safetensors` | ~4.5GB | Advanced text encoding |
| VAE | `vae/` | `ae.safetensors` | ~80MB | Image decoder |
| LoRA (optional) | `loras/` | `clothes_remover_v0.safetensors` | ~50MB | Enhancement |

**Alternative Flux Variants:**
- `flux1-dev.safetensors` (full precision, ~23GB)
- `flux1-schnell.safetensors` (fast variant, ~23GB)
- `flux1-dev-kontext_fp8_scaled.safetensors` (kontext version)

#### Stable Diffusion 3 (sd3)
**Location:** `/comfyui/models/checkpoints/`

| Filename | Size | Authentication |
|----------|------|----------------|
| `sd3_medium_incl_clips_t5xxlfp8.safetensors` | ~6GB | Required (HuggingFace token) |

**Note:** SD3 includes CLIP and T5 encoders in a single file.

#### SDXL (Stable Diffusion XL)
**Location:** `/comfyui/models/checkpoints/`

| Filename | Purpose |
|----------|---------|
| `sd_xl_base_1.0.safetensors` | Base model |
| `sd_xl_refiner_1.0.safetensors` | Refiner (optional) |

### Video Generation Workflows

#### WAN 2.1 (Text-to-Video)
**Location:** `/comfyui/models/`

| Model Type | Directory | Filename | Size | Purpose |
|------------|-----------|----------|------|---------|
| Diffusion Model | `unet/` or `checkpoints/` | `wan2.1_t2v_1.3B_fp16.safetensors` | ~2.6GB | Main video generation model |
| Text Encoder | `clip/` or `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | ~4.5GB | Text encoding for video |
| VAE | `vae/` | `wan_2.1_vae.safetensors` | ~160MB | Video decoder |

**Workflow Configurations:**
- **Fast:** 512×512, 16 frames, 8 FPS (~15-30 seconds generation)
- **Quality:** 832×480, 33 frames, 16 FPS (~2-3 minutes generation)

---

## API Endpoints

### ComfyUI HTTP API

The handler communicates with ComfyUI running on `127.0.0.1:8188` via the following endpoints:

#### 1. **Health Check**
```http
GET http://127.0.0.1:8188/
```
**Purpose:** Verify ComfyUI server is running  
**Handler Function:** `check_server()`, `_comfy_server_status()`  
**Retry Configuration:**
- Max retries: 500 (configurable via `COMFY_API_AVAILABLE_MAX_RETRIES`)
- Interval: 50ms (configurable via `COMFY_API_AVAILABLE_INTERVAL_MS`)

---

#### 2. **Upload Image**
```http
POST http://127.0.0.1:8188/upload/image
Content-Type: multipart/form-data
```

**Request Body:**
```
image: <binary file data>
overwrite: true
```

**Handler Function:** `upload_images(images)`

**Input Format:**
```json
{
  "images": [
    {
      "name": "input.png",
      "image": "data:image/png;base64,iVBORw0KGgo..."
    }
  ]
}
```

**Features:**
- Strips data URI prefix automatically (`data:image/png;base64,`)
- Supports pure base64 strings
- Sets overwrite flag to replace existing files

**Code Reference:**
```python
# handler.py lines 210-270
def upload_images(images):
    for image in images:
        name = image["name"]
        image_data_uri = image["image"]
        
        # Strip Data URI prefix if present
        if "," in image_data_uri:
            base64_data = image_data_uri.split(",", 1)[1]
        else:
            base64_data = image_data_uri
            
        blob = base64.b64decode(base64_data)
        
        files = {
            "image": (name, BytesIO(blob), "image/png"),
            "overwrite": (None, "true"),
        }
        
        response = requests.post(
            f"http://{COMFY_HOST}/upload/image", 
            files=files, 
            timeout=30
        )
```

---

#### 3. **Queue Workflow (Submit Prompt)**
```http
POST http://127.0.0.1:8188/prompt
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": {
    "6": {
      "inputs": {
        "text": "anime cat...",
        "clip": ["30", 1]
      },
      "class_type": "CLIPTextEncode"
    },
    ...
  },
  "client_id": "uuid-string"
}
```

**Response:**
```json
{
  "prompt_id": "12345-abcde-67890",
  "number": 1,
  "node_errors": {}
}
```

**Handler Function:** `queue_workflow(workflow, client_id)`

**Validation:**
- Returns 400 for invalid workflows
- Includes detailed error messages for missing models
- Auto-detects available models via `/object_info` endpoint

**Error Handling:**
```python
# handler.py lines 332-420
if response.status_code == 400:
    error_data = response.json()
    
    # Extract validation errors
    if "node_errors" in error_data:
        for node_id, node_error in error_data["node_errors"].items():
            error_details.append(f"Node {node_id}: {node_error}")
    
    # Check available models
    available_models = get_available_models()
    if available_models.get("checkpoints"):
        error_message += f"\nAvailable: {', '.join(available_models['checkpoints'])}"
```

---

#### 4. **Get History**
```http
GET http://127.0.0.1:8188/history/{prompt_id}
```

**Response:**
```json
{
  "12345-abcde-67890": {
    "prompt": [...],
    "outputs": {
      "9": {
        "images": [
          {
            "filename": "ComfyUI_00001_.webp",
            "subfolder": "",
            "type": "output"
          }
        ]
      }
    }
  }
}
```

**Handler Function:** `get_history(prompt_id)`

**Purpose:**
- Retrieve completed workflow results
- Get output filenames and metadata
- Access error information if job failed

---

#### 5. **Retrieve Image/Video**
```http
GET http://127.0.0.1:8188/view?filename={name}&subfolder={folder}&type={type}
```

**Query Parameters:**
- `filename`: Output filename (e.g., `ComfyUI_00001_.webp`)
- `subfolder`: Subdirectory path (usually empty `""`)
- `type`: File type (`output`, `input`, `temp`)

**Response:** Binary image/video data

**Handler Function:** `get_image_data(filename, subfolder, image_type)`

**Features:**
- Skips temporary files (`type=temp`)
- Downloads final outputs only
- Supports images and video formats (.webp, .png, .jpg)

**Code Reference:**
```python
# handler.py lines 444-477
def get_image_data(filename, subfolder, image_type):
    data = {"filename": filename, "subfolder": subfolder, "type": image_type}
    url_values = urllib.parse.urlencode(data)
    response = requests.get(
        f"http://{COMFY_HOST}/view?{url_values}", 
        timeout=60
    )
    return response.content
```

---

#### 6. **Get Object Info (Model Discovery)**
```http
GET http://127.0.0.1:8188/object_info
```

**Response:**
```json
{
  "CheckpointLoaderSimple": {
    "input": {
      "required": {
        "ckpt_name": [["flux1-dev-fp8.safetensors", "sd3_medium.safetensors"]]
      }
    }
  },
  "VAELoader": {
    "input": {
      "required": {
        "vae_name": [["ae.safetensors", "wan_2.1_vae.safetensors"]]
      }
    }
  }
}
```

**Handler Function:** `get_available_models()`

**Purpose:**
- Dynamically discover available models
- Validate workflow requirements
- Provide helpful error messages

---

### WebSocket API

#### Connection
```
ws://127.0.0.1:8188/ws?clientId={uuid}
```

**Handler Configuration:**
```python
COMFY_HOST = "127.0.0.1:8188"
client_id = str(uuid.uuid4())
ws_url = f"ws://{COMFY_HOST}/ws?clientId={client_id}"
```

**Features:**
- Real-time execution monitoring
- Progress updates
- Error notifications
- Auto-reconnection on disconnect

---

#### Message Types

**1. Status Update**
```json
{
  "type": "status",
  "data": {
    "status": {
      "exec_info": {
        "queue_remaining": 0
      }
    }
  }
}
```

**2. Execution Progress**
```json
{
  "type": "executing",
  "data": {
    "node": "6",
    "prompt_id": "12345-abcde-67890"
  }
}
```

**3. Execution Complete**
```json
{
  "type": "executing",
  "data": {
    "node": null,
    "prompt_id": "12345-abcde-67890"
  }
}
```
*Note: `node: null` indicates completion*

**4. Execution Error**
```json
{
  "type": "execution_error",
  "data": {
    "prompt_id": "12345-abcde-67890",
    "node_type": "CLIPTextEncode",
    "node_id": "6",
    "exception_message": "Model not found"
  }
}
```

---

#### Reconnection Logic

**Configuration:**
```python
WEBSOCKET_RECONNECT_ATTEMPTS = int(os.environ.get("WEBSOCKET_RECONNECT_ATTEMPTS", 5))
WEBSOCKET_RECONNECT_DELAY_S = int(os.environ.get("WEBSOCKET_RECONNECT_DELAY_S", 3))
```

**Environment Variables:**
- `WEBSOCKET_RECONNECT_ATTEMPTS=5` - Max reconnection attempts
- `WEBSOCKET_RECONNECT_DELAY_S=3` - Delay between attempts (seconds)
- `WEBSOCKET_TRACE=true` - Enable low-level frame debugging

**Handler Function:** `_attempt_websocket_reconnect()`

**Behavior:**
1. Detects websocket connection drop
2. Checks ComfyUI HTTP endpoint health
3. Aborts if ComfyUI is unresponsive (crash/OOM)
4. Retries connection with exponential backoff
5. Resumes message listening after successful reconnect

---

## API Configuration

### Environment Variables

#### Required for ComfyUI Access
```bash
# ComfyUI is hardcoded to run on localhost:8188
# No configuration needed - this is internal container networking
COMFY_HOST="127.0.0.1:8188"
```

#### Optional Configuration
```bash
# API Availability Check
COMFY_API_AVAILABLE_INTERVAL_MS=50      # Wait time between checks
COMFY_API_AVAILABLE_MAX_RETRIES=500      # Max connection attempts

# WebSocket Configuration
WEBSOCKET_RECONNECT_ATTEMPTS=5           # Reconnection attempts
WEBSOCKET_RECONNECT_DELAY_S=3            # Delay between attempts
WEBSOCKET_TRACE=false                    # Enable frame-level debugging

# Worker Behavior
REFRESH_WORKER=false                     # Clean state after each job
SERVE_API_LOCALLY=false                  # Enable local development mode

# Logging
COMFY_LOG_LEVEL=DEBUG                    # ComfyUI verbosity
```

#### S3 Upload Configuration (Optional)
```bash
# If set, outputs are uploaded to S3 instead of returned as base64
BUCKET_ENDPOINT_URL=https://bucket.s3.region.amazonaws.com
BUCKET_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
BUCKET_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCY
```

#### Model Download (Build-time)
```bash
# Required for SD3 and other gated models
HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxxx
```

---

## Workflow Integration

### Workflow Structure

ComfyUI workflows are JSON-based node graphs where each node has:
- **Node ID**: Unique identifier (string number)
- **inputs**: Parameters and connections to other nodes
- **class_type**: Node type (e.g., `CLIPTextEncode`, `VAEDecode`)
- **_meta**: Metadata like title

### Example: Flux Workflow

```json
{
  "input": {
    "workflow": {
      "10": {
        "inputs": {
          "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader",
        "_meta": {
          "title": "Load VAE"
        }
      },
      "11": {
        "inputs": {
          "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
          "clip_name2": "clip_l.safetensors",
          "type": "flux"
        },
        "class_type": "DualCLIPLoader",
        "_meta": {
          "title": "DualCLIPLoader"
        }
      },
      "12": {
        "inputs": {
          "unet_name": "flux1-dev.safetensors",
          "weight_dtype": "fp8_e4m3fn"
        },
        "class_type": "UNETLoader",
        "_meta": {
          "title": "Load Diffusion Model"
        }
      }
    }
  }
}
```

### Model References in Workflows

**Model loaders must reference exact filenames in the model directories:**

| Loader Class | Directory | Input Parameter | Example Value |
|--------------|-----------|-----------------|---------------|
| `CheckpointLoaderSimple` | `checkpoints/` | `ckpt_name` | `flux1-dev-fp8.safetensors` |
| `UNETLoader` | `unet/` | `unet_name` | `flux1-dev.safetensors` |
| `VAELoader` | `vae/` | `vae_name` | `ae.safetensors` |
| `DualCLIPLoader` | `clip/` | `clip_name1`, `clip_name2` | `clip_l.safetensors` |
| `LoraLoader` | `loras/` | `lora_name` | `clothes_remover_v0.safetensors` |
| `ControlNetLoader` | `controlnet/` | `control_net_name` | `control_v11p_sd15_openpose.pth` |

### Dynamic Model Discovery

The handler can check available models:

```python
def get_available_models():
    response = requests.get(f"http://{COMFY_HOST}/object_info", timeout=10)
    object_info = response.json()
    
    if "CheckpointLoaderSimple" in object_info:
        checkpoint_info = object_info["CheckpointLoaderSimple"]
        available_checkpoints = checkpoint_info["input"]["required"]["ckpt_name"][0]
    
    return available_checkpoints
```

---

## Network Volume Support

### Configuration File Location
```
/comfyui/extra_model_paths.yaml
```

### Purpose
Allows sharing models across multiple worker instances via RunPod network volumes, avoiding redundant model downloads per worker.

### Mounting Network Volume

**Docker Compose:**
```yaml
volumes:
  - ./data/runpod-volume:/runpod-volume
```

**RunPod Dashboard:**
1. Create a Network Volume
2. Upload models to `/models/checkpoints/`, `/models/vae/`, etc.
3. Attach volume to serverless endpoint
4. Mount path: `/runpod-volume`

### Model Resolution Priority

ComfyUI checks models in this order:
1. **Built-in path:** `/comfyui/models/{type}/`
2. **Network volume:** `/runpod-volume/models/{type}/`

If a model exists in both locations, the built-in version is used.

---

## Troubleshooting

### Model Not Found Errors

**Symptom:**
```json
{
  "error": "Workflow validation failed: Node 12 (ckpt_name): 'flux1-dev.safetensors' not in list"
}
```

**Solution:**
1. Check model filename matches exactly (case-sensitive)
2. Verify model is in correct directory
3. Check available models via API:
   ```bash
   curl http://127.0.0.1:8188/object_info | jq '.CheckpointLoaderSimple'
   ```

### Connection Refused Errors

**Symptom:**
```
worker-comfyui - ComfyUI server (127.0.0.1:8188) not reachable after multiple retries
```

**Solution:**
1. Check ComfyUI startup logs
2. Increase `COMFY_API_AVAILABLE_MAX_RETRIES`
3. Verify no port conflicts
4. Check container has sufficient GPU memory

### WebSocket Disconnects

**Symptom:**
```
worker-comfyui - Websocket connection closed unexpectedly
```

**Solution:**
1. Enable diagnostics: `WEBSOCKET_TRACE=true`
2. Increase reconnection attempts: `WEBSOCKET_RECONNECT_ATTEMPTS=10`
3. Check ComfyUI didn't crash (OOM, CUDA error)
4. Review ComfyUI logs: `/comfyui/comfyui.log`

### Model Loading Timeout

**Symptom:**
Long delays before workflow execution starts

**Solution:**
1. First run loads models into VRAM (slow)
2. Use fp8 quantized models (faster loading)
3. Keep worker alive with `REFRESH_WORKER=false`
4. Pre-warm models by running test workflow

### S3 Upload Failures

**Symptom:**
```
worker-comfyui - Error uploading ComfyUI_00001_.webp to S3
```

**Solution:**
1. Verify S3 credentials are correct
2. Check bucket permissions (s3:PutObject)
3. Test endpoint URL is accessible
4. Review IAM policy allows bucket access

---

## Quick Reference

### Model Download Commands

**Flux 1-dev fp8:**
```bash
wget -O /comfyui/models/checkpoints/flux1-dev-fp8.safetensors \
  https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors
```

**SD3 (requires token):**
```bash
wget --header="Authorization: Bearer ${HF_TOKEN}" \
  -O /comfyui/models/checkpoints/sd3_medium_incl_clips_t5xxlfp8.safetensors \
  https://huggingface.co/stabilityai/stable-diffusion-3-medium/resolve/main/sd3_medium_incl_clips_t5xxlfp8.safetensors
```

**WAN 2.1:**
```bash
wget -O /comfyui/models/unet/wan2.1_t2v_1.3B_fp16.safetensors \
  https://huggingface.co/Wan-Lab/Wan2.1/resolve/main/wan2.1_t2v_1.3B_fp16.safetensors
```

### Testing API Endpoints

**Health Check:**
```bash
curl http://127.0.0.1:8188/
```

**List Available Models:**
```bash
curl http://127.0.0.1:8188/object_info | jq '.CheckpointLoaderSimple.input.required.ckpt_name'
```

**Queue Workflow:**
```bash
curl -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  -d @test_input.json
```

**Check History:**
```bash
curl http://127.0.0.1:8188/history/YOUR_PROMPT_ID
```

### Container Testing

**Start locally:**
```bash
docker-compose up
```

**Access ComfyUI UI:**
```
http://localhost:8188
```

**Access Worker API:**
```
http://localhost:8000
```

---

## Additional Resources

- [ComfyUI Documentation](https://github.com/comfyanonymous/ComfyUI)
- [RunPod Serverless Docs](https://docs.runpod.io/serverless/overview)
- [Workflow Examples](../test_resources/workflows/)
- [Development Guide](./development.md)
- [Deployment Guide](./deployment.md)
- [Configuration Guide](./configuration.md)

---

**Document Version:** 1.0  
**Last Updated:** November 1, 2025  
**Repository:** comfyui-wan2-2  
**Maintainer:** romantony
