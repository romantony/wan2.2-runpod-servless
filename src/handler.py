import os, io, json, time, base64, shutil, subprocess, uuid, requests, runpod

WAN_HOME = os.environ.get("WAN_HOME","/workspace/Wan2.2")
WAN_CKPT_DIR = os.environ.get("WAN_CKPT_DIR","/workspace/models")
OUT_DIR = os.environ.get("WAN_OUT_DIR","/workspace/outputs")
os.makedirs(OUT_DIR, exist_ok=True)

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
    size = args.get("size","1280*720")
    prompt = args.get("prompt","")
    seed = str(args.get("seed","")) if args.get("seed") is not None else ""
    offload = str(args.get("offload_model","True"))
    t5_cpu = str(args.get("t5_cpu","True"))
    cmd = ["python3", f"{WAN_HOME}/generate.py",
           "--task","i2v-A14B",
           "--size",size,
           "--ckpt_dir",WAN_CKPT_DIR,
           "--image",image_path,
           "--offload_model",offload,
           "--convert_model_dtype"]
    if t5_cpu.lower() in ("1","true","yes"): cmd += ["--t5_cpu"]
    if prompt is not None: cmd += ["--prompt", str(prompt)]
    if seed: cmd += ["--base_seed", seed]
    return cmd

def _run(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=WAN_HOME)
    out, err = p.communicate()
    return p.returncode, out, err

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
    img = _download_ref_image(params)
    if not img: return {"error":"Missing reference image (url/base64/path)."}
    JOBS[rid] = {"status":"RUNNING","started":time.time()}
    code,out,err = _run(_build_cmd(params, img))
    if code!=0:
        JOBS[rid].update({"status":"ERROR","completed_at":time.time(),"error":err[-4000:]})
        return {"request_id":rid, "status":JOBS[rid]}
    mp4 = _find_latest_mp4(WAN_HOME)
    if mp4:
        os.makedirs(OUT_DIR, exist_ok=True)
        dst = os.path.join(OUT_DIR, f"{rid}.mp4")
        shutil.copy2(mp4, dst)
        JOBS[rid].update({"status":"COMPLETED","completed_at":time.time(),"outputs":[dst]})
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

def handler(event):
    if event.get("health"):
        ok = os.path.isdir(WAN_HOME) and os.path.isdir(WAN_CKPT_DIR)
        return {"ok": ok, "wan_home": WAN_HOME, "ckpt_dir": WAN_CKPT_DIR}
    action = (event.get("action") or "").lower()
    if action in ("request","generate","create"): return handle_request(event)
    if action in ("status","get","result"): return handle_status(event)
    if "inputs" in event or "params" in event:
        event["action"]="request"; return handle_request(event)
    return {"error":"Unsupported event. Use action=request|status or provide inputs."}

runpod.serverless.start({"handler": handler})
