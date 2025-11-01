# Storage Migration Guide

## Moving from `/workspace/runpod-slim/ComfyUI/models/` to `/workspace/models/`

### Why Migrate?

The recommended approach is to store models at `/workspace/models/` (separate from ComfyUI) instead of `/workspace/runpod-slim/ComfyUI/models/` (inside ComfyUI installation).

**Benefits:**
- ✅ Clean separation of data and application
- ✅ Easy ComfyUI upgrades without touching models
- ✅ Portable across different ComfyUI versions
- ✅ Standard RunPod practice
- ✅ Simpler path management

---

## Migration Steps

### Option 1: Move Files (Recommended for Production)

**On your storage system or inside a container with both paths mounted:**

```bash
# Create new structure
mkdir -p /workspace/models

# Move model directories
mv /workspace/runpod-slim/ComfyUI/models/* /workspace/models/

# Verify
ls -lh /workspace/models/
# Should show: diffusion_models/, vae/, loras/, etc.

# Check sizes match
du -sh /workspace/models/
# Should be ~51GB
```

---

### Option 2: Copy Files (Safe, but uses 2× storage temporarily)

```bash
# Create new structure
mkdir -p /workspace/models

# Copy model directories (preserves originals)
cp -r /workspace/runpod-slim/ComfyUI/models/* /workspace/models/

# Verify copy succeeded
ls -lh /workspace/models/

# Test with new location before deleting old
# ... (run ComfyUI, test workflows) ...

# Once confirmed working, remove old location
rm -rf /workspace/runpod-slim/ComfyUI/models/*
```

---

### Option 3: Symbolic Link (Quick Fix, Not Recommended Long-term)

```bash
# Backup old location
mv /workspace/runpod-slim/ComfyUI/models /workspace/runpod-slim/ComfyUI/models.bak

# Create symlink
ln -s /workspace/models /workspace/runpod-slim/ComfyUI/models

# Models now accessible from both paths
ls -lh /workspace/runpod-slim/ComfyUI/models/
# Shows contents of /workspace/models/
```

**Note:** This works but defeats the purpose of separation. Use only as a temporary solution.

---

### Option 4: Use extra_model_paths.yaml (No File Movement)

If you want to keep models where they are but still use the recommended pattern:

```yaml
# extra_model_paths.yaml
wan2_storage:
  base_path: /workspace/runpod-slim/ComfyUI
  
  diffusion_models: models/diffusion_models/
  vae: models/vae/
  # ... etc
```

This allows ComfyUI to find models without moving them, but you lose the benefits of separation.

---

## Configuration Changes

### 1. Update extra_model_paths.yaml

Change from:
```yaml
# OLD - models inside ComfyUI
wan2_storage:
  base_path: /workspace/runpod-slim/ComfyUI
  diffusion_models: models/diffusion_models/
```

To:
```yaml
# NEW - models separate from ComfyUI
wan2_permanent_storage:
  base_path: /workspace/models
  diffusion_models: diffusion_models/
```

### 2. Update Dockerfile

```dockerfile
# Copy configuration file
COPY extra_model_paths.yaml /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml

# Create mount point for separate model storage
RUN mkdir -p /workspace/models
```

### 3. Update Volume Mounts

**Docker Compose - Before:**
```yaml
volumes:
  - ./models:/workspace/runpod-slim/ComfyUI/models
```

**Docker Compose - After:**
```yaml
volumes:
  - ./models:/workspace/models
```

**RunPod Dashboard - Before:**
- Mount path: `/workspace/runpod-slim/ComfyUI/models`

**RunPod Dashboard - After:**
- Mount path: `/workspace/models`

---

## Verification After Migration

### 1. Check Files Are in New Location
```bash
ls -lh /workspace/models/diffusion_models/
# Should show 4 WAN models

du -sh /workspace/models/
# Should show ~51GB
```

### 2. Verify ComfyUI Config
```bash
cat /workspace/runpod-slim/ComfyUI/extra_model_paths.yaml
# Should show base_path: /workspace/models
```

### 3. Start ComfyUI and Test Model Detection
```bash
# Start ComfyUI
python /workspace/runpod-slim/ComfyUI/main.py --listen 0.0.0.0 --port 8188

# In another terminal, check models are detected
curl -s http://127.0.0.1:8188/object_info | jq '.UNETLoader.input.required.unet_name[0]'

# Expected output:
# [
#   "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors",
#   "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
#   "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
#   "wan2.2_s2v_14B_fp8_scaled.safetensors"
# ]
```

### 4. Test a Workflow
```bash
# Queue a test I2V workflow
curl -X POST http://127.0.0.1:8188/prompt \
  -H "Content-Type: application/json" \
  -d @test_i2v_request.json

# If successful, migration is complete!
```

---

## Rollback Plan

If something goes wrong:

### If You Used Option 1 (Move):
```bash
# Move back
mv /workspace/models/* /workspace/runpod-slim/ComfyUI/models/
```

### If You Used Option 2 (Copy):
```bash
# Old files still exist, just revert config
# Remove new location
rm -rf /workspace/models/*
# Models still work from old location
```

### If You Used Option 3 (Symlink):
```bash
# Remove symlink
rm /workspace/runpod-slim/ComfyUI/models
# Restore backup
mv /workspace/runpod-slim/ComfyUI/models.bak /workspace/runpod-slim/ComfyUI/models
```

---

## Timeline Recommendation

1. **Today:** Create `/workspace/models/` structure, copy `extra_model_paths.yaml`
2. **Testing:** Copy models to new location, test with new config
3. **Validation:** Run all workflows (I2V, S2V, Animation) to verify
4. **Cleanup:** Once confirmed working for 24-48 hours, remove old location
5. **Update Docs:** Update any internal documentation with new paths

---

## Checklist

- [ ] Created `/workspace/models/` directory structure
- [ ] Moved/copied model files to new location
- [ ] Updated `extra_model_paths.yaml` with new base_path
- [ ] Copied config to ComfyUI directory
- [ ] Updated Dockerfile to mount `/workspace/models/`
- [ ] Updated volume mount configurations
- [ ] Tested ComfyUI model detection
- [ ] Ran test workflow successfully
- [ ] Verified all 4 diffusion models load
- [ ] Verified all 5 LoRAs load
- [ ] Tested I2V workflow
- [ ] Tested S2V workflow
- [ ] Tested Animation workflow
- [ ] Removed old model location (after confirmation)
- [ ] Updated deployment documentation

---

**Migration Complete!** 🎉

Your models are now properly organized in permanent storage at `/workspace/models/`, separate from your ComfyUI installation.
