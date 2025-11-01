#!/usr/bin/env python3
"""
Test script for ComfyUI RunPod endpoint
Endpoint: https://api.runpod.ai/v2/h0wircb2dlbeax/run
"""
import argparse
import json
import time
import requests
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Test ComfyUI RunPod endpoint')
    parser.add_argument('--api-url', default='https://api.runpod.ai/v2/h0wircb2dlbeax/run', 
                       help='RunPod API endpoint URL')
    parser.add_argument('--api-key', required=True, help='RunPod API key')
    parser.add_argument('--prompt', required=True, help='Prompt for generation')
    parser.add_argument('--output', default='output_comfyui.png', help='Output filename')
    parser.add_argument('--workflow', help='Optional: JSON workflow file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed (default: 42)')
    parser.add_argument('--steps', type=int, default=20, help='Sampling steps (default: 20)')
    parser.add_argument('--cfg', type=float, default=7.0, help='CFG scale (default: 7.0)')
    parser.add_argument('--width', type=int, default=512, help='Width (default: 512)')
    parser.add_argument('--height', type=int, default=512, help='Height (default: 512)')
    
    args = parser.parse_args()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {args.api_key}"
    }
    
    # Build payload
    if args.workflow:
        # Load workflow from file
        with open(args.workflow, 'r') as f:
            workflow = json.load(f)
        payload = {"input": workflow}
    else:
        # Simple prompt-based payload
        payload = {
            "input": {
                "prompt": args.prompt,
                "seed": args.seed,
                "steps": args.steps,
                "cfg_scale": args.cfg,
                "width": args.width,
                "height": args.height
            }
        }
    
    print(f"Testing ComfyUI endpoint")
    print(f"  Prompt: {args.prompt}")
    print(f"  Seed: {args.seed}")
    print(f"  Steps: {args.steps}, CFG: {args.cfg}")
    print(f"  Size: {args.width}x{args.height}")
    if args.workflow:
        print(f"  Workflow: {args.workflow}")
    print()
    
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
            
            # Try to extract and save output
            output_data = status_data.get('output', {})
            
            # Check for various output formats
            if isinstance(output_data, dict):
                # Look for image data
                if 'image' in output_data:
                    save_output(output_data['image'], args.output, 'image')
                elif 'images' in output_data and isinstance(output_data['images'], list):
                    for i, img in enumerate(output_data['images']):
                        output_file = f"{Path(args.output).stem}_{i}{Path(args.output).suffix}"
                        save_output(img, output_file, 'image')
                elif 'result' in output_data:
                    save_output(output_data['result'], args.output, 'generic')
                else:
                    print(f"\n⚠️ Output structure not recognized. Full output:")
                    print(json.dumps(output_data, indent=2))
            elif isinstance(output_data, str):
                # Direct string output (might be base64 or URL)
                save_output(output_data, args.output, 'generic')
            else:
                print(f"\n⚠️ No output data found in response.")
            
            break

def save_output(data, filename, data_type):
    """Save output data to file"""
    try:
        if isinstance(data, str):
            # Check if it's base64
            if data.startswith('data:image'):
                # Data URI format
                import base64
                header, encoded = data.split(',', 1)
                decoded = base64.b64decode(encoded)
                with open(filename, 'wb') as f:
                    f.write(decoded)
                print(f"\n✅ Image saved to: {filename}")
            elif data.startswith('http'):
                # URL - download it
                import requests
                response = requests.get(data)
                response.raise_for_status()
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"\n✅ Downloaded and saved to: {filename}")
            else:
                # Try as base64
                try:
                    import base64
                    decoded = base64.b64decode(data)
                    with open(filename, 'wb') as f:
                        f.write(decoded)
                    print(f"\n✅ Image saved to: {filename}")
                except:
                    # Save as text
                    with open(filename, 'w') as f:
                        f.write(data)
                    print(f"\n✅ Output saved to: {filename}")
        else:
            # Save as JSON
            with open(f"{Path(filename).stem}.json", 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✅ Output saved to: {Path(filename).stem}.json")
    except Exception as e:
        print(f"\n❌ Failed to save output: {e}")

if __name__ == '__main__':
    main()
