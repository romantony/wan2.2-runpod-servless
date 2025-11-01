import os, io, json, time, base64, shutil, subprocess, uuid, requests, runpod, threading
from comfyui_client import ComfyUIClient, create_i2v_workflow, create_s2v_workflow

WAN_HOME = os.environ.get("WAN_HOME","/workspace/Wan2.2")
WAN_CKPT_DIR = os.environ.get("WAN_CKPT_DIR","/workspace/models")
COMFYUI_ROOT = os.environ.get("COMFYUI_ROOT","/workspace/runpod-slim/ComfyUI")
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = os.environ.get("COMFYUI_PORT", "8188")

# Be tolerant to common RunPod Serverless mount path defaults
if not os.path.isdir(WAN_CKPT_DIR) and os.path.isdir("/runpod-volume"):
    WAN_CKPT_DIR = "/runpod-volume"
OUT_DIR = os.environ.get("WAN_OUT_DIR","/workspace/outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# Initialize ComfyUI client
comfyui_client = ComfyUIClient(f"http://{COMFYUI_HOST}:{COMFYUI_PORT}")

def _download_ref_image(inputs):
    os.makedirs("/workspace/ref", exist_ok=True)
    url = inputs.get("reference_image_url") or inputs.get("image_url")
    if url:
        import os as _os
        ext = ".png"
        try: ext = _os.path.splitext(url.split("?")[0])[1] or ".png"
        except: pass
        path = f"/workspace/ref/{uuid.uuid4().hex}{ext}"
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(path,"wb") as f:
                for chunk in r.iter_content(8192): f.write(chunk)
        return path
    b64 = inputs.get("reference_image_base64") or inputs.get("image_base64")
    if b64:
        if "," in b64: b64 = b64.split(",",1)[1]
        data = base64.b64decode(b64)
        path = f"/workspace/ref/{uuid.uuid4().hex}.png"
        open(path,"wb").write(data); return path
    p = inputs.get("reference_image_path") or inputs.get("image_path")
    if p and os.path.exists(p): return p
    return None

def _build_cmd(args, image_path):
    # Support selecting WAN task: default i2v-A14B; allow s2v-* from request
    task = str(args.get("task", "i2v-A14B")).strip() or "i2v-A14B"
    size = args.get("size","1280*720")
    prompt = args.get("prompt","")
    seed = str(args.get("seed","")) if args.get("seed") is not None else ""
    offload = str(args.get("offload_model","True"))
    t5_cpu = str(args.get("t5_cpu","True"))

    # Determine the correct model directory based on task
    # WAN expects ckpt_dir to point to the specific model folder (e.g., Wan2.2-T2V-A14B)
    task_upper = task.upper()
    if "T2V" in task_upper:
        model_name = "Wan2.2-T2V-A14B"
    elif "I2V" in task_upper:
        model_name = "Wan2.2-I2V-A14B"
    elif "S2V" in task_upper:
        model_name = "Wan2.2-S2V-14B"
    elif "TI2V" in task_upper:
        model_name = "Wan2.2-TI2V-5B"
    elif "ANIMATE" in task_upper:
        model_name = "Wan2.2-Animate-14B"
    else:
        # Default to task name with capitalization
        model_name = f"Wan2.2-{task}"
    
    # Construct full checkpoint directory path
    model_ckpt_dir = os.path.join(WAN_CKPT_DIR, model_name)
    
    # If the model directory doesn't exist, try without the prefix
    # (in case user already has it in the exact format)
    if not os.path.isdir(model_ckpt_dir):
        model_ckpt_dir = WAN_CKPT_DIR

    cmd = [
        "python3", f"{WAN_HOME}/generate.py",
        "--task", task,
        "--size", size,
        "--ckpt_dir", model_ckpt_dir,
        "--offload_model", offload,
    ]
    # Only pass image flag for i2v tasks
    if task.lower().startswith("i2v") and image_path:
        cmd += ["--image", image_path]

    # Optional: dtype conversion to optimize VRAM
    if str(args.get("convert_model_dtype", True)).lower() in ("1","true","yes"):
        cmd += ["--convert_model_dtype"]

    if t5_cpu.lower() in ("1","true","yes"):
        cmd += ["--t5_cpu"]
    if prompt is not None:
        cmd += ["--prompt", str(prompt)]
    if seed:
        cmd += ["--base_seed", seed]

    # Optional parameters mapping aligned with Wan2.2 generate.py
    opt_map = {
        # core sampling
        "frame_num": "--frame_num",
        "num_frames": "--frame_num",  # alias
        "sample_steps": "--sample_steps",
        "sample_shift": "--sample_shift",
        "sample_guide_scale": "--sample_guide_scale",
        "guidance_scale": "--sample_guide_scale",  # alias
        "cfg_scale": "--sample_guide_scale",       # alias
        "sample_solver": "--sample_solver",        # unipc | dpm++

        # performance / parallelism
        "ulysses_size": "--ulysses_size",
        "t5_fsdp": "--t5_fsdp",
        "dit_fsdp": "--dit_fsdp",

        # prompt extension
        "use_prompt_extend": "--use_prompt_extend",
        "prompt_extend_method": "--prompt_extend_method",
        "prompt_extend_model": "--prompt_extend_model",
        "prompt_extend_target_lang": "--prompt_extend_target_lang",

        # file outputs
        "save_file": "--save_file",

        # animate/s2v extras (safe to pass if user opts-in)
        "src_root_path": "--src_root_path",
        "refert_num": "--refert_num",
        "replace_flag": "--replace_flag",
        "use_relighting_lora": "--use_relighting_lora",
        "start_from_ref": "--start_from_ref",
        "infer_frames": "--infer_frames",
        "audio": "--audio",
        "enable_tts": "--enable_tts",
        "tts_prompt_audio": "--tts_prompt_audio",
        "tts_prompt_text": "--tts_prompt_text",
        "tts_text": "--tts_text",
        "pose_video": "--pose_video",
    }

    for k, flag in opt_map.items():
        if k in args and args[k] is not None and args[k] != "":
            v = args[k]
            if isinstance(v, bool):
                if v:
                    cmd.append(flag)
            else:
                cmd += [flag, str(v)]

    # Extra args passthrough (advanced users):
    # - Accepts a list of strings or a space-delimited string.
    # - Each token is appended as-is, but we restrict overall length.
    extra = args.get("extra_args")
    if extra:
        if isinstance(extra, str):
            tokens = [t for t in extra.strip().split() if t]
        elif isinstance(extra, (list, tuple)):
            tokens = [str(t) for t in extra]
        else:
            tokens = []
        # Guardrail: limit to 50 tokens to avoid abuse
        cmd += tokens[:50]

    return cmd

def _progress(percent: int, status: str):
    """Best-effort progress update across possible RunPod SDK shapes."""
    try:
        # Common signature in newer SDKs
        if hasattr(runpod.serverless, "progress_update"):
            try:
                runpod.serverless.progress_update(percent=percent, status=status)
                return
            except TypeError:
                # Some variants might be positional
                runpod.serverless.progress_update(percent, status)
                return
        # Older util path
        utils = getattr(runpod.serverless, "utils", None)
        if utils is not None:
            rp_prog = getattr(utils, "rp_progress", None)
            if rp_prog is not None and hasattr(rp_prog, "update"):
                rp_prog.update(status=status, percent=percent)
    except Exception:
        # Never fail the job because of progress issues
        pass


def _run_streaming(cmd, heartbeat_s: float = 5.0):
    """Run command, stream stdout, and emit periodic progress heartbeats.
    Returns (returncode, captured_stdout, captured_stderr).
    """
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=WAN_HOME,
        bufsize=1,
        universal_newlines=True,
    )

    captured_out = []
    captured_err = []
    last_hb = time.time()
    percent = 10

    def read_stderr():
        try:
            for line in iter(p.stderr.readline, ""):
                if not line:
                    break
                captured_err.append(line)
        except Exception:
            pass

    t_err = threading.Thread(target=read_stderr, daemon=True)
    t_err.start()

    try:
        for line in iter(p.stdout.readline, ""):
            if not line:
                if p.poll() is not None:
                    break
                continue
            captured_out.append(line)

            # Try to parse crude percent patterns like "xx%"
            try:
                if "%" in line:
                    # find last percentage number in line
                    for tok in line.strip().split():
                        if tok.endswith("%") and tok[:-1].isdigit():
                            percent = max(percent, min(95, int(tok[:-1])))
                            break
            except Exception:
                pass

            # Heartbeat
            if time.time() - last_hb >= heartbeat_s:
                _progress(percent, "Generating video...")
                percent = min(95, percent + 3)
                last_hb = time.time()

        # Ensure one last heartbeat if it took long without output
        if time.time() - last_hb >= heartbeat_s:
            _progress(percent, "Finalizing...")
    finally:
        try:
            p.wait(timeout=600)
        except Exception:
            pass

    return p.returncode, "".join(captured_out), "".join(captured_err)

