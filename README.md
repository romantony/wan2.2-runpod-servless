# Wan2.2 I2V-A14B — RunPod Serverless (Models pre-loaded)

This variant **uses your pre-downloaded models** at **/workspace/models** (or set `WAN_CKPT_DIR`). No HF download at startup.

## Build & Deploy
```bash
docker build -t <YOUR_REGISTRY>/wan22-runpod-serverless:latest .
docker push <YOUR_REGISTRY>/wan22-runpod-serverless:latest
```
Create a RunPod Serverless template using the image. Set env:
- `WAN_CKPT_DIR`: `/workspace/models` (default)
- `RUNPOD_MAX_CONCURRENCY`: `1`

**Mount your RunPod permanent storage** to `/workspace/models` so weights survive cold starts.

## GPU/CUDA Compatibility
- Base image: CUDA 12.4.1 + cuDNN (Ubuntu 22.04)
- PyTorch stack: 2.5.1 cu124 (torch 2.5.1, torchvision 0.20.1, torchaudio 2.5.1)
- Target GPUs: RTX 5090 (default in runpod.yaml), RTX 4090, A100.
- If you see device/driver mismatches, ensure the host drivers support CUDA 12.4 or upgrade host drivers accordingly.

## API
### Request
```json
{
  "action": "request",
  "params": {
    "reference_image_url": "https://.../img.png",
    "prompt": "cinematic winter summit, steady pan, subtle parallax",
    "size": "1280*720",
    "seed": 42,
    "offload_model": true,
    "t5_cpu": true
  },
  "return_video": true
}
```

### Status
```json
{ "action": "status", "request_id": "UUID", "return_video": true }
```

Outputs save to `/workspace/outputs/<request_id>.mp4` (and can be returned as base64 when `return_video=true`).

## Parameters
These inputs are forwarded to Wan2.2’s `generate.py` (aligned to the upstream CLI). Defaults shown are from the wrapper or upstream where noted; ranges are recommended, not strict.

- reference_image_url | reference_image_base64 | reference_image_path
  - Required. Source image for i2v. One of URL, base64, or absolute path.
- size
  - Default (upstream): `1280*720` (`WIDTH*HEIGHT`).
  - Use one of WAN’s supported sizes; recommend `1024*576`–`1920*1080` based on VRAM.
- prompt
  - Default (upstream): `None` (falls back to an internal example if omitted).
- seed (alias for `base_seed`)
  - Default (upstream): `-1` → random.
  - Integer; set for reproducibility.
- frame_num (alias: `num_frames`)
  - Default (upstream): task default.
  - Must satisfy `4n+1` (e.g., 33, 49, 81). Higher → longer video and more VRAM/time.
- sample_solver
  - Default (upstream): `unipc`. Choices: `unipc`, `dpm++`.
- sample_steps
  - Default (upstream): task default.
  - Recommend ~20–36 depending on quality/runtime tradeoff.
- sample_guide_scale (aliases: `cfg_scale`, `guidance_scale`)
  - Default (upstream): task default.
  - Recommend 3.0–9.0. Higher → stronger prompt adherence.
- sample_shift
  - Default (upstream): task default.
  - Recommend 0.0–1.0 (scheduler-specific effect).
- offload_model
  - Default (upstream): auto → `True` on single-GPU. Wrapper default: `true`.
  - Offloads parts of the model to CPU to reduce VRAM.
- t5_cpu
  - Default (upstream): `false`. Wrapper default: `true` (reduce VRAM).
- convert_model_dtype
  - Default (upstream): `false`. Wrapper default: `true`.
- t5_fsdp | dit_fsdp | ulysses_size
  - Advanced distributed/parallelism options. Keep defaults in serverless.
- use_prompt_extend | prompt_extend_method | prompt_extend_model | prompt_extend_target_lang
  - Enable and configure WAN’s prompt extension (advanced).
- save_file
  - The wrapper sets this automatically to `/workspace/outputs/<request_id>.mp4`.
- extra_args
  - Advanced passthrough to the WAN CLI; accepts string or array. Limited to 50 tokens.
- return_video (top-level)
  - Default: `true`. If true, response includes base64 MP4; otherwise returns the saved path only.

Notes
- Only supported flags are forwarded. See `src/handler.py` for aliased mappings.
- If `WAN_CKPT_DIR` (`/workspace/models` by default) is missing but `/runpod-volume` exists, the handler falls back to `/runpod-volume`.
