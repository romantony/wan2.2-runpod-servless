# Deployment Status - WAN 2.2 RunPod Serverless

> **Current State:** CI/CD Active - Automatic builds on git push

---

## Current Setup

### Repository Integration ✅

**GitHub Repository:** `romantony/wan2.2-runpod-servless`  
**Branch:** `main`  
**CI/CD Status:** **Active** - Builds automatically on push

### What Happens on Each Commit

1. **Push to GitHub** → Triggers RunPod build
2. **Docker Build** → RunPod builds your Dockerfile
3. **Image Push** → New image pushed to registry
4. **Auto-Deploy** → Serverless workers update to new image
5. **Ready** → API endpoints available with latest code

### Current Configuration

```yaml
# runpod.yaml
name: wan22-i2v-a14b-serverless
gpu: "NVIDIA RTX 5090"
containerDiskGB: 40
imageName: "<YOUR_REGISTRY>/wan22-runpod-serverless:latest"

env:
  - key: WAN_CKPT_DIR
    value: "/workspace/models"
  - key: RUNPOD_MAX_CONCURRENCY
    value: "1"
  - key: COMFYUI_ROOT
    value: "/workspace/runpod-slim/ComfyUI"
```

---

## Recent Changes (Ready for Next Build)

### ✅ Completed Integrations

1. **ComfyUI Integration**
   - Dockerfile updated with ComfyUI paths
   - Bootstrap script starts ComfyUI server
   - Handler.py routes API requests
   - Model path configuration via `extra_model_paths.yaml`

2. **API Routing**
   - `comfyui_workflow` - Execute custom workflows
   - `comfyui_i2v` - Image-to-video generation
   - `comfyui_models` - List available models
   - `request/generate/create` - WAN 2.2 CLI
   - `status/get/result` - Job status checking

3. **Model Configuration**
   - `/workspace/models/` structure defined
   - `extra_model_paths.yaml` configuration created
   - 73GB model inventory documented
   - Storage best practices documented

### Files Modified in Latest Commit

**Dockerfile:**
- Added COMFYUI_ROOT, COMFYUI_HOST, COMFYUI_PORT env vars
- Changed ComfyUI clone path to `/workspace/runpod-slim/ComfyUI`
- Added `extra_model_paths.yaml` copy to container

**bootstrap.sh:**
- Added ComfyUI startup in background
- Created symlink logic for `extra_model_paths.yaml`
- Added health check wait loop (60s timeout)
- Starts RunPod handler after ComfyUI ready

**handler.py:**
- Added `comfyui_client` import
- Added `handle_comfyui_workflow()` function
- Added `handle_comfyui_i2v()` function
- Added `handle_comfyui_models()` function
- Updated `handler()` with action routing

**New Files:**
- `src/comfyui_client.py` - Complete ComfyUI API client
- `doc/API_Documentation.md` - Full API reference
- `doc/WAN2.2_Implementation.md` - Model guide
- `doc/Storage_Migration_Guide.md` - Migration instructions
- `doc/Storage_Strategy_Summary.md` - Best practices
- `extra_model_paths.yaml` - Model path configuration

---

## What Will Happen on Next Push

### Build Process

1. **Dockerfile Execution:**
   ```dockerfile
   # Install base dependencies
   RUN apt-get update && install packages...
   
   # Install PyTorch + CUDA
   RUN pip install torch torchvision torchaudio
   
   # Clone WAN 2.2
   RUN git clone https://github.com/Wan-Video/Wan2.2.git
   
   # Clone ComfyUI
   RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/runpod-slim/ComfyUI
   
   # Copy configurations
   COPY extra_model_paths.yaml /workspace/extra_model_paths.yaml
   COPY src /workspace/src
   COPY scripts /workspace/scripts
   ```

2. **Container Startup:**
   ```bash
   # bootstrap.sh executes:
   - Setup model paths
   - Create/symlink extra_model_paths.yaml
   - Start ComfyUI on port 8188
   - Wait for ComfyUI ready (up to 60s)
   - Start RunPod handler
   ```

3. **API Availability:**
   - WAN 2.2 CLI endpoints active
   - ComfyUI workflow endpoints active
   - Health check endpoint ready

### Expected Build Time

- **Cold Build:** ~15-20 minutes (first time or after dependency changes)
  - Base image pull: ~2 min
  - Package installation: ~3 min
  - WAN 2.2 clone + install: ~5 min
  - ComfyUI clone + install: ~2 min
  - Flash-attn compilation: ~5-8 min
  
- **Warm Build:** ~5-10 minutes (code changes only)
  - Uses cached layers
  - Only rebuilds changed files

### Worker Startup Time

- **Container Init:** ~30 seconds
- **ComfyUI Startup:** ~10-30 seconds (model detection)
- **Total Ready Time:** ~1-2 minutes after deployment

---

## Testing After Deployment

### 1. Health Check
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"health": true}}'
```

**Expected Response:**
```json
{
  "ok": true,
  "wan_home": "/workspace/Wan2.2",
  "ckpt_dir": "/workspace/models",
  "comfyui_url": "http://127.0.0.1:8188",
  "comfyui_status": "online"
}
```

### 2. List Available Models
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"action": "comfyui_models"}}'
```

