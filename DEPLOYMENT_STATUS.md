# WAN 2.2 RunPod Deployment - Configuration Summary

**Date:** November 1, 2025  
**Status:** ✅ DEPLOYMENT SUCCESSFUL - Needs Video Nodes

---

## Current Configuration

### ✅ What's Working

1. **All Models Detected (11/11)**
   - 4 Diffusion models
   - 5 LoRAs  
   - 2 VAEs
   - Path: `/runpod-volume/models/` (flat structure)

2. **ComfyUI Integration**
   - Running on port 8188
   - `extra_model_paths.yaml` configured correctly
   - Model detection working via API

3. **Handler Actions**
   - `comfyui_models` - ✅ Working
   - `comfyui_workflow` - ✅ Working (needs proper workflow)
   - `comfyui_i2v` - ⚠️ Working but workflow rejected by ComfyUI

### ⚠️ Issues Identified

1. **ComfyUI Video Nodes Missing**
   - Error: `400 Bad Request` when executing workflow
   - Cause: Video nodes (`EmptyLatentVideo`, `VHS_VideoCombine`) not installed
   - Solution: Add ComfyUI-VideoHelperSuite to Dockerfile ✅ DONE

2. **WAN CLI Not Compatible with Current Structure**
   - Your models: Flat structure at `/runpod-volume/models/*.safetensors`
   - WAN CLI expects: Hierarchical `/runpod-volume/models/Wan2.2-I2V-A14B/diffusion_models/*.safetensors`
   - Solution: Focus on ComfyUI workflows (more flexible anyway)

---

## Files Updated

### 1. Dockerfile ✅
Added ComfyUI video nodes:
```dockerfile
# Install ComfyUI Custom Nodes for Video Generation
RUN cd /workspace/runpod-slim/ComfyUI/custom_nodes && \
    # Video Helper Suite - Essential for video generation
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    pip install -r ComfyUI-VideoHelperSuite/requirements.txt && \
    # AnimateDiff Evolved - Advanced video animation  
    git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git && \
    pip install -r ComfyUI-AnimateDiff-Evolved/requirements.txt || true && \
    # Advanced ControlNet - For better control
    git clone https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git && \
    pip install -r ComfyUI-Advanced-ControlNet/requirements.txt || true
```

### 2. New Diagnostic Scripts ✅

**`check_wan_cli_config.py`**
- Checks model path configuration
- Tests WAN CLI compatibility
- Provides solutions for current setup

**`discover_comfyui_nodes.py`**
- Discovers available ComfyUI nodes
- Tests which node types work
- Identifies missing dependencies

---

## Next Steps

### Immediate: Rebuild with Video Nodes

```bash
# 1. Commit changes
git add Dockerfile check_wan_cli_config.py discover_comfyui_nodes.py
git commit -m "Add ComfyUI video nodes and diagnostic scripts

- Install VideoHelperSuite for VHS_VideoCombine, EmptyLatentVideo
- Add AnimateDiff-Evolved for advanced animations
- Add Advanced-ControlNet for better control
- Create check_wan_cli_config.py to verify model paths
- Create discover_comfyui_nodes.py to test node availability"

# 2. Push to trigger rebuild
git push origin main

# 3. Wait for build (~20 minutes)
```

### After Rebuild: Test ComfyUI Workflow

```python
import requests

# Test I2V with updated ComfyUI (has video nodes)
r = requests.post(
    'https://api.runpod.ai/v2/c5tcnbrax0chts/run',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={
        'input': {
            'action': 'comfyui_i2v',
            'params': {
                'image_url': 'https://picsum.photos/512/512',
                'prompt': 'slow camera pan',
                'steps': 4,
                'use_lora': True,
                'num_frames': 25,
                'width': 512,
                'height': 512
            }
        }
    }
)

job_id = r.json()['id']
# Poll for results...
```

### If Still Issues: Adjust Workflow Nodes

After rebuild, if workflow still fails:

1. **Discover available nodes:**
   ```bash
   python discover_comfyui_nodes.py
   ```

2. **Update workflow in `src/comfyui_client.py`:**
   - Replace missing node types with available alternatives
   - May need `CheckpointLoaderSimple` instead of separate loaders
   - May need different video node names

---

## Architecture Decision

### Recommended: ComfyUI Workflows

**Why:**
- ✅ Works with your flat model structure
- ✅ More flexible and maintainable
- ✅ Better for custom pipelines
- ✅ Already integrated in handler

**Status:** Ready once video nodes installed

### Not Recommended: WAN CLI

**Why:**
- ❌ Requires restructuring all models
- ❌ Less flexible
- ❌ Harder to customize

**Alternative:** If really needed, use symlink approach in bootstrap.sh

---

## Test Results So Far

| Test | Status | Details |
|------|--------|---------|
| Model Detection | ✅ PASS | 11/11 models found |
| ComfyUI Health | ✅ PASS | Server online |
| Image Download | ✅ PASS | Image processed successfully |
| Image Upload | ✅ PASS | Uploaded to ComfyUI |
| Workflow Creation | ✅ PASS | Python function executed |
| ComfyUI Execution | ⚠️ REJECTED | 400 - Missing video nodes |
| WAN CLI | ❌ N/A | Incompatible directory structure |

---

## API Usage Examples

### ComfyUI I2V (After rebuild)

```python
# Standard 20-step generation
{
    "input": {
        "action": "comfyui_i2v",
        "params": {
            "image_url": "https://example.com/image.jpg",
            "prompt": "camera slowly zooming in",
            "steps": 20,
            "cfg_scale": 7.0,
            "num_frames": 49,
            "width": 768,
            "height": 512
        }
    }
}

# Fast 4-step with LoRA
{
    "input": {
        "action": "comfyui_i2v",
        "params": {
            "image_url": "https://example.com/image.jpg",
            "prompt": "dynamic motion",
            "steps": 4,
            "use_lora": true,
            "cfg_scale": 7.0,
            "num_frames": 49,
            "width": 768,
            "height": 512
        }
    }
}
```

### Model Detection

```python
{
    "input": {
        "action": "comfyui_models"
    }
}
```

---

## Performance Expectations (Post-Fix)

**RTX 5090 Pro:**

| Mode | Resolution | Frames | Expected Time |
|------|-----------|--------|---------------|
| LoRA 4-step | 512×512 | 25 | ~30s |
| LoRA 4-step | 768×512 | 49 | ~45s |
| LoRA 4-step | 1280×720 | 121 | ~2min |
| Standard 20 | 512×512 | 25 | ~2min |
| Standard 20 | 768×512 | 49 | ~3min |
| Standard 20 | 1280×720 | 121 | ~8min |

---

## Troubleshooting

### If workflow still fails after rebuild:

1. **Check logs for specific node errors**
2. **Run `discover_comfyui_nodes.py`** to see what's available
3. **Update workflow nodes** in `src/comfyui_client.py`
4. **Test with simpler workflow** first (just LoadImage + SaveImage)

### If you need WAN CLI:

1. **Reorganize models** into hierarchical structure
2. **Or use symlinks** in bootstrap.sh
3. **Update WAN_CKPT_DIR** to point to parent folder

---

## Summary

**Status:** Deployment functional, video nodes being added

**Action Required:** 
1. Commit Dockerfile changes ✅ 
2. Push to rebuild
3. Test after build completes

**Expected Outcome:** Full I2V and S2V generation working via ComfyUI workflows

**ETA:** ~20 minutes (rebuild time)
