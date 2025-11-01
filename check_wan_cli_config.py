#!/usr/bin/env python3
"""
Test WAN CLI mode and check model directory configuration
"""
import requests
import json
import time
import sys
import os
from pathlib import Path

API_KEY = os.environ.get("RUNPOD_API_KEY", "YOUR_API_KEY_HERE")
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "YOUR_ENDPOINT_ID_HERE")

def check_model_paths():
    """Check what paths the handler sees for models"""
    print("🔍 Checking Model Paths Configuration...")
    print("=" * 70)
    
    # Health check shows current paths
    r = requests.post(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"input": {"health": True}},
        timeout=30
    )
    
    result = r.json()
    if result.get("status") == "COMPLETED":
        output = result.get("output", {})
        print(f"✅ WAN_HOME: {output.get('wan_home')}")
        print(f"✅ WAN_CKPT_DIR: {output.get('ckpt_dir')}")
        print(f"✅ ComfyUI: {output.get('comfyui_url')} ({output.get('comfyui_status')})")
        
        ckpt_dir = output.get('ckpt_dir', '')
        print(f"\n📁 Current Model Directory Structure:")
        print(f"   Path: {ckpt_dir}")
        
        if ckpt_dir == "/runpod-volume/models":
            print(f"   ✅ Flat structure - models directly in /runpod-volume/models/")
            print(f"   📝 This works with ComfyUI but NOT WAN CLI")
            print(f"\n   WAN CLI expects:")
            print(f"      /runpod-volume/models/Wan2.2-I2V-A14B/diffusion_models/...")
            print(f"      /runpod-volume/models/Wan2.2-I2V-A14B/vae/...")
            print(f"      /runpod-volume/models/Wan2.2-I2V-A14B/loras/...")
            return False
        else:
            print(f"   ℹ️  Using: {ckpt_dir}")
            return True
    else:
        print(f"❌ Health check failed: {result}")
        return False

def test_wan_cli_i2v():
    """Test WAN CLI I2V generation"""
    print("\n" + "=" * 70)
    print("🧪 Testing WAN CLI I2V Mode...")
    print("=" * 70)
    
    print("\n⚠️  Note: WAN CLI expects hierarchical directory structure:")
    print("   /path/to/models/Wan2.2-I2V-A14B/")
    print("       ├── diffusion_models/")
    print("       ├── vae/")
    print("       ├── loras/")
    print("       └── text_encoders/")
    
    print("\n📤 Submitting WAN CLI I2V job...")
    
    payload = {
        "input": {
            "action": "generate",
            "task": "i2v-A14B",
            "reference_image_url": "https://picsum.photos/512/512",
            "prompt": "slow camera pan revealing depth",
            "size": "512*512",
            "frame_num": 16,
            "sample_steps": 10,
            "convert_model_dtype": True
        }
    }
    
    r = requests.post(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json=payload,
        timeout=30
    )
    
    result = r.json()
    job_id = result.get("id")
    print(f"✅ Job submitted: {job_id}")
    
    # Poll for results
    print("\n⏳ Waiting for completion (up to 5 minutes)...")
    for i in range(60):
        time.sleep(5)
        
        r = requests.get(
            f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        
        status_result = r.json()
        status = status_result.get("status")
        
        elapsed = (i + 1) * 5
        print(f"[{elapsed}s] Status: {status}")
        
        if status == "COMPLETED":
            print("\n✅ WAN CLI I2V SUCCEEDED!")
            output = status_result.get("output", {})
            
            if "video_url" in output:
                print(f"\n🎬 Video URL: {output['video_url']}")
            
            if "outputs" in output:
                print(f"📊 Generated {len(output['outputs'])} file(s)")
            
            print(f"\n📝 Full output:")
            print(json.dumps(output, indent=2)[:1000])
            return True
            
        elif status == "FAILED":
            print("\n❌ WAN CLI I2V FAILED!")
            error = status_result.get("error", "Unknown error")
            print(f"\n💥 Error Details:")
            
            if isinstance(error, dict):
                error_msg = error.get("error_message", str(error))
                print(error_msg)
                
                if "No such file or directory" in error_msg or "model" in error_msg.lower():
                    print("\n❓ Likely cause: Hierarchical directory structure not found")
                    print("   WAN CLI needs: /path/Wan2.2-I2V-A14B/diffusion_models/...")
                    print("   You have: /runpod-volume/models/wan2.2_i2v_*.safetensors")
            else:
                print(error)
            
            return False
    
    print("\n⏰ Timeout after 5 minutes")
    return False

def suggest_solutions():
    """Suggest solutions based on current setup"""
    print("\n" + "=" * 70)
    print("💡 Solutions for Your Setup")
    print("=" * 70)
    
    print("\n**Current Situation:**")
    print("  - Models: Flat structure at /runpod-volume/models/")
    print("  - WAN CLI: Expects hierarchical structure")
    print("  - ComfyUI: Works with flat structure (via extra_model_paths.yaml)")
    
    print("\n**Option 1: Use ComfyUI Workflows (Recommended)**")
    print("  ✅ Already configured for your flat model structure")
    print("  ✅ More flexible and customizable")
    print("  ⚠️  Need to add video nodes to Dockerfile")
    print("  📝 Action: Run 'discover_comfyui_nodes.py' to check nodes")
    print("         Then update Dockerfile with video nodes")
    
    print("\n**Option 2: Reorganize Models for WAN CLI**")
    print("  ❌ Requires restructuring /runpod-volume/models/")
    print("  📝 Create structure:")
    print("     mkdir -p /runpod-volume/models/Wan2.2-I2V-A14B/{diffusion_models,vae,loras,text_encoders}")
    print("     mv /runpod-volume/models/wan2.2_i2v*.safetensors /runpod-volume/models/Wan2.2-I2V-A14B/diffusion_models/")
    print("     # ... move other files to appropriate folders")
    
    print("\n**Option 3: Hybrid Approach**")
    print("  ✅ Keep flat structure for ComfyUI")
    print("  ✅ Use symlinks for WAN CLI")
    print("  📝 Add to bootstrap.sh:")
    print("     # Create WAN CLI compatible structure with symlinks")
    print("     mkdir -p /workspace/wan_models/Wan2.2-I2V-A14B")
    print("     ln -s /runpod-volume/models /workspace/wan_models/Wan2.2-I2V-A14B/diffusion_models")
    print("     export WAN_CKPT_DIR=/workspace/wan_models")
    
    print("\n**Recommended Next Steps:**")
    print("1. Add video nodes to Dockerfile (already done ✅)")
    print("2. Commit and rebuild")
    print("3. Test ComfyUI workflow again")
    print("4. Once ComfyUI works, decide if WAN CLI is needed")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("WAN CLI Configuration Checker")
    print("=" * 70)
    
    # Check current paths
    flat_structure = not check_model_paths()
    
    if flat_structure:
        print("\n⚠️  Flat model structure detected")
        print("   WAN CLI will not work without reorganization")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--force-test":
            print("\n   Testing anyway (will likely fail)...")
            test_wan_cli_i2v()
        else:
            print("\n   Skipping WAN CLI test")
            print("   Use --force-test to test anyway")
    else:
        # Test WAN CLI
        success = test_wan_cli_i2v()
        
        if not success:
            print("\n⚠️  WAN CLI test failed")
    
    # Show solutions
    suggest_solutions()
    
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
