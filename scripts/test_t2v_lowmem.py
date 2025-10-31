#!/usr/bin/env python3
"""
Test script for WAN 2.2 T2V with memory-optimized settings
Designed for 24-32GB GPUs with 14B parameter models
"""
import argparse
import json
import time
import requests
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Test WAN T2V with low memory settings')
    parser.add_argument('--api-url', required=True, help='RunPod API endpoint URL')
    parser.add_argument('--api-key', required=True, help='RunPod API key')
    parser.add_argument('--prompt', required=True, help='Text prompt for video generation')
    parser.add_argument('--size', default='480*832', help='Video size (default: 480*832 for low VRAM)')
    parser.add_argument('--frames', type=int, default=17, help='Number of frames (default: 17)')
    parser.add_argument('--steps', type=int, default=20, help='Sampling steps (default: 20)')
    parser.add_argument('--cfg', type=float, default=6.0, help='CFG scale (default: 6.0)')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--output', default='output_t2v_lowmem.mp4', help='Output filename')
    
    args = parser.parse_args()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {args.api_key}"
    }
    
    params = {
        "task": "t2v-A14B",
        "prompt": args.prompt,
        "size": args.size,
        "frame_num": args.frames,
        "sample_steps": args.steps,
        "sample_guide_scale": args.cfg,
        "offload_model": True,
        "convert_model_dtype": True,
        "t5_cpu": True,
    }
    
    if args.seed:
        params["seed"] = args.seed
    
    payload = {"input": {"params": params}}
    
    print(f"Submitting T2V job (LOW MEMORY MODE)")
    print(f"  Prompt: {args.prompt}")
    print(f"  Size: {args.size}, Frames: {args.frames}, Steps: {args.steps}, CFG: {args.cfg}")
    
    # Submit job
    response = requests.post(args.api_url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    job_id = result.get('id')
    print(f"Submitted job: {job_id}")
    
    # Poll for completion
    status_url = args.api_url.replace('/run', '') + f"/status/{job_id}"
    
    while True:
        response = requests.get(status_url, headers=headers)
        response.raise_for_status()
        status_data = response.json()
        
        status = status_data.get('status', 'UNKNOWN')
        print(f"Status: {status}")
        
        if status == 'COMPLETED':
            print("\nFinal status:")
            print(json.dumps(status_data, indent=2))
            
            # Check for video output
            output_data = status_data.get('output', {})
            if isinstance(output_data, dict):
                video_b64 = output_data.get('video_base64')
                if video_b64:
                    import base64
                    video_data = base64.b64decode(video_b64)
                    with open(args.output, 'wb') as f:
                        f.write(video_data)
                    print(f"\n✅ Video saved to: {args.output}")
                    return
            
            print("\n⚠️ No video found in response.")
            return
            
        elif status in ['FAILED', 'CANCELLED']:
            print("\n❌ Job failed or was cancelled")
            print(json.dumps(status_data, indent=2))
            return
        
        time.sleep(5)

if __name__ == '__main__':
    main()
