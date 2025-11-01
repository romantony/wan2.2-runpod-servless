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
    use_lora=False,
    lora_name="wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
    lora_strength=1.0
):
    """
    Create a ComfyUI workflow for Image-to-Video generation
    
    This is a template - you'll need to customize based on your ComfyUI nodes
    """
    workflow = {
        "1": {
            "inputs": {
                "unet_name": diffusion_model
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Load Diffusion Model"}
        },
        "2": {
            "inputs": {
                "vae_name": vae_model
            },
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        "3": {
            "inputs": {
                "image": image_filename,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Load Input Image"}
        },
        "4": {
            "inputs": {
                "text": prompt,
                "clip": ["5", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Encode Prompt"}
        },
        "5": {
            "inputs": {
                "clip_name1": text_encoder,
                "type": "wan"
            },
            "class_type": "CLIPLoader",
            "_meta": {"title": "Load Text Encoder"}
        }
    }
    
    # Add LoRA if requested
    if use_lora:
        workflow["6"] = {
            "inputs": {
                "lora_name": lora_name,
                "strength_model": lora_strength,
                "model": ["1", 0]
            },
            "class_type": "LoraLoader",
            "_meta": {"title": "Load LoRA"}
        }
    
    return workflow


def create_s2v_workflow(
    audio_filename,
    diffusion_model="wan2.2_s2v_14B_fp8_scaled.safetensors",
    vae_model="wan_2.1_vae.safetensors",
    audio_encoder="wav2vec2_large_english_fp16.safetensors",
    prompt="",
    seed=-1,
    steps=20
):
    """
    Create a ComfyUI workflow for Sound-to-Video generation
    """
    # This is a template - customize based on your actual ComfyUI nodes
    workflow = {
        "1": {
            "inputs": {
                "unet_name": diffusion_model
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Load S2V Model"}
        },
        "2": {
            "inputs": {
                "vae_name": vae_model
            },
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        "3": {
            "inputs": {
                "audio_encoder_name": audio_encoder
            },
            "class_type": "AudioEncoderLoader",
            "_meta": {"title": "Load Audio Encoder"}
        }
    }
    
    return workflow
