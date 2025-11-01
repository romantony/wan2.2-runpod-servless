#!/usr/bin/env python3
"""
Discover available ComfyUI nodes in the deployed environment
"""
import requests
import json
import os

API_KEY = os.environ.get("RUNPOD_API_KEY", "YOUR_API_KEY_HERE")
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "YOUR_ENDPOINT_ID_HERE")

def discover_nodes():
    """Query ComfyUI for available node types"""
    print("🔍 Discovering ComfyUI Nodes...")
    print("=" * 70)
    
    # Create a simple workflow that queries object info
    test_workflow = {
        "1": {
            "inputs": {},
            "class_type": "GetObjectInfo",
            "_meta": {"title": "Query Nodes"}
        }
    }
    
    # Also try direct ComfyUI API call via handler
    payload = {
        "input": {
            "action": "comfyui_workflow",
            "workflow": test_workflow,
            "check_nodes": True
        }
    }
    
    try:
        response = requests.post(
            f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=payload,
            timeout=60
        )
        
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("✅ Successfully queried ComfyUI\n")
            print(json.dumps(output, indent=2)[:2000])
        else:
            print(f"⚠️ Status: {result.get('status')}")
            print(f"Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_basic_nodes():
    """Test which basic node types are available"""
    print("\n" + "=" * 70)
    print("🧪 Testing Common Node Types...")
    print("=" * 70)
    
    node_types_to_test = [
        # Loaders
        ("LoadImage", "Image loader"),
        ("VAELoader", "VAE loader"),
        ("UNETLoader", "Diffusion model loader"),
        ("CheckpointLoaderSimple", "Checkpoint loader"),
        ("CLIPLoader", "CLIP loader"),
        ("DualCLIPLoader", "Dual CLIP loader"),
        ("LoraLoader", "LoRA loader"),
        
        # Encoders
        ("CLIPTextEncode", "Text encoder"),
        ("VAEEncode", "VAE encoder"),
        
        # Samplers
        ("KSampler", "K-sampler"),
        
        # Decoders
        ("VAEDecode", "VAE decoder"),
        
        # Video
        ("EmptyLatentVideo", "Video latent creator"),
        ("VHS_VideoCombine", "Video combiner"),
        ("LoadVideo", "Video loader"),
        
        # Output
        ("SaveImage", "Image saver"),
    ]
    
    for node_type, description in node_types_to_test:
        workflow = {
            "1": {
                "inputs": {},
                "class_type": node_type,
                "_meta": {"title": f"Test {node_type}"}
            }
        }
        
        payload = {
            "input": {
                "action": "comfyui_workflow",
                "workflow": workflow
            }
        }
        
        try:
            response = requests.post(
                f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=payload,
                timeout=30
            )
            
            result = response.json()
            status = result.get("status")
            
            if status == "COMPLETED":
                print(f"✅ {node_type:30s} - {description}")
            elif status == "FAILED":
                error_msg = str(result.get("error", ""))
                if "Cannot import" in error_msg or "class_type" in error_msg:
                    print(f"❌ {node_type:30s} - NOT AVAILABLE")
                else:
                    print(f"⚠️  {node_type:30s} - {error_msg[:50]}...")
            else:
                print(f"❓ {node_type:30s} - Unknown status: {status}")
                
        except Exception as e:
            print(f"❌ {node_type:30s} - Exception: {str(e)[:40]}")

def check_custom_nodes():
    """Check what custom node packages are installed"""
    print("\n" + "=" * 70)
    print("📦 Checking Custom Node Packages...")
    print("=" * 70)
    
    # Query through handler to list custom nodes directory
    payload = {
        "input": {
            "action": "comfyui_workflow",
            "workflow": {
                "1": {
                    "inputs": {"text": "list custom nodes"},
                    "class_type": "Note",
                    "_meta": {"title": "Custom Nodes"}
                }
            }
        }
    }
    
    print("\nTo check installed custom nodes, SSH into pod and run:")
    print("  ls -la /workspace/runpod-slim/ComfyUI/custom_nodes/")
    print("\nExpected for video generation:")
    print("  - ComfyUI-VideoHelperSuite (for VHS_VideoCombine, EmptyLatentVideo)")
    print("  - ComfyUI-Advanced-ControlNet (for advanced features)")
    print("  - WAN specific nodes (if any)")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ComfyUI Node Discovery Tool")
    print("=" * 70)
    
    # Test basic node availability
    test_basic_nodes()
    
    # Check custom nodes
    check_custom_nodes()
    
    print("\n" + "=" * 70)
    print("Discovery Complete!")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("1. Add missing nodes to Dockerfile if needed")
    print("2. Adjust workflow functions to use available nodes")
    print("3. Test WAN CLI mode as alternative")
