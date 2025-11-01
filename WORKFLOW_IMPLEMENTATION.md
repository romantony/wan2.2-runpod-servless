# WAN 2.2 ComfyUI Workflow Implementation

## Overview

This document describes the ComfyUI workflow implementation for WAN 2.2 models, based on patterns from production-grade systems like SaladTechnologies/comfyui-api.

## Implementation Status

✅ **Completed:**
- Image-to-Video (I2V) workflow with LoRA support
- Sound-to-Video (S2V) workflow  
- ComfyUI client integration in handler.py
- Automatic model detection (11 models verified)

🔄 **Testing Required:**
- End-to-end I2V generation
- LoRA acceleration (4-step vs 20-step)
- S2V workflow validation
- Different model combinations

## Workflow Architecture

### Image-to-Video (I2V) Workflow

The I2V workflow implements a 12-node ComfyUI graph:

```
Input Image → LoadImage (1)
              ↓
        VAEEncode (8) → KSampler (10) → VAEDecode (11) → SaveVideo (12)
              ↑             ↑
          VAELoader (2)    UNetLoader (3)
                           ↓ (optional)
                        LoraLoader (4)
                           ↓
                     DualCLIPLoader (5)
                           ↓
                   CLIPTextEncode (6,7)
                           ↓
                    EmptyLatentVideo (9)
```

**Key Components:**

1. **LoadImage** - Loads the input reference image from ComfyUI uploads
2. **VAELoader** - Loads WAN 2.1 VAE (`wan_2.1_vae.safetensors`)
3. **UNETLoader** - Loads I2V diffusion model:
   - `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` (default)
   - `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` (alternative)
4. **LoraLoader** (optional) - Applies LightX2V acceleration for 4-step inference
5. **DualCLIPLoader** - Loads UMT5-XXL text encoder
6. **CLIPTextEncode** - Encodes positive and negative prompts
7. **EmptyLatentVideo** - Creates empty video latent space
8. **VAEEncode** - Encodes input image to latent
9. **KSampler** - Diffusion sampling for video generation
10. **VAEDecode** - Decodes latent to video frames
11. **VHS_VideoCombine** - Saves video with specified FPS

### Sound-to-Video (S2V) Workflow

Similar structure with audio conditioning:

```
Input Audio → LoadAudio (1)
              ↓
      AudioEncoderLoader (2)
              ↓
        AudioEncode (3) → KSampler (10) → VAEDecode (11) → SaveVideo (12)
                             ↑
                       UNetLoader (5)
                             ↓
                    DualCLIPLoader (6)
                             ↓
                   CLIPTextEncode (7,8)
                             ↓
                    EmptyLatentVideo (9)
```

## Function API

### create_i2v_workflow()

```python
def create_i2v_workflow(
    image_filename,                # Name of uploaded image in ComfyUI
    diffusion_model="wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
    vae_model="wan_2.1_vae.safetensors",
    text_encoder="umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    prompt="",                     # Text prompt for generation
    seed=-1,                       # Random seed (-1 = random)
    steps=20,                      # Diffusion steps (use 4 with LoRA)
    cfg_scale=7.0,                 # Classifier-free guidance
    width=1280,                    # Output width
    height=720,                    # Output height
    num_frames=121,                # Number of frames
    fps=24,                        # Frames per second
    use_lora=False,                # Enable LightX2V acceleration
    lora_name="wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
    lora_strength=1.0,             # LoRA strength
    sampler_name="euler",          # Sampler algorithm
    scheduler="normal",            # Scheduler type
    denoise=1.0                    # Denoising strength
) -> dict
```

**Returns:** ComfyUI workflow dictionary (node-based prompt format)

### create_s2v_workflow()

```python
def create_s2v_workflow(
    audio_filename,                # Name of uploaded audio in ComfyUI
    diffusion_model="wan2.2_s2v_14B_fp8_scaled.safetensors",
    vae_model="wan_2.1_vae.safetensors",
    audio_encoder="wav2vec2_large_english_fp16.safetensors",
    text_encoder="umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    prompt="",
    seed=-1,
    steps=20,
    cfg_scale=7.0,
    width=1280,
    height=720,
    num_frames=121,
    fps=24,
    sampler_name="euler",
    scheduler="normal",
    denoise=1.0
) -> dict
```

## Handler Integration

The workflows are integrated into `src/handler.py`:

```python
# Image-to-Video endpoint
async def handle_comfyui_i2v(event):
    # 1. Download/get input image
    image_path = _download_ref_image(params)
    
    # 2. Upload to ComfyUI
    image_name = f"{rid}_input.png"
    comfyui_client.upload_image(image_path, image_name)
    
    # 3. Create workflow
    workflow = create_i2v_workflow(
        image_filename=image_name,
        diffusion_model=params.get("diffusion_model"),
        prompt=params.get("prompt", ""),
        use_lora=params.get("use_lora", False)
    )
    
    # 4. Execute on ComfyUI
    result = comfyui_client.execute_workflow(workflow, timeout=600)
    
    # 5. Return video URL
    return {"video_url": result["outputs"][0]["url"]}
```

## API Usage Examples

### Basic I2V Generation

```bash
curl -X POST https://api.runpod.ai/v2/c5tcnbrax0chts/run \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "comfyui_i2v",
      "image_url": "https://example.com/input.jpg",
      "prompt": "A beautiful sunset over the ocean",
      "steps": 20,
      "cfg_scale": 7.0
    }
  }'
```

### I2V with LoRA Acceleration (4-step)

```bash
curl -X POST https://api.runpod.ai/v2/c5tcnbrax0chts/run \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "comfyui_i2v",
      "image_base64": "data:image/png;base64,iVBORw0KG...",
      "prompt": "Dynamic camera movement through a forest",
      "use_lora": true,
      "steps": 4,
      "cfg_scale": 7.0
    }
  }'
```