def _find_latest_mp4(base_dir):
    best, bestm = None, -1.0
    for r,_,fs in os.walk(base_dir):
        for f in fs:
            if f.lower().endswith(".mp4"):
                p = os.path.join(r,f); m=os.path.getmtime(p)
                if m>bestm: best,bestm=p,m
    return best

JOBS = {}

def handle_request(event):
    rid = str(uuid.uuid4())
    params = event.get("params") or event.get("inputs") or {}
    task = str(params.get("task","i2v-A14B")).strip() or "i2v-A14B"
    img = None
    if task.lower().startswith("i2v"):
        img = _download_ref_image(params)
        if not img:
            return {"error":"Missing reference image (url/base64/path) for i2v task."}
    JOBS[rid] = {"status":"RUNNING","started":time.time()}
    _progress(5, "Starting generation...")
    # Prefer directing WAN to save into our outputs dir
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
    except Exception:
        pass
    dst = os.path.join(OUT_DIR, f"{rid}.mp4")
    # do not override if user explicitly set save_file
    params = dict(params)
    params.setdefault("save_file", dst)
    code,out,err = _run_streaming(_build_cmd(params, img))
    if code!=0:
        JOBS[rid].update({"status":"ERROR","completed_at":time.time(),"error":err[-4000:]})
        return {"request_id":rid, "status":JOBS[rid]}
    mp4 = dst if os.path.exists(dst) else _find_latest_mp4(WAN_HOME)
    if mp4:
        os.makedirs(OUT_DIR, exist_ok=True)
        dst = os.path.join(OUT_DIR, f"{rid}.mp4")
        shutil.copy2(mp4, dst)
        JOBS[rid].update({"status":"COMPLETED","completed_at":time.time(),"outputs":[dst]})
        _progress(100, "Completed")
        if event.get("return_video", True):
            b64 = base64.b64encode(open(dst,"rb").read()).decode("utf-8")
            return {"request_id":rid,"status":JOBS[rid],"result":{"filename":os.path.basename(dst),"data":"data:video/mp4;base64,"+b64}}
        return {"request_id":rid,"status":JOBS[rid],"result_path":dst}
    JOBS[rid].update({"status":"NO_OUTPUT","completed_at":time.time()})
    return {"request_id":rid,"status":JOBS[rid]}

