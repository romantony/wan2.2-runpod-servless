# Infrastructure Comparison: ComfyUI vs WAN 2.2 on RunPod

## Overview
Both deployments run on the same GPU hardware but use different optimization strategies.

---

## Hardware Specifications

| Component | ComfyUI Setup | WAN 2.2 Setup | Notes |
|-----------|---------------|---------------|-------|
| **GPU** | NVIDIA GeForce RTX 5090 | **NVIDIA RTX 5090 Pro** | ⚠️ Different SKU |
| **VRAM** | 32,120 MB (32.1 GB) | 31,370 MB (31.37 GB) | Similar, slight variance |
| **System RAM** | 967,512 MB (~968 GB) | 117,000 MB (~117 GB) | ⚠️ **ComfyUI has 8x more RAM!** |
| **CUDA Version** | 12.8.1 | 12.8.0 | Nearly identical |
| **PyTorch** | 2.8.0+cu128 | 2.8.0+cu128 | ✅ Same |

> **Note**: RTX 5090 Pro is a professional/workstation GPU with potentially different memory bandwidth, ECC support, and driver optimizations compared to consumer GeForce RTX 5090.

---

## Docker Images

### ComfyUI
```
registry.runpod.net/wlsdml1114-generate-video-main-dockerfile:a4899524e
```
- Base: NVIDIA CUDA container (NGC Deep Learning Container)
- Full CUDA development environment
- Pre-installed: xformers 0.0.32.post2

### WAN 2.2
```
nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04
```
- Base: Official NVIDIA CUDA image
- Requires manual dependency installation
- Flash-attn compilation from source

---

## Memory & Attention Optimizations

### ComfyUI Advantages:
1. **Sage Attention** - More memory-efficient than flash-attention
2. **xformers 0.0.32.post2** - Pre-compiled and optimized
3. **VRAM Mode**: `NORMAL_VRAM` (not low VRAM mode)
4. **Memory Allocator**: `cudaMallocAsync` - Optimized CUDA memory management
5. **Massive RAM**: 968GB allows aggressive model offloading

### WAN 2.2 Current State:
1. **Flash-attn fallback** - Using PyTorch's `scaled_dot_product_attention`
2. **Limited RAM**: 117GB (still good, but 8x less)
3. **Manual offloading**: `offload_model=True`, `t5_cpu=True`, `convert_model_dtype=True`
4. **OOM Issues**: 14B models struggle even at minimal settings

---

## Startup & Performance

### ComfyUI:
- **Cold Start**: ~15 seconds (ComfyUI ready at 11:59:38)
- **Custom Nodes**: Loaded in ~1 second
- **Model Loading**: Fast with pre-compiled dependencies
- **Handler**: Requires specific workflow structure

### WAN 2.2:
- **Cold Start**: ~10-20 minutes (Docker rebuild + model loading)
- **Model Loading**: First-time load is slow (14B models)
- **Handler**: Simple params structure (`task`, `prompt`, `size`, etc.)
- **Current Issues**: Matrix shape mismatches, OOM errors

---

## Key Differences to Learn From

### 1. RAM Allocation
```
ComfyUI: 968GB RAM → Can offload almost everything to RAM
WAN 2.2: 117GB RAM → More constrained, needs efficient VRAM usage
```

**Action**: Consider upgrading WAN 2.2 RunPod instance to match ComfyUI's RAM

### 2. Attention Mechanism
```
ComfyUI: Sage Attention (optimized for memory)
WAN 2.2: Flash-attn → PyTorch fallback (less efficient)
```

**Action**: Investigate sage attention or upgrade xformers

### 3. VRAM Management
```
ComfyUI: cudaMallocAsync (async allocation)
WAN 2.2: Default PyTorch allocator
```

**Action**: Consider setting `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`

### 4. Pre-compiled Dependencies
```
ComfyUI: Everything pre-built in Docker image
WAN 2.2: Compiles flash-attn on every build (slow)
```

**Action**: Pre-build dependencies in base Docker image

---

## Recommendations for WAN 2.2

### Immediate (Can do now):
1. ✅ **Test minimal settings** with new patch (480*832, 9 frames)
2. Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` in Dockerfile
3. Add xformers explicitly to requirements.txt
4. Consider using 5B models instead of 14B for better memory fit

### Short-term (Next iteration):
1. **Match RAM allocation** to ComfyUI (968GB instance)
2. **Pre-compile flash-attn** in Docker image (not during startup)
3. **Add model caching** to avoid reloading
4. **Test with xformers** instead of flash-attn fallback

### Long-term (Optimization):
1. Investigate **sage attention** for ComfyUI
2. Implement **model quantization** (8-bit, 4-bit)
3. Add **gradient checkpointing** for training/fine-tuning
4. Consider **tensor parallelism** if multi-GPU becomes available

---

## Cost Comparison

Based on hardware specs, the ComfyUI instance likely costs more due to:
- 8x more RAM (968GB vs 117GB)
- Potentially different pricing tier

**Question to investigate**: What's the cost per hour for each instance?

---

## Testing Strategy

### Phase 1: Verify Current Build ✅
```bash
python scripts/test_t2v_lowmem.py \
  --api-url https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  --api-key YOUR_RUNPOD_API_KEY \
  --prompt "A cat playing piano" \
  --size "480*832" --frames 9 --steps 15
```

### Phase 2: If OOM persists
- Upgrade to 968GB RAM instance (match ComfyUI)
- Use 5B models instead of 14B
- Add xformers optimization

### Phase 3: Optimize
- Pre-build Docker image with all dependencies
- Implement model caching
- Test with larger settings

---

## Conclusion

The main bottleneck for WAN 2.2 is likely **RAM availability**. ComfyUI's 968GB RAM allows aggressive offloading, keeping VRAM free for active computation. WAN 2.2's 117GB RAM is good but may not be enough for 14B models with video generation.

**Next Step**: Test current build, then consider RAM upgrade if OOM continues.