### High Noise vs Low Noise Models

**High Noise** (default) - Better for dynamic scenes with motion:
```json
{
  "diffusion_model": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
  "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
}
```

**Low Noise** - Better for subtle movements:
```json
{
  "diffusion_model": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
  "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
}
```

## Model Configuration

### Available Models (Detected in /runpod-volume/models/)

**Diffusion Models (4):**
- `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`
- `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`
- `wan2.2_s2v_14B_fp8_scaled.safetensors`
- `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors`

**LoRAs (5):**
- `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors`
- `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors`
- `wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors`
- `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors`
- `WanAnimate_relight_lora_fp16.safetensors`

**VAEs (2):**
- `wan_2.1_vae.safetensors` (default)
- `pixel_space` (alternative)

### Model Selection Strategy

1. **Task-Specific Models:**
   - I2V High Noise: Dynamic scenes, camera movement
   - I2V Low Noise: Subtle motion, character animation
   - S2V: Audio-synchronized video
   - Animate: Full animation from text

2. **Acceleration:**
   - Standard: 20 steps, no LoRA
   - Fast: 4 steps, LightX2V LoRA (5x speedup)

3. **Quality vs Speed:**
   - High quality: 20 steps, cfg_scale=7.0
   - Balanced: 4 steps + LoRA, cfg_scale=7.0
   - Fast preview: 4 steps + LoRA, cfg_scale=3.0

## ComfyUI Node Types

The workflows use standard ComfyUI nodes:

### Loaders
- `LoadImage` - Loads image from uploads
- `LoadAudio` - Loads audio file
- `VAELoader` - Loads VAE model
- `UNETLoader` - Loads diffusion model
- `LoraLoader` - Loads LoRA acceleration
- `DualCLIPLoader` - Loads text encoder

### Encoders
- `CLIPTextEncode` - Encodes text prompts
- `VAEEncode` - Encodes image to latent
- `AudioEncode` - Encodes audio

### Samplers
- `KSampler` - Diffusion sampling

### Decoders
- `VAEDecode` - Decodes latent to pixels

### Video
- `EmptyLatentVideo` - Creates video latent space
- `VHS_VideoCombine` - Combines frames and saves video

### Audio (S2V)
- `AudioEncoderLoader` - Loads Wav2Vec2

## Testing

### Test Script Template

```python
import requests
import base64

# Read test image
with open("test_image.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

# Submit I2V request
response = requests.post(
    "https://api.runpod.ai/v2/c5tcnbrax0chts/run",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "input": {
            "action": "comfyui_i2v",
            "image_base64": f"data:image/jpeg;base64,{image_b64}",
            "prompt": "A serene lake with gentle ripples",
            "steps": 4,
            "use_lora": True,
            "cfg_scale": 7.0
        }
    }
)

job_id = response.json()["id"]

# Poll for results
while True:
    status = requests.get(
        f"https://api.runpod.ai/v2/c5tcnbrax0chts/status/{job_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    ).json()
    
    if status["status"] == "COMPLETED":
        video_url = status["output"]["video_url"]
        print(f"Video ready: {video_url}")
        break
    elif status["status"] == "FAILED":
        print(f"Error: {status['error']}")
        break
    
    time.sleep(5)
```

## Troubleshooting

### Common Issues

1. **"Missing node type: EmptyLatentVideo"**
   - **Cause:** ComfyUI video nodes not installed
   - **Solution:** Install ComfyUI-VideoHelperSuite custom node pack

2. **"Missing node type: VHS_VideoCombine"**
   - **Cause:** Video Helper Suite not installed
   - **Solution:** `git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite`

3. **"Model not found: wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"**
   - **Cause:** extra_model_paths.yaml not configured correctly
   - **Solution:** Verify `/runpod-volume/models/` path in extra_model_paths.yaml

4. **"CUDA out of memory"**
   - **Cause:** Model too large for GPU
   - **Solution:** 
     - Use fp8 models (already using these)
     - Reduce num_frames
     - Reduce resolution (width/height)

5. **Slow generation (>5 minutes)**
   - **Cause:** Not using LoRA acceleration
   - **Solution:** Set `use_lora=true, steps=4`

## Performance Benchmarks

**RTX 5090 Pro (Expected):**

| Configuration | Steps | Resolution | Frames | Time |
|--------------|-------|------------|--------|------|
| Standard     | 20    | 1280x720   | 121    | ~8min |
| LoRA Fast    | 4     | 1280x720   | 121    | ~2min |
| LoRA 480p    | 4     | 854x480    | 121    | ~1min |

## References

- [SaladTechnologies/comfyui-api](https://github.com/SaladTechnologies/comfyui-api) - Production workflow patterns
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Video nodes
- WAN 2.2 Reference Architecture (doc/Ref_Architecture.md)
- Model Detection Test Results (test_models.py)

## Next Steps

1. **Test I2V Generation:**
   ```bash
   python test_jetski_simple.py
   ```

2. **Commit and Deploy:**
   ```bash
   git add src/comfyui_client.py WORKFLOW_IMPLEMENTATION.md
   git commit -m "Implement I2V and S2V workflow functions with ComfyUI nodes"
   git push origin main
   ```

3. **Wait for Build:**
   - CI/CD will automatically rebuild (~15-20 min)
   - Monitor at RunPod dashboard

4. **Validate:**
   - Test I2V with different models
   - Compare 4-step LoRA vs 20-step standard
   - Test S2V workflow

5. **Optimize:**
   - Fine-tune sampler settings
   - Test different schedulers
   - Optimize video encoding parameters
