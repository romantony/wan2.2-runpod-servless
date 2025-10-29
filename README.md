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
