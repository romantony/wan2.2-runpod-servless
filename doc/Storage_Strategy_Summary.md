# Model Storage Strategy Summary

## Recommendation: Use `/workspace/models/` ✅

Store all models in **`/workspace/models/`** on permanent storage, separate from ComfyUI installation.

---

## Quick Comparison

| Aspect | `/workspace/models/` ✅ | `/workspace/runpod-slim/ComfyUI/models/` ❌ |
|--------|-------------------------|---------------------------------------------|
| **Separation** | Clean data/app separation | Models mixed with application |
| **Upgrades** | Easy ComfyUI updates | Risk overwriting models |
| **Portability** | Works with any ComfyUI version | Tied to specific path |
| **Standard** | RunPod best practice | Non-standard |
| **Flexibility** | Easy to reconfigure | Locked to structure |
| **Config Required** | Yes (`extra_model_paths.yaml`) | No |
| **Clarity** | Clear purpose | Confusing structure |

---

## File Structure

### Permanent Storage (Network Volume)
```
/workspace/models/                    👈 51GB on network volume
├── diffusion_models/                 (4× 14GB models)
├── loras/                            (5× 100MB LoRAs)
├── vae/                              (160MB)
├── text_encoders/                    (4.5GB)
├── audio_encoders/                   (630MB)
├── clip_vision/                      (3.7GB)
└── configs/
```

### Container (Ephemeral)
```
/workspace/runpod-slim/ComfyUI/      👈 Application code (rebuilt each deploy)
├── main.py
├── nodes/
├── custom_nodes/
└── extra_model_paths.yaml           👈 Config pointing to /workspace/models
```

---

## Setup Steps

### 1. Organize Models on Permanent Storage
```bash
# Your current structure
/workspace/models/
├── diffusion_models/
│   ├── Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors
│   ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
│   ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
│   └── wan2.2_s2v_14B_fp8_scaled.safetensors
├── loras/
│   └── (5 LoRA files)
├── vae/
│   └── wan_2.1_vae.safetensors
├── text_encoders/
│   └── umt5_xxl_fp8_e4m3fn_scaled.safetensors
├── audio_encoders/
│   └── wav2vec2_large_english_fp16.safetensors
└── clip_vision/
    └── clip_vision_h.safetensors
```

### 2. Use Provided Configuration
```bash
# File already created in your repo:
extra_model_paths.yaml
```

### 3. Update Dockerfile
```dockerfile
# Copy configuration
COPY extra_model_paths.yaml /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml

# Create mount point
RUN mkdir -p /workspace/models
```

### 4. Mount Network Volume
```bash
# Docker
docker run -v /path/to/network/storage:/workspace/models your-image

# Docker Compose
volumes:
  - ./models:/workspace/models

# RunPod Dashboard
Mount path: /workspace/models
```

### 5. Verify
```bash
curl http://127.0.0.1:8188/object_info | jq '.UNETLoader.input.required.unet_name[0]'
```

---

## Benefits of This Approach

### 1. **Separation of Concerns**
- **Code**: `/workspace/runpod-slim/ComfyUI/` (ephemeral, rebuilt often)
- **Data**: `/workspace/models/` (persistent, rarely changes)

### 2. **Easy Updates**
```bash
# Update ComfyUI without touching models
cd /workspace/runpod-slim
git pull
# Models at /workspace/models/ are untouched
```

### 3. **Flexibility**
```bash
# Want to test a different ComfyUI fork?
git clone https://github.com/other/ComfyUI /workspace/test-comfyui
cp /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml /workspace/test-comfyui/
# Same models, different code!
```

### 4. **Shared Resources**
```yaml
# Multiple ComfyUI installations can share models
comfyui-stable:
  volumes:
    - network-models:/workspace/models

comfyui-beta:
  volumes:
    - network-models:/workspace/models  # Same models!
```

### 5. **Cost Savings**
- Single copy of 51GB models on network storage
- Multiple workers access same models
- No duplication per container

---

## What You Get

✅ **51GB of production-ready models**
- 4× WAN 2.2 diffusion models (14B each)
- 5× LightX2V LoRA accelerators
- Complete supporting infrastructure

✅ **Clean architecture**
- Models: `/workspace/models/`
- Code: `/workspace/runpod-slim/ComfyUI/`
- Config: `extra_model_paths.yaml`

✅ **Production ready**
- I2V (high noise & low noise)
- S2V (sound-to-video)
- Animation (with lighting control)
- Fast 4-step generation

---

## Files Created in Your Repo

1. **`extra_model_paths.yaml`** - ComfyUI configuration pointing to `/workspace/models/`
2. **`doc/WAN2.2_Implementation.md`** - Complete implementation guide
3. **`doc/Storage_Migration_Guide.md`** - Migration instructions
4. **`doc/Storage_Strategy_Summary.md`** - This file

---

## Next Steps

1. ✅ Use `extra_model_paths.yaml` from repo root
2. ✅ Organize models at `/workspace/models/` on network volume
3. ✅ Update Dockerfile to copy config
4. ✅ Mount network volume to `/workspace/models/`
5. ✅ Test and deploy!

---

## Questions?

**Q: Do I need to move my existing models?**  
A: Yes, if they're currently at `/workspace/runpod-slim/ComfyUI/models/`, move them to `/workspace/models/`. See migration guide.

**Q: Can I keep models in the old location?**  
A: Yes, but not recommended. You lose flexibility and standard practices.

**Q: What if I have multiple ComfyUI installations?**  
A: Perfect! All can share `/workspace/models/` via the same config.

**Q: Will this slow down model loading?**  
A: No. Both paths are on the same filesystem. Performance is identical.

**Q: What about small models or configs?**  
A: Large models (diffusion, encoders) go to `/workspace/models/`. Small files can stay in ComfyUI directory if needed.

---

**Recommendation: Use `/workspace/models/` for production deployments** ✅