**Expected Response:**
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
    "loras": [ /* 5 LoRAs */ ]
  }
}
```

### 3. Test I2V Generation (Fast Mode)
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "comfyui_i2v",
      "reference_image_url": "https://example.com/test.jpg",
      "prompt": "person smiling",
      "diffusion_model": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
      "steps": 4,
      "use_lora": true,
      "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
      "return_video": true
    }
  }'
```

---

## Known Limitations (Current Build)

### Not Yet Implemented

1. **Custom ComfyUI Workflows**
   - Basic I2V workflow template exists
   - Need actual WAN 2.2 ComfyUI node configuration
   - Workflow JSON needs to match installed nodes

2. **S2V (Sound-to-Video)**
   - Handler routing exists
   - Workflow template needs customization
   - Audio upload mechanism needs testing

3. **Model Auto-Discovery**
   - `get_available_models()` implemented
   - May need refinement based on actual ComfyUI response format

4. **Output Retrieval**
   - Base64 encoding works
   - Large video file handling needs testing
   - Timeout settings may need adjustment

### Pending Validation

- [ ] ComfyUI successfully starts in container
- [ ] Models detected at `/workspace/models/` path
- [ ] `extra_model_paths.yaml` symlink created correctly
- [ ] API routing works end-to-end
- [ ] Image upload to ComfyUI succeeds
- [ ] Workflow execution completes
- [ ] Output retrieval works for large videos

---

## Rollback Plan

If deployment fails or has issues:

### Option 1: Quick Rollback (Git)
```bash
# Revert last commit
git revert HEAD
git push origin main

# Triggers new build with previous state
```

### Option 2: Force Previous Image
```bash
# In RunPod Dashboard:
# Change image tag to previous version
# Example: your-registry/wan22-runpod-serverless:previous-tag
```

### Option 3: Emergency Disable
```bash
# In RunPod Dashboard:
# Set "Active Workers" to 0
# Stops accepting new jobs
```

---

## Monitoring & Logs

### Check Build Status
- **GitHub Actions:** Check `.github/workflows/` for CI logs (if configured)
- **RunPod Dashboard:** View build logs in Serverless → Endpoints → Logs

### Runtime Logs
```bash
# In RunPod Dashboard:
# Endpoints → Your Endpoint → Logs → View Worker Logs

# Look for:
[bootstrap] ===== WAN 2.2 + ComfyUI Setup =====
[bootstrap] ComfyUI is ready!
[bootstrap] Starting RunPod handler...
```

### Error Indicators

**ComfyUI Failed to Start:**
```
[bootstrap] WARNING: ComfyUI did not start within 60s
```
→ Check `/tmp/comfyui.log` for errors

**Model Not Found:**
```
error: Model 'xyz.safetensors' not found in /workspace/models/
```
→ Verify network volume mount and model files

**Handler Crash:**
```
Traceback (most recent call last):
  File "/workspace/src/handler.py", line X
```
→ Check handler.py syntax and imports

---

## Next Steps After Deployment

### Immediate (Next 1-2 hours)

1. **Push Current Changes**
   ```bash
   git add .
   git commit -m "Add ComfyUI integration + API routing"
   git push origin main
   ```

2. **Monitor Build**
   - Watch RunPod build logs
   - Expect 15-20 minute build time
   - Check for any compilation errors

3. **Test Health Check**
   - Use curl command above
   - Verify `comfyui_status: "online"`

4. **Test Model Detection**
   - List models via API
   - Confirm all 4 diffusion models visible

### Short-term (Next 24 hours)

5. **Create Actual ComfyUI Workflows**
   - Export workflow JSON from ComfyUI UI
   - Replace template in `comfyui_client.py`
   - Test with actual WAN 2.2 nodes

6. **Test I2V Generation**
   - Small test image (512x512)
   - 4-step LoRA mode
   - Verify output retrieval

7. **Optimize Workflow Templates**
   - Add S2V workflow
   - Add Animation workflow
   - Test all variants

### Long-term (Next Week)

8. **Performance Testing**
   - Benchmark generation times
   - Test concurrent requests
   - Monitor GPU memory usage

9. **Error Handling**
   - Add retry logic
   - Improve error messages
   - Add timeout handling

10. **Documentation**
    - Add workflow examples
    - Create troubleshooting guide
    - Document API usage patterns

---

## Success Criteria

### Build Success ✅
- [ ] Docker build completes without errors
- [ ] Image pushed to registry
- [ ] Workers deployed and active

### Runtime Success ✅
- [ ] Health check returns `ok: true`
- [ ] ComfyUI status is `online`
- [ ] Models list returns 4 diffusion models
- [ ] Handler responds to all action types

### Functional Success ✅
- [ ] Image upload to ComfyUI works
- [ ] Workflow execution completes
- [ ] Video output retrieved successfully
- [ ] No OOM errors during generation

---

## Support Resources

- **API Documentation:** `doc/API_Documentation.md`
- **Model Guide:** `doc/WAN2.2_Implementation.md`
- **Storage Guide:** `doc/Storage_Migration_Guide.md`
- **RunPod Docs:** https://docs.runpod.io/serverless/overview
- **ComfyUI Docs:** https://github.com/comfyanonymous/ComfyUI
- **WAN 2.2 Repo:** https://github.com/Wan-Video/Wan2.2

---

## Contact

**Repository:** https://github.com/romantony/wan2.2-runpod-servless  
**Issues:** https://github.com/romantony/wan2.2-runpod-servless/issues

---

**Document Version:** 1.0  
**Last Updated:** November 1, 2025  
**Status:** Ready for Deployment ✅