def handle_status(event):
    rid = event.get("request_id") or event.get("id")
    if not rid: return {"error":"Missing request_id"}
    st = JOBS.get(rid)
    if not st:
        p = os.path.join(OUT_DIR, f"{rid}.mp4")
        if os.path.exists(p):
            st = {"status":"COMPLETED","started":time.time(),"completed_at":os.path.getmtime(p),"outputs":[p]}
            JOBS[rid]=st
        else:
            return {"error":f"Unknown request_id: {rid}"}
    res = {"request_id":rid,"status":st}
    if event.get("return_video", False) and st.get("outputs"):
        p = st["outputs"][0]
        if os.path.exists(p):
            b64 = base64.b64encode(open(p,"rb").read()).decode("utf-8")
            res["result"] = {"filename":os.path.basename(p),"data":"data:video/mp4;base64,"+b64}
    return res

def _normalize_event(event):
    try:
        if isinstance(event, dict) and isinstance(event.get("input"), dict):
            return event["input"]
    except Exception:
        pass
    return event or {}


# ComfyUI Handlers

def handle_comfyui_workflow(event):
    """Execute a ComfyUI workflow"""
    rid = str(uuid.uuid4())
    params = event.get("params") or event.get("inputs") or {}
    
    # Get workflow from params
    workflow = params.get("workflow")
    if not workflow:
        return {"error": "Missing 'workflow' parameter"}
    
    _progress(5, "Preparing ComfyUI workflow...")
    
    # Handle image uploads if present
    images = params.get("images", [])
    for img in images:
        img_name = img.get("name", "input.png")
        img_data = img.get("data") or img.get("image")
        
        if img_data:
            result = comfyui_client.upload_image(img_data, img_name)
            if "error" in result:
                return {"error": f"Image upload failed: {result['error']}"}
    
    _progress(20, "Executing workflow...")
    
    # Execute the workflow
    timeout = params.get("timeout", 600)
    result = comfyui_client.execute_workflow(workflow, timeout)
    
    if result.get("status") != "completed":
        return {"request_id": rid, "error": result.get("error", "Workflow execution failed"), "result": result}
    
    _progress(90, "Collecting outputs...")
    
    # Save outputs
    outputs = []
    for output in result.get("outputs", []):
        filename = output.get("filename", f"{rid}_output.png")
        output_path = os.path.join(OUT_DIR, filename)
        
        # Save the file
        file_data = base64.b64decode(output.get("data", ""))
        with open(output_path, "wb") as f:
            f.write(file_data)
        
        outputs.append({
            "filename": filename,
            "path": output_path,
            "size": len(file_data)
        })
    
    _progress(100, "Completed")
    
    # Return results
    if params.get("return_base64", False):
        return {
            "request_id": rid,
            "status": "completed",
            "outputs": [
                {
                    "filename": o["filename"],
                    "data": base64.b64encode(open(o["path"], "rb").read()).decode("utf-8"),
                    "size": o["size"]
                }
                for o in outputs
            ]
        }
    else:
        return {
            "request_id": rid,
            "status": "completed",
            "outputs": outputs
        }


