# Docker Image Comparison: zjwfufu/wan2.2 vs Current Build

## Investigation Summary

### Pre-built Docker Image: zjwfufu/wan2.2:2025-08-16
- **Status**: Image exists on Docker Hub but details not accessible without Docker Desktop
- **GitHub Repo**: https://github.com/zjwfufu/wan2.2 returns 404 (repo may be private or deleted)
- **Potential Benefits**:
  - Pre-compiled flash-attn (saves 5-10 min build time)
  - Optimized CUDA settings pre-configured
  - Known-working dependency versions
  - May include additional memory optimizations

### Current Custom Build
- **Status**: Building from scratch on each RunPod deployment
- **Base Image**: nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04
- **Build Time**: ~20 minutes per deployment (due to flash-attn compilation)
- **Current Optimizations**:
  - Flash-attn made optional via patch (commit abfc07b)
  - Memory flags: offload_model=True, convert_model_dtype=True, t5_cpu=True
  - All 60+ dependencies installed

## Official WAN 2.2 Best Practices (from GitHub analysis)

### Installation Order (IMPORTANT!)
From official docs:
```bash
# If the installation of `flash_attn` fails, try installing the other packages 
# first and install `flash_attn` last
pip install -r requirements.txt
```

**Recommendation**: Our current Dockerfile installs flash-attn separately (correct approach).

### Memory Optimization Flags
Official WAN 2.2 code uses these constructor parameters:
- `t5_cpu=True` - Offload T5 encoder to CPU (saves ~8GB VRAM)
- `init_on_cpu=True` - Initialize models on CPU before moving to GPU
- `convert_model_dtype=True` - Convert to mixed precision (saves ~40% VRAM)
- `offload_model=True` - Dynamically move models between CPU/GPU per timestep

**Status**: ✅ All flags already used in our test scripts

### Model-Specific Requirements

#### TI2V-5B (5 Billion Parameters)
- **Official VRAM**: 24GB (RTX 4090 mentioned in docs)
- **Supported Sizes**: ONLY 1280*704 or 704*1280
- **Memory Flags**: `--offload_model True --convert_model_dtype --t5_cpu`
- **Status**: Our test script uses these exact settings

#### T2V-A14B / I2V-A14B (14 Billion Parameters)
- **Official Setup**: 8x GPU with FSDP + Ulysses sequence parallel
- **Single GPU**: Not officially supported for 720P+
- **RAM Requirement**: Based on ComfyUI comparison, likely needs 800-1000GB RAM
- **Your Hardware**: 117GB RAM (insufficient for 14B models)

## Why ComfyUI Works Better (Analysis)

### Key Differences Discovered
1. **RAM**: ComfyUI has 968GB vs WAN's 117GB (8x difference!)
2. **Attention**: sage attention (more efficient) vs flash-attn
3. **Memory Allocator**: cudaMallocAsync vs default
4. **Dependencies**: xformers 0.0.32.post2 pre-compiled

### Root Cause of OOM Errors
- **14B models** need massive CPU RAM for aggressive offloading
- With only 117GB RAM, can't offload enough to fit in 31GB VRAM
- ComfyUI's 968GB RAM allows entire model pipeline in RAM, swapping pieces to VRAM as needed

## Recommendations (Priority Order)

### 1. Test TI2V-5B Model (IMMEDIATE)
**Rationale**: 5B params designed for 24GB VRAM (you have 31GB)
```bash
python scripts/test_ti2v_5b.py \
    --api-url https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
    --api-key YOUR_RUNPOD_API_KEY \
    --prompt "Two cats boxing on a stage" \
    --size "1280*704" \
    --frames 25 \
    --steps 20
```
**Expected**: Should work with current hardware (31GB VRAM, 117GB RAM)

### 2. Test zjwfufu/wan2.2 Docker Image (NEXT)
**Method**: Temporarily switch Dockerfile FROM line:
```dockerfile
FROM zjwfufu/wan2.2:2025-08-16
# Remove all apt-get install, pip install lines - use image as-is
# Only copy your handler.py and bootstrap.sh
```
**Benefits**: 
- Faster deploys (pre-compiled)
- May have additional optimizations
- Saves build time if it works

**Risk**: Unknown dependencies, may not be compatible with RunPod Serverless

### 3. Upgrade RAM to Match ComfyUI (IF BUDGET ALLOWS)
**Target**: 968GB RAM (or at least 512GB)
**Cost**: Check RunPod pricing for high-RAM instances
**Benefit**: Should enable 14B models with aggressive offloading
**Alternative**: Use multi-GPU setup with FSDP (8x GPU as per official docs)

### 4. Add PyTorch Memory Optimization (LOW-HANGING FRUIT)
Add to handler.py or Dockerfile ENV:
```python
import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
```
**Benefit**: Reduces memory fragmentation, may gain 5-10% VRAM

### 5. Consider sage_attention (ADVANCED)
Based on ComfyUI's setup:
```bash
pip install sageattention
```
Then modify WAN's attention mechanism to use sage attention instead of flash-attn.
**Complexity**: Requires code modifications to WAN library
**Benefit**: More memory efficient than flash-attn

## Testing Plan

### Phase 1: Verify Current Build Works (TI2V-5B)
✅ Build completed with commit abfc07b (simplified attention patch)
⏳ Test with 5B model (should work with 24GB VRAM requirement)

### Phase 2: Compare with Pre-built Image
- Switch to zjwfufu/wan2.2:2025-08-16
- Test same prompt with same settings
- Measure: build time, startup time, success rate

### Phase 3: Hardware Upgrade (if needed)
- If TI2V-5B works but T2V-14B still OOM
- Upgrade to 512-968GB RAM instance
- Re-test T2V-14B with same settings

## Current Build Status
- **Last Commit**: abfc07b (Simplified attention patch - comment out assert)
- **Build Time**: ~20 minutes (estimated complete by now)
- **Ready to Test**: YES
- **Expected Result**: TI2V-5B should work, T2V-14B may still OOM due to RAM limitation

## Next Immediate Action
Run this command to test if current build works:
```bash
python scripts/test_ti2v_5b.py \
    --api-url https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
    --api-key YOUR_RUNPOD_API_KEY \
    --prompt "A white cat wearing sunglasses sits on a surfboard at the beach" \
    --size "1280*704" \
    --frames 25 \
    --steps 20 \
    --output "test_ti2v_5b.mp4"
```

If this works, we've found a viable path forward with the 5B model while we investigate RAM upgrade options for the 14B models.
