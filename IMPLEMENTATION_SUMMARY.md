# WAN 2.2 I2V & S2V Workflow Implementation - Summary

## What Was Done

Based on the production-grade patterns from [SaladTechnologies/comfyui-api](https://github.com/SaladTechnologies/comfyui-api), I've implemented complete ComfyUI workflow generation functions for WAN 2.2 models.

## Files Changed

### 1. `src/comfyui_client.py`
**Status:** ✅ Implemented

#### create_i2v_workflow()
- **Purpose:** Generate ComfyUI workflow for Image-to-Video
- **Nodes:** 12-node graph (LoadImage → VAEEncode → KSampler → VAEDecode → SaveVideo)
- **Features:**
  - Automatic seed generation (if -1)
  - Optional LoRA acceleration (4-step vs 20-step)
  - Configurable resolution, frames, FPS
  - High/low noise model support
  - Proper node connections following ComfyUI standards

**Key Parameters:**
```python
def create_i2v_workflow(
    image_filename,                # Uploaded image name
    diffusion_model="wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
    vae_model="wan_2.1_vae.safetensors",
    prompt="",
    steps=20,                      # 4 with LoRA, 20 without
    use_lora=False,                # LightX2V acceleration
    width=1280,
    height=720,
    num_frames=121,
    fps=24,
    ...
)
```

**Workflow Structure:**
```
1. LoadImage - Load input image from ComfyUI uploads
2. VAELoader - Load WAN 2.1 VAE
3. UNETLoader - Load I2V diffusion model
4. LoraLoader (optional) - Apply LightX2V for 4-step inference
5. DualCLIPLoader - Load UMT5-XXL text encoder
6. CLIPTextEncode - Encode positive prompt
7. CLIPTextEncode - Encode negative prompt
8. VAEEncode - Encode image to latent
9. EmptyLatentVideo - Create video latent space
10. KSampler - Diffusion sampling
11. VAEDecode - Decode to video frames
12. VHS_VideoCombine - Save video
```

#### create_s2v_workflow()
- **Purpose:** Generate ComfyUI workflow for Sound-to-Video
- **Nodes:** 12-node graph with audio conditioning
- **Features:**
  - LoadAudio + AudioEncode integration
  - Wav2Vec2 audio encoder support
  - Audio-conditioned KSampler
  - Same video output pipeline as I2V

**Key Parameters:**
```python
def create_s2v_workflow(
    audio_filename,                # Uploaded audio name
    diffusion_model="wan2.2_s2v_14B_fp8_scaled.safetensors",
    audio_encoder="wav2vec2_large_english_fp16.safetensors",
    ...
)
```

### 2. `test_jetski_simple.py`
**Status:** ✅ Updated

**Changes:**
- Removed old `motion_bucket_id` and `noise_aug_strength` (SVD-specific)
- Added WAN 2.2 specific parameters:
  - `diffusion_model` - Select I2V model variant
  - `vae_model` - VAE model name
  - `lora_name` - LoRA acceleration model
  - `use_lora` - Enable/disable LoRA
- Updated payload structure to match handler expectations
- Fixed parameter display to show WAN 2.2 settings

### 3. `WORKFLOW_IMPLEMENTATION.md`
**Status:** ✅ Created

**Contents:**
- Complete workflow architecture documentation
- Node-by-node breakdown with diagrams
- API usage examples
- Model selection guide
- Performance benchmarks
- Troubleshooting guide
- Testing instructions

## Technical Details

### ComfyUI Node Types Used

**Loaders:**
- `LoadImage` - Standard ComfyUI image loader
- `LoadAudio` - Audio file loader
- `VAELoader` - VAE model loader
- `UNETLoader` - Diffusion model loader
- `LoraLoader` - LoRA weight loader
- `DualCLIPLoader` - Text encoder loader
- `AudioEncoderLoader` - Wav2Vec2 loader (S2V)

**Encoders:**
- `CLIPTextEncode` - Text prompt encoder
- `VAEEncode` - Image to latent encoder
- `AudioEncode` - Audio to latent encoder (S2V)

**Samplers:**
- `KSampler` - Main diffusion sampler

**Decoders:**
- `VAEDecode` - Latent to pixels

**Video:**
- `EmptyLatentVideo` - Create video latent space
- `VHS_VideoCombine` - Combine frames and save video

### Model Compatibility

**Verified Models (from test_models.py):**

✅ **Diffusion Models (4):**
- wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors ✓
- wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors ✓
- wan2.2_s2v_14B_fp8_scaled.safetensors ✓
- Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors ✓

✅ **LoRAs (5):**
- wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors ✓
- wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors ✓
- wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors ✓
- lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors ✓
- WanAnimate_relight_lora_fp16.safetensors ✓

✅ **VAEs (2):**
- wan_2.1_vae.safetensors ✓
- pixel_space ✓

### Implementation Pattern

Based on SaladTechnologies/comfyui-api:

1. **Input Validation** - Type-safe parameters with defaults
2. **Node Graph Construction** - Proper node connections using [node_id, output_index]
3. **Conditional Logic** - LoRA only added if use_lora=True
4. **Metadata** - All nodes have descriptive _meta.title
5. **Random Seeds** - Auto-generate if -1 passed

### Integration Points

**Handler (src/handler.py) calls workflow like this:**

```python
# In handle_comfyui_i2v()
workflow = create_i2v_workflow(
    image_filename=uploaded_image_name,
    diffusion_model=params.get("diffusion_model", "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"),
    prompt=params.get("prompt", ""),
    use_lora=params.get("use_lora", False),
    steps=params.get("steps", 20),
    ...
)

result = comfyui_client.execute_workflow(workflow, timeout=600)
```

**API Request Format:**

```json
{
  "input": {
    "action": "comfyui_i2v",
    "image_base64": "base64-encoded-image...",
    "prompt": "A jetski gliding through calm ocean waters",
    "steps": 4,
    "use_lora": true,
    "cfg_scale": 7.0,
    "num_frames": 49,
    "fps": 24,
    "width": 768,
    "height": 512
  }
}
```

## What's Next

### 1. Test the Implementation (IMMEDIATE)

```bash
# Test I2V generation with LoRA (4-step fast)
python test_jetski_simple.py test_jetski.jpg

# If test fails locally (expected - need ComfyUI server):
# Commit and deploy to test on actual RunPod environment
```

### 2. Commit and Deploy

```bash
git add src/comfyui_client.py test_jetski_simple.py WORKFLOW_IMPLEMENTATION.md IMPLEMENTATION_SUMMARY.md
git commit -m "Implement WAN 2.2 I2V and S2V workflows based on SaladTechnologies patterns

- Complete 12-node workflow generation for I2V
- Complete 12-node workflow generation for S2V  
- Support for LoRA acceleration (4-step inference)
- High/low noise model variants
- Proper ComfyUI node connections
- Updated test scripts with WAN 2.2 parameters
- Comprehensive documentation"

git push origin main
```

### 3. Wait for Build (~15-20 minutes)

Monitor at RunPod dashboard: https://runpod.io/console/serverless

### 4. Test Endpoints

**I2V with LoRA (fast 4-step):**
```bash
python test_jetski_simple.py test_jetski.jpg \
  --steps 4 \
  --use-lora \
  --prompt "Jetski racing through waves"
```

**I2V Standard (20-step):**
```bash
python test_jetski_simple.py test_jetski.jpg \
  --steps 20 \
  --prompt "Smooth sailing on calm waters"
```

**Low Noise Model:**
```bash
python test_jetski_simple.py test_jetski.jpg \
  --diffusion-model wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors \
  --lora-name wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
```

### 5. Potential Issues to Watch For

1. **Missing ComfyUI Nodes:**
   - If EmptyLatentVideo or VHS_VideoCombine not found
   - Solution: Install ComfyUI-VideoHelperSuite in Dockerfile

2. **Node Connection Errors:**
   - If output indices don't match
   - Solution: Adjust [node_id, output_index] based on actual node outputs

3. **Model Loading Issues:**
   - If CLIP/text encoder loading fails
   - Solution: May need to use CheckpointLoaderSimple instead of separate loaders

4. **Memory Issues:**
   - If CUDA OOM on RTX 5090
   - Solution: Reduce num_frames or resolution

### 6. Performance Expectations

**On RTX 5090 Pro:**

| Configuration | Resolution | Frames | Expected Time |
|--------------|-----------|--------|---------------|
| LoRA 4-step  | 1280x720  | 121    | ~2 minutes    |
| LoRA 4-step  | 768x512   | 49     | ~45 seconds   |
| Standard 20  | 1280x720  | 121    | ~8 minutes    |
| Standard 20  | 768x512   | 49     | ~3 minutes    |

## Key Learnings from SaladTechnologies/comfyui-api

1. **Workflow Structure:** Dictionary of node_id → node_config
2. **Node Format:** `{ inputs: {...}, class_type: "...", _meta: {...} }`
3. **Connections:** Use `[node_id, output_index]` to reference outputs
4. **Images:** LoadImage node accepts base64 or URL in inputs.image
5. **Video:** VHS_VideoCombine is standard for video output
6. **LoRAs:** Connected to model output, apply to both model and CLIP
7. **Validation:** Use Zod schemas (TypeScript) or similar for input validation
8. **Defaults:** Always provide sensible defaults for all parameters

## References

- [SaladTechnologies/comfyui-api](https://github.com/SaladTechnologies/comfyui-api) - Production workflow patterns
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Video nodes
- WAN 2.2 Model List (test_models.py output)
- Handler Integration (src/handler.py lines 410-450)

## Success Criteria

✅ **Implementation Complete:**
- [x] create_i2v_workflow() function implemented
- [x] create_s2v_workflow() function implemented
- [x] 12-node ComfyUI graphs properly structured
- [x] LoRA support with conditional logic
- [x] Proper node connections with [id, index] format
- [x] Comprehensive documentation
- [x] Test scripts updated

⏳ **Testing Pending:**
- [ ] End-to-end I2V generation
- [ ] LoRA acceleration validation (4-step)
- [ ] High noise vs low noise comparison
- [ ] S2V workflow test
- [ ] Model switching test

🎯 **Final Goal:**
Working I2V and S2V generation through ComfyUI API with proper workflow execution and video output.