def handle_comfyui_i2v(event):
    """Handle Image-to-Video via ComfyUI"""
    rid = str(uuid.uuid4())
    params = event.get("params") or event.get("inputs") or {}
    
    # Download/get input image
    image_path = _download_ref_image(params)
    if not image_path:
        return {"error": "Missing reference image (url/base64/path) for I2V task"}
    
    _progress(5, "Uploading image to ComfyUI...")
    
    # Upload image to ComfyUI
    image_name = f"{rid}_input.png"
    upload_result = comfyui_client.upload_image(image_path, image_name)
    
    if "error" in upload_result:
        return {"error": f"Image upload failed: {upload_result['error']}"}
    
    _progress(15, "Creating I2V workflow...")
    
    # Create workflow
    workflow = create_i2v_workflow(
        image_filename=image_name,
        diffusion_model=params.get("diffusion_model", "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"),
        vae_model=params.get("vae_model", "wan_2.1_vae.safetensors"),
        prompt=params.get("prompt", ""),
        seed=params.get("seed", -1),
        steps=params.get("steps", 20),
        cfg_scale=params.get("cfg_scale", 7.0),
        use_lora=params.get("use_lora", False),
        lora_name=params.get("lora_name", "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"),
        lora_strength=params.get("lora_strength", 1.0)
    )
    
    _progress(25, "Executing I2V generation...")
    
    # Execute workflow
    timeout = params.get("timeout", 600)
    result = comfyui_client.execute_workflow(workflow, timeout)
    
    if result.get("status") != "completed":
        return {"request_id": rid, "error": result.get("error", "I2V generation failed"), "result": result}
    
    _progress(95, "Saving outputs...")
    
    # Save outputs
    outputs = []
    for output in result.get("outputs", []):
        filename = f"{rid}_i2v_output.mp4"
        output_path = os.path.join(OUT_DIR, filename)
        
        file_data = base64.b64decode(output.get("data", ""))
        with open(output_path, "wb") as f:
            f.write(file_data)
        
        outputs.append(output_path)
    
    _progress(100, "Completed")
    
    if params.get("return_video", True) and outputs:
        video_data = open(outputs[0], "rb").read()
        return {
            "request_id": rid,
            "status": "completed",
            "result": {
                "filename": os.path.basename(outputs[0]),
                "data": "data:video/mp4;base64," + base64.b64encode(video_data).decode("utf-8")
            }
        }
    else:
        return {
            "request_id": rid,
            "status": "completed",
            "outputs": outputs
        }


def handle_comfyui_models(event):
    """List available models in ComfyUI"""
    models = comfyui_client.get_available_models()
    return {
        "status": "success",
        "models": models
    }


def handler(event):
    # Unwrap RunPod job wrapper shape: { id, input: { ... } }
    event = _normalize_event(event)
    
    # Health check
    if event.get("health"):
        wan_ok = os.path.isdir(WAN_HOME) and os.path.isdir(WAN_CKPT_DIR)
        comfyui_ok = comfyui_client.health_check()
        return {
            "ok": wan_ok and comfyui_ok,
            "wan_home": WAN_HOME,
            "ckpt_dir": WAN_CKPT_DIR,
            "comfyui_url": comfyui_client.url,
            "comfyui_status": "online" if comfyui_ok else "offline"
        }
    
    action = (event.get("action") or "").lower()
    
    # ComfyUI actions
    if action == "comfyui_workflow":
        return handle_comfyui_workflow(event)
    if action == "comfyui_i2v":
        return handle_comfyui_i2v(event)
    if action == "comfyui_models":
        return handle_comfyui_models(event)
    
    # WAN actions
    if action in ("request","generate","create"):
        return handle_request(event)
    if action in ("status","get","result"):
        return handle_status(event)
    
    # Auto-detect action
    if "workflow" in event:
        return handle_comfyui_workflow(event)
    if "inputs" in event or "params" in event:
        event["action"]="request"
        return handle_request(event)
    
    return {"error": "Unsupported event. Use action=request|status|comfyui_workflow|comfyui_i2v|comfyui_models"}

runpod.serverless.start({"handler": handler})
