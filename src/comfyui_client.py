# ComfyUI API Integration Module
# Handles ComfyUI workflow execution, image uploads, and output retrieval

import os
import uuid
import json
import base64
import time
import requests
import websocket
from io import BytesIO
from urllib.parse import urlencode

COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = os.environ.get("COMFYUI_PORT", "8188")
COMFYUI_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

class ComfyUIClient:
    """Client for interacting with ComfyUI API"""
    
    def __init__(self, url=COMFYUI_URL):
        self.url = url
        self.client_id = str(uuid.uuid4())
        
    def health_check(self):
        """Check if ComfyUI server is responding"""
        try:
            response = requests.get(f"{self.url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"ComfyUI health check failed: {e}")
            return False
    
    def upload_image(self, image_data, filename="input.png", overwrite=True):
        """
        Upload an image to ComfyUI
        
        Args:
            image_data: bytes or base64 string or file path
            filename: name for the uploaded file
            overwrite: whether to overwrite existing file
            
        Returns:
            dict with upload result
        """
        # Handle different input types
        if isinstance(image_data, str):
            if image_data.startswith("data:"):
                # Base64 data URI
                image_data = image_data.split(",", 1)[1]
                image_data = base64.b64decode(image_data)
            elif os.path.exists(image_data):
                # File path
                with open(image_data, "rb") as f:
                    image_data = f.read()
            else:
                # Assume it's base64
                image_data = base64.b64decode(image_data)
        
        files = {
            "image": (filename, BytesIO(image_data), "image/png"),
            "overwrite": (None, str(overwrite).lower())
        }
        
        try:
            response = requests.post(
                f"{self.url}/upload/image",
                files=files,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Image upload failed: {str(e)}"}
    
    def queue_prompt(self, workflow):
        """
        Queue a workflow for execution
        
        Args:
            workflow: dict containing ComfyUI workflow/prompt
            
        Returns:
            dict with prompt_id and execution info
        """
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        try:
            response = requests.post(
                f"{self.url}/prompt",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Queue prompt failed: {str(e)}"}
    
    def get_history(self, prompt_id):
        """
        Get execution history for a prompt
        
        Args:
            prompt_id: ID of the queued prompt
            
        Returns:
            dict with execution history and outputs
        """
        try:
            response = requests.get(
                f"{self.url}/history/{prompt_id}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Get history failed: {str(e)}"}
    
    def get_image(self, filename, subfolder="", folder_type="output"):
        """
        Retrieve an output image/video from ComfyUI
        
        Args:
            filename: name of the file
            subfolder: subfolder path
            folder_type: "output", "input", or "temp"
            
        Returns:
            bytes of the file
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        url = f"{self.url}/view?{urlencode(params)}"
        
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Get image failed: {e}")
            return None
    
    def get_available_models(self):
        """Get list of available models from ComfyUI"""
        try:
            response = requests.get(f"{self.url}/object_info", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            models = {}
            if "UNETLoader" in data:
                models["diffusion_models"] = data["UNETLoader"]["input"]["required"]["unet_name"][0]
            if "VAELoader" in data:
                models["vae"] = data["VAELoader"]["input"]["required"]["vae_name"][0]
            if "LoraLoader" in data:
                models["loras"] = data["LoraLoader"]["input"]["required"]["lora_name"][0]
            if "CheckpointLoaderSimple" in data:
                models["checkpoints"] = data["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
            
            return models
        except Exception as e:
            return {"error": f"Get models failed: {str(e)}"}
    
    def wait_for_completion(self, prompt_id, timeout=600, check_interval=2):
        """
        Wait for a prompt to complete execution
        
        Args:
            prompt_id: ID of the queued prompt
            timeout: maximum time to wait in seconds
            check_interval: how often to check status in seconds
            
        Returns:
            dict with execution results
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            
            if "error" in history:
                return history
            
            if prompt_id in history:
                result = history[prompt_id]
                
                # Check if completed
                if "outputs" in result:
                    return {
                        "status": "completed",
                        "outputs": result["outputs"],
                        "prompt_id": prompt_id
                    }
                
                # Check for errors
                if "status" in result and result["status"].get("status_str") == "error":
                    return {
                        "status": "error",
                        "error": result.get("status", {}).get("messages", ["Unknown error"]),
                        "prompt_id": prompt_id
                    }
            
            time.sleep(check_interval)
        
        return {
            "status": "timeout",
            "error": f"Execution did not complete within {timeout}s",
            "prompt_id": prompt_id
        }
    
    def execute_workflow(self, workflow, timeout=600):
        """
        Execute a complete workflow and wait for results
        
        Args:
            workflow: ComfyUI workflow dict
            timeout: maximum time to wait
            
        Returns:
            dict with results and output files
        """
        # Queue the workflow
        queue_result = self.queue_prompt(workflow)
        
        if "error" in queue_result:
            return queue_result
        
        prompt_id = queue_result.get("prompt_id")
        if not prompt_id:
            return {"error": "No prompt_id returned from queue"}
        
        # Wait for completion
        result = self.wait_for_completion(prompt_id, timeout)
        
        if result.get("status") != "completed":
            return result
        
        # Collect output files
        outputs = []
        for node_id, node_output in result.get("outputs", {}).items():
            if "images" in node_output:
                for img_info in node_output["images"]:
                    filename = img_info.get("filename")
                    subfolder = img_info.get("subfolder", "")
                    file_type = img_info.get("type", "output")
                    
                    # Download the file
                    file_data = self.get_image(filename, subfolder, file_type)
                    
                    if file_data:
                        outputs.append({
                            "filename": filename,
                            "data": base64.b64encode(file_data).decode("utf-8"),
                            "size": len(file_data),
                            "node_id": node_id
                        })
        
        return {
            "status": "completed",
            "prompt_id": prompt_id,
            "outputs": outputs
        }


# Helper functions for common WAN 2.2 workflows

def create_i2v_workflow(
    image_filename,
    diffusion_model="wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors",
    vae_model="wan_2.1_vae.safetensors",
    text_encoder="umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    prompt="",
    seed=-1,
    steps=20,
    cfg_scale=7.0,
    width=1280,
    height=720,
    num_frames=121,
    fps=24,
    use_lora=False,
    lora_name="wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
    lora_strength=1.0,
    sampler_name="euler",
    scheduler="normal",
    denoise=1.0
):
    """
    Create a ComfyUI workflow for WAN 2.2 Image-to-Video generation
    
    This workflow follows the pattern:
    LoadImage → VAEEncode → UNetLoader → CLIPTextEncode → KSampler → VAEDecode → SaveVideo
    
    Parameters:
    - image_filename: Name of the uploaded image in ComfyUI
    - diffusion_model: WAN 2.2 I2V model (high_noise or low_noise)
    - vae_model: VAE model for encoding/decoding
    - text_encoder: Text encoder model (UMT5-XXL)
    - prompt: Text prompt for generation
    - seed: Random seed (-1 for random)
    - steps: Number of diffusion steps (4 with LoRA, 20 without)
    - cfg_scale: Classifier-free guidance scale
    - width, height: Output video dimensions
    - num_frames: Number of frames to generate
    - fps: Frames per second
    - use_lora: Whether to use LightX2V acceleration
    - lora_name: LoRA model name
    - lora_strength: LoRA strength (0.0-1.0)
    - sampler_name: Sampler to use
    - scheduler: Scheduler to use
    - denoise: Denoising strength
    """
    import random
    
    # Generate random seed if -1
    if seed == -1:
        seed = random.randint(0, 2**32 - 1)
    
    # Build workflow
    # Node 1: Load input image
    workflow = {
        "1": {
            "inputs": {
                "image": image_filename,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Load Input Image"}
        }
    }
    
    # Node 2: Load VAE
    workflow["2"] = {
        "inputs": {
            "vae_name": vae_model
        },
        "class_type": "VAELoader",
        "_meta": {"title": "Load VAE"}
    }
    
    # Node 3: Load Diffusion Model (UNET)
    model_input_node = "3"
    workflow["3"] = {
        "inputs": {
            "unet_name": diffusion_model
        },
        "class_type": "UNETLoader",
        "_meta": {"title": "Load Diffusion Model"}
    }
    
    # Node 4: Load LoRA (optional)
    if use_lora:
        workflow["4"] = {
            "inputs": {
                "lora_name": lora_name,
                "strength_model": lora_strength,
                "strength_clip": lora_strength,
                "model": [model_input_node, 0],
                "clip": ["3", 1]  # Most UNetLoaders also output CLIP
            },
            "class_type": "LoraLoader",
            "_meta": {"title": "Load LoRA Acceleration"}
        }
        model_input_node = "4"  # Use LoRA output as model input
        clip_node = "4"
    else:
        clip_node = "3"
    
    # Node 5: Load Text Encoder (if CLIP not from UNET)
    # Note: Some implementations have separate CLIP loader
    workflow["5"] = {
        "inputs": {
            "clip_name1": text_encoder,
            "type": "wan"
        },
        "class_type": "DualCLIPLoader",
        "_meta": {"title": "Load Text Encoder"}
    }
    clip_node = "5"
    
    # Node 6: Encode positive prompt
    workflow["6"] = {
        "inputs": {
            "text": prompt if prompt else "high quality video",
            "clip": [clip_node, 0]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Encode Positive Prompt"}
    }
    
    # Node 7: Encode negative prompt
    workflow["7"] = {
        "inputs": {
            "text": "low quality, blurry, distorted",
            "clip": [clip_node, 0]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Encode Negative Prompt"}
    }
    
    # Node 8: VAE Encode input image to latent
    workflow["8"] = {
        "inputs": {
            "pixels": ["1", 0],
            "vae": ["2", 0]
        },
        "class_type": "VAEEncode",
        "_meta": {"title": "Encode Image to Latent"}
    }
    
    # Node 9: Empty Latent Video (for video generation)
    workflow["9"] = {
        "inputs": {
            "width": width,
            "height": height,
            "length": num_frames,
            "batch_size": 1
        },
        "class_type": "EmptyLatentVideo",
        "_meta": {"title": "Create Empty Video Latent"}
    }
    
    # Node 10: KSampler for video generation
    workflow["10"] = {
        "inputs": {
            "seed": seed,
            "steps": steps,
            "cfg": cfg_scale,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "denoise": denoise,
            "model": [model_input_node, 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["9", 0]  # Use empty video latent
        },
        "class_type": "KSampler",
        "_meta": {"title": "Video Generation Sampler"}
    }
    
    # Node 11: VAE Decode latent to video
    workflow["11"] = {
        "inputs": {
            "samples": ["10", 0],
            "vae": ["2", 0]
        },
        "class_type": "VAEDecode",
        "_meta": {"title": "Decode Latent to Video"}
    }
    
    # Node 12: Save video
    workflow["12"] = {
        "inputs": {
            "filename_prefix": "wan_i2v",
            "fps": fps,
            "images": ["11", 0]
        },
        "class_type": "VHS_VideoCombine",
        "_meta": {"title": "Save Video"}
    }
    
    return workflow


def create_s2v_workflow(
    audio_filename,
    diffusion_model="wan2.2_s2v_14B_fp8_scaled.safetensors",
    vae_model="wan_2.1_vae.safetensors",
    audio_encoder="wav2vec2_large_english_fp16.safetensors",
    text_encoder="umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    prompt="",
    seed=-1,
    steps=20,
    cfg_scale=7.0,
    width=1280,
    height=720,
    num_frames=121,
    fps=24,
    sampler_name="euler",
    scheduler="normal",
    denoise=1.0
):
    """
    Create a ComfyUI workflow for WAN 2.2 Sound-to-Video generation
    
    This workflow follows the pattern:
    LoadAudio → AudioEncode → UNetLoader → CLIPTextEncode → KSampler → VAEDecode → SaveVideo
    
    Parameters:
    - audio_filename: Name of the uploaded audio file in ComfyUI
    - diffusion_model: WAN 2.2 S2V model
    - vae_model: VAE model for decoding
    - audio_encoder: Audio encoder model (Wav2Vec2)
    - text_encoder: Text encoder model (UMT5-XXL)
    - prompt: Text prompt for generation
    - seed: Random seed (-1 for random)
    - steps: Number of diffusion steps
    - cfg_scale: Classifier-free guidance scale
    - width, height: Output video dimensions
    - num_frames: Number of frames to generate
    - fps: Frames per second
    - sampler_name: Sampler to use
    - scheduler: Scheduler to use
    - denoise: Denoising strength
    """
    import random
    
    # Generate random seed if -1
    if seed == -1:
        seed = random.randint(0, 2**32 - 1)
    
    # Build workflow
    # Node 1: Load audio file
    workflow = {
        "1": {
            "inputs": {
                "audio": audio_filename
            },
            "class_type": "LoadAudio",
            "_meta": {"title": "Load Input Audio"}
        }
    }
    
    # Node 2: Load Audio Encoder
    workflow["2"] = {
        "inputs": {
            "audio_encoder_name": audio_encoder
        },
        "class_type": "AudioEncoderLoader",
        "_meta": {"title": "Load Audio Encoder"}
    }
    
    # Node 3: Encode audio
    workflow["3"] = {
        "inputs": {
            "audio": ["1", 0],
            "encoder": ["2", 0]
        },
        "class_type": "AudioEncode",
        "_meta": {"title": "Encode Audio"}
    }
    
    # Node 4: Load VAE
    workflow["4"] = {
        "inputs": {
            "vae_name": vae_model
        },
        "class_type": "VAELoader",
        "_meta": {"title": "Load VAE"}
    }
    
    # Node 5: Load Diffusion Model (UNET)
    workflow["5"] = {
        "inputs": {
            "unet_name": diffusion_model
        },
        "class_type": "UNETLoader",
        "_meta": {"title": "Load S2V Model"}
    }
    
    # Node 6: Load Text Encoder
    workflow["6"] = {
        "inputs": {
            "clip_name1": text_encoder,
            "type": "wan"
        },
        "class_type": "DualCLIPLoader",
        "_meta": {"title": "Load Text Encoder"}
    }
    
    # Node 7: Encode positive prompt
    workflow["7"] = {
        "inputs": {
            "text": prompt if prompt else "high quality video synchronized with audio",
            "clip": ["6", 0]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Encode Positive Prompt"}
    }
    
    # Node 8: Encode negative prompt
    workflow["8"] = {
        "inputs": {
            "text": "low quality, blurry, distorted, out of sync",
            "clip": ["6", 0]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Encode Negative Prompt"}
    }
    
    # Node 9: Empty Latent Video
    workflow["9"] = {
        "inputs": {
            "width": width,
            "height": height,
            "length": num_frames,
            "batch_size": 1
        },
        "class_type": "EmptyLatentVideo",
        "_meta": {"title": "Create Empty Video Latent"}
    }
    
    # Node 10: KSampler for S2V generation
    workflow["10"] = {
        "inputs": {
            "seed": seed,
            "steps": steps,
            "cfg": cfg_scale,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "denoise": denoise,
            "model": ["5", 0],
            "positive": ["7", 0],
            "negative": ["8", 0],
            "latent_image": ["9", 0],
            "audio_conditioning": ["3", 0]  # Add audio conditioning
        },
        "class_type": "KSampler",
        "_meta": {"title": "S2V Generation Sampler"}
    }
    
    # Node 11: VAE Decode
    workflow["11"] = {
        "inputs": {
            "samples": ["10", 0],
            "vae": ["4", 0]
        },
        "class_type": "VAEDecode",
        "_meta": {"title": "Decode Latent to Video"}
    }
    
    # Node 12: Save video
    workflow["12"] = {
        "inputs": {
            "filename_prefix": "wan_s2v",
            "fps": fps,
            "images": ["11", 0]
        },
        "class_type": "VHS_VideoCombine",
        "_meta": {"title": "Save Video"}
    }
    
    return workflow
