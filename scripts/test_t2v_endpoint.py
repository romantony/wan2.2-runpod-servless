#!/usr/bin/env python3
"""
Test script for WAN 2.2 Text-to-Video (T2V) endpoint on RunPod Serverless
"""
import argparse
import json
import time
import base64
import requests
from pathlib import Path

def submit_job(api_url, api_key, params):
    """Submit a T2V job to RunPod"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "input": {
            "task": params["task"],
            "prompt": params["prompt"],
            "size": params.get("size", "1280*720"),
            "sample_steps": params.get("steps", 24),
            "sample_guide_scale": params.get("cfg", 6.0),
            "frame_num": params.get("frames", 49),
            "offload_model": True,
            "convert_model_dtype": True,
            "t5_cpu": True,
        }
    }
    
    if params.get("seed"):
        payload["input"]["seed"] = params["seed"]
    
    response = requests.post(f"{api_url}", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def check_status(api_url, api_key, job_id):
    """Check job status"""
    headers = {"Authorization": f"Bearer {api_key}"}
    status_url = f"{api_url.replace('/run', '')}/status/{job_id}"
    response = requests.get(status_url, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Test WAN 2.2 T2V endpoint")
    parser.add_argument("--api-url", required=True, help="RunPod API URL")
    parser.add_argument("--api-key", required=True, help="RunPod API key")
    parser.add_argument("--task", default="t2v-A14B", help="Task name (default: t2v-A14B)")
    parser.add_argument("--prompt", required=True, help="Text prompt for video generation")
    parser.add_argument("--size", default="1280*720", help="Video size (default: 1280*720)")
    parser.add_argument("--frames", type=int, default=49, help="Number of frames (4n+1, default: 49)")
    parser.add_argument("--steps", type=int, default=24, help="Sampling steps (default: 24)")
    parser.add_argument("--cfg", type=float, default=6.0, help="CFG scale (default: 6.0)")
    parser.add_argument("--seed", type=int, help="Random seed (optional)")
    parser.add_argument("--output", default="output_t2v.mp4", help="Output video filename")
    
    args = parser.parse_args()
    
    params = {
        "task": args.task,
        "prompt": args.prompt,
        "size": args.size,
        "frames": args.frames,
        "steps": args.steps,
        "cfg": args.cfg,
    }
    
    if args.seed:
        params["seed"] = args.seed
    
    print(f"Submitting T2V job with prompt: {args.prompt}")
    print(f"Parameters: task={args.task}, size={args.size}, frames={args.frames}, steps={args.steps}, cfg={args.cfg}")
    
    # Submit job
    result = submit_job(args.api_url, args.api_key, params)
    job_id = result.get("id")
    print(f"Submitted job: {job_id}")
    
    # Poll for completion
    while True:
        status_result = check_status(args.api_url, args.api_key, job_id)
        status = status_result.get("status")
        print(f"Status: {status}")
        
        if status == "COMPLETED":
            print("\nFinal status:")
            print(json.dumps(status_result, indent=2))
            
            # Save video if present
            output = status_result.get("output", {})
            video_b64 = output.get("video_base64")
            
            if video_b64:
                video_data = base64.b64decode(video_b64)
                with open(args.output, "wb") as f:
                    f.write(video_data)
                print(f"\n✅ Video saved to: {args.output}")
            else:
                print("\nNo video found in response.")
            break
            
        elif status in ("FAILED", "CANCELLED"):
            print("\n❌ Job failed or cancelled:")
            print(json.dumps(status_result, indent=2))
            break
            
        time.sleep(5)

if __name__ == "__main__":
    main()
