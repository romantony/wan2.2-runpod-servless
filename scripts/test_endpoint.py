#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
import time
from typing import Optional, Tuple

import requests


def _b64_to_bytes(data_uri: str) -> bytes:
    if not data_uri:
        raise ValueError("Empty data URI")
    if "," in data_uri:
        data_uri = data_uri.split(",", 1)[1]
    return base64.b64decode(data_uri)


def run_health(base_or_run_url: str, api_key: str) -> dict:
    base_url, run_url, _ = normalize_urls(base_or_run_url)
    payload = {"input": {"health": True}}
    r = requests.post(
        run_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def run_job(
    base_or_run_url: str,
    api_key: str,
    image_url: str,
    prompt: str,
    size: str = "1280*720",
    frame_num: int = 49,
    sample_steps: int = 24,
    sample_solver: str = "unipc",
    cfg_scale: float = 6.0,
    offload_model: bool = True,
    t5_cpu: bool = True,
) -> str:
    base_url, run_url, _ = normalize_urls(base_or_run_url)
    payload = {
        "input": {
            "action": "request",
            "return_video": True,
            "inputs": {
                "reference_image_url": image_url,
                "prompt": prompt,
                "size": size,
                "num_frames": frame_num,
                "sample_solver": sample_solver,
                "sample_steps": sample_steps,
                "cfg_scale": cfg_scale,
                "offload_model": offload_model,
                "t5_cpu": t5_cpu,
            },
        }
    }
    r = requests.post(
        run_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    job_id = data.get("id") or data.get("jobId")
    if not job_id:
        raise RuntimeError(f"Unexpected run response: {data}")
    return job_id


def poll_status(base_or_run_url: str, api_key: str, job_id: str, interval_s: float = 5.0) -> dict:
    base_url, _, status_base = normalize_urls(base_or_run_url)
    last_status = None
    while True:
        # Prefer GET; fall back to POST if necessary
        try:
            r = requests.get(
                f"{status_base}/{job_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=60,
            )
            if r.status_code == 405:
                raise requests.HTTPError("Method Not Allowed", response=r)
        except requests.HTTPError:
            r = requests.post(
                f"{status_base}/{job_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=60,
            )
        r.raise_for_status()
        s = r.json()
        status = s.get("status") or s.get("state")
        if status and status != last_status:
            print(f"Status: {status}")
            last_status = status
        if status in ("COMPLETED", "FAILED", "CANCELED", "CANCELLED", "ERROR"):
            return s
        time.sleep(interval_s)


def extract_and_save_output(status_payload: dict, out_dir: str = "outputs") -> Optional[str]:
    os.makedirs(out_dir, exist_ok=True)
    output = status_payload.get("output") or {}
    # Our handler returns base64 under output.result.data
    b64 = None
    result = output.get("result") or {}
    if isinstance(result, dict):
        b64 = result.get("data")
    if not b64 and isinstance(output, dict):
        # Edge case: some wrappers might place data at top level
        b64 = output.get("data")

    if b64:
        job_id = status_payload.get("id", "job")
        out_path = os.path.join(out_dir, f"{job_id}.mp4")
        with open(out_path, "wb") as f:
            f.write(_b64_to_bytes(b64))
        return out_path

    # Fallback: look for a path in outputs list
    try:
        st = output.get("status") or {}
        outputs = st.get("outputs") or []
        if outputs:
            return outputs[0]
    except Exception:
        pass
    return None


def normalize_urls(api_url_or_base: str) -> Tuple[str, str, str]:
    """Return (base_url, run_url, status_base).

    Accepts either:
    - base URL: https://api.runpod.ai/v2/<endpointId>
    - run URL:  https://api.runpod.ai/v2/<endpointId>/run
    """
    url = (api_url_or_base or "").rstrip("/")
    if url.endswith("/run"):
        base = url[:-4]
        run = url
    else:
        base = url
        run = f"{base}/run"
    status_base = f"{base}/status"
    return base, run, status_base


def main():
    DEFAULT_ENDPOINT_ID = "c5tcnbrax0chts"
    DEFAULT_API_BASE = f"https://api.runpod.ai/v2/{DEFAULT_ENDPOINT_ID}"
    p = argparse.ArgumentParser(description="Test RunPod Serverless WAN 2.2 endpoint and save MP4.")
    p.add_argument(
        "--api-url",
        default=os.getenv("RUNPOD_API_URL", DEFAULT_API_BASE),
        help=(
            "Full API base or run URL. Examples: \n"
            "  https://api.runpod.ai/v2/<endpointId> \n"
            "  https://api.runpod.ai/v2/<endpointId>/run"
        ),
    )
    p.add_argument(
        "--endpoint-id",
        default=os.getenv("RUNPOD_ENDPOINT_ID", DEFAULT_ENDPOINT_ID),
        help=(
            "Endpoint ID (used if --api-url not provided). Defaults to env RUNPOD_ENDPOINT_ID or the built-in."
        ),
    )
    p.add_argument("--api-key", default=os.getenv("RUNPOD_API_KEY"), help="RunPod API key (Bearer)")
    p.add_argument("--image-url", default="https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=1024")
    p.add_argument("--prompt", default="A cinematic slow pan, dreamy lighting")
    p.add_argument("--size", default="1280*720")
    p.add_argument("--frames", type=int, default=49)
    p.add_argument("--steps", type=int, default=24)
    p.add_argument("--solver", default="unipc", choices=["unipc", "dpm++"])
    p.add_argument("--cfg", type=float, default=6.0)
    p.add_argument("--offload", action="store_true", help="Set --offload_model true")
    p.add_argument("--no-offload", dest="offload", action="store_false")
    p.set_defaults(offload=True)
    p.add_argument("--t5-cpu", action="store_true")
    p.add_argument("--t5-gpu", dest="t5_cpu", action="store_false")
    p.set_defaults(t5_cpu=True)
    p.add_argument("--health-only", action="store_true", help="Run only a health check and exit")
    p.add_argument("--skip-health", action="store_true", help="Skip health check and run generation directly")
    p.add_argument("--ignore-health-fail", action="store_true", help="Proceed to generation even if health fails")
    args = p.parse_args()

    # Prefer explicit API URL; otherwise build from endpoint-id
    api_url = (args.api_url or "").strip()
    if not api_url:
        api_url = f"https://api.runpod.ai/v2/{args.endpoint_id}"

    if not api_url or not args.api_key:
        print("ERROR: Provide --api-url/--endpoint-id and --api-key or set RUNPOD_API_URL/RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY.", file=sys.stderr)
        sys.exit(2)

    # Health-first flow (default): run health, then generation unless --health-only or --skip-health specified
    if not args.skip_health:
        try:
            data = run_health(api_url, args.api_key)
            print("Health:")
            print(json.dumps(data, indent=2))
            ok = bool(data.get("output", {}).get("ok")) or bool(data.get("ok"))
            if args.health_only:
                sys.exit(0)
            if not ok and not args.ignore_health_fail:
                print("Health check failed (ok=false). Use --ignore-health-fail to proceed anyway.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            if args.health_only:
                raise
            if not args.ignore_health_fail:
                print(f"Health check error: {e}", file=sys.stderr)
                sys.exit(1)

    job_id = run_job(
        base_or_run_url=api_url,
        api_key=args.api_key,
        image_url=args.image_url,
        prompt=args.prompt,
        size=args.size,
        frame_num=args.frames,
        sample_steps=args.steps,
        sample_solver=args.solver,
        cfg_scale=args.cfg,
        offload_model=args.offload,
        t5_cpu=args.t5_cpu,
    )
    print(f"Submitted job: {job_id}")
    status = poll_status(api_url, args.api_key, job_id)
    print("Final status:")
    print(json.dumps(status, indent=2))
    out = extract_and_save_output(status)
    if out:
        print(f"Saved video to: {out}")
    else:
        print("No video found in response.")


if __name__ == "__main__":
    main()
