#!/usr/bin/env python3
"""
Test script for WAN 2.2 T2V with ULTRA-LOW memory settings
Absolute minimum settings for 14B model on 34GB VRAM
"""
import argparse
import json
import time
import requests
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Test WAN T2V with ultra-low memory settings')
    parser.add_argument('--api-url', required=True, help='RunPod API endpoint URL')
    parser.add_argument('--api-key', required=True, help='RunPod API key')
    parser.add_argument('--prompt', required=True, help='Text prompt for video generation')
    parser.add_argument('--size', default='320*576', help='Video size (default: 320*576 - ULTRA LOW)')
    parser.add_argument('--frames', type=int, default=9, help='Number of frames (default: 9)')
    parser.add_argument('--steps', type=int, default=15, help='Sampling steps (default: 15)')
    parser.add_argument('--cfg', type=float, default=5.0, help='CFG scale (default: 5.0)')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--output', default='output_t2v_ultralowmem.mp4', help='Output filename')
    
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
        "cpu_offload_modules": ["vae", "text_encoder"],  # Extra aggressive offloading
    }
    
    if args.seed:
        params["seed"] = args.seed
    
    payload = {"input": {"params": params}}
    
    print(f"Submitting T2V job (ULTRA-LOW MEMORY MODE)")
    print(f"  Prompt: {args.prompt}")
    print(f"  Size: {args.size}, Frames: {args.frames}, Steps: {args.steps}, CFG: {args.cfg}")
    print(f"  ⚠️  WARNING: These are MINIMAL settings to test if model works at all")
    
    # Submit job
    response = requests.post(args.api_url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    
    job_id = result.get('id')
    print(f"Submitted job: {job_id}")
    
    # Poll for completion
    status_url = f"{args.api_url.rstrip('/run')}/status/{job_id}"
    while True:
        time.sleep(5)
        status_response = requests.get(status_url, headers=headers)
        status_response.raise_for_status()
        status_data = status_response.json()
        
        current_status = status_data.get('status')
        print(f"Status: {current_status}")
        
        if current_status in ['COMPLETED', 'FAILED']:
            print(f"\nFinal status:")
            print(json.dumps(status_data, indent=2))
            
            # Try to extract and save video
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
            
            print(f"\n⚠️ No video found in response.")
            break

if __name__ == '__main__':
    main()
