import os
import json
import requests

def get_app_data_dir():
    return os.path.join(os.path.expanduser("~"), "OmniStudioData")

PER_LIST = 150
PAGE = 1000
TIMEOUT = 90
NSFW_KEYS = ("nsfw", "uncensored", "adult", "porn", "lewd", "hentai",
             "nude", "mature", "erotica", "xxx")

def _is_nsfw(m):
    tags = m.get("tags", [])
    mid = m.get("id", "").lower()
    name = mid.split("/")[-1].replace("-", " ").lower()
    return any(k in tags or k in mid or k in name for k in NSFW_KEYS)

def _seen_ids(formatted_models):
    seen = set()
    for v in formatted_models.values():
        for m in v:
            seen.add(m.get("id"))
    return seen

def _fetch_page(pipeline_tag, skip):
    url = (f"https://huggingface.co/api/models?pipeline_tag={pipeline_tag}"
           f"&sort=downloads&direction=-1&limit={PAGE}&skip={skip}")
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  request failed (skip={skip}, tag={pipeline_tag}): {e}")
    return None

def _fetch_actual_size_gb(model_id):
    url = f"https://huggingface.co/api/models/{model_id}/tree/main"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            files = r.json()
            # Filter files that look like weights
            weight_files = [
                f for f in files 
                if f.get('type') == 'file' 
                and any(f.get('path', '').endswith(ext) for ext in ('.safetensors', '.bin', '.pt', '.gguf'))
            ]
            if weight_files:
                # Prioritize safetensors to avoid counting both formats if present
                safetensors = [f for f in weight_files if f.get('path', '').endswith('.safetensors')]
                if safetensors:
                    total_bytes = sum(f.get('size', 0) for f in safetensors)
                else:
                    total_bytes = sum(f.get('size', 0) for f in weight_files)
                
                size_gb = total_bytes / (1024**3)
                if size_gb > 0.1:
                    return round(size_gb, 1)
    except Exception as e:
        print(f"  [API Size Info] Could not fetch tree for {model_id}: {e}")
    return None

def _get_author_and_desc(model_id, type_name):
    author = model_id.split('/')[0]
    mid = model_id.lower()
    
    # Map common authors and quantized variations to original authors
    if author.lower() in ("nvidia", "huggingface", "hardware-accelerated"):
        if "gemma" in mid:
            author = "Google (квантованная NVIDIA)"
        elif "llama" in mid:
            author = "Meta (квантованная NVIDIA)"
        elif "nemotron" in mid:
            author = "NVIDIA"
        elif "qwen" in mid:
            author = "Alibaba Qwen (квантованная NVIDIA)"
    elif author.lower() == "huihui-ai" and "llama" in mid:
        author = "Meta (модификация huihui-ai)"
    elif author.lower() == "optimum-intel-internal-testing":
        author = "Intel Testing"
    
    if type_name == "photo":
        desc = f"Модель генерации изображений от {author}."
    elif type_name == "video":
        desc = f"Видео-модель от {author}."
    else:
        desc = f"Текстовая нейросеть (LLM) от {author}."
        
    return author, desc

def _image_entry(m):
    tags = m.get("tags", [])
    model_id = m["id"]
    name = model_id.split("/")[-1].replace("-", " ").title()
    
    # Get actual size from Hugging Face tree API
    size_gb = _fetch_actual_size_gb(model_id)
    
    if size_gb is None:
        # Fallback to heuristics
        if "stable-diffusion-xl" in tags or "sdxl" in model_id.lower() or "xl" in model_id.lower():
            size_gb = 6.5
        elif "flux" in model_id.lower():
            size_gb = 12.0
        else:
            size_gb = 4.0
            
    # Classify requirements based on size
    if size_gb >= 11.0:
        model_class, req = "Next-Gen", "GPU: VRAM 12GB+"
    elif size_gb >= 6.0:
        model_class, req = "Next-Gen", "GPU: VRAM 8GB+"
    else:
        model_class, req = "Стандарт", "GPU: VRAM 6GB+"
        
    _, desc = _get_author_and_desc(model_id, "photo")
    
    return {"name": name, "id": model_id, "desc": desc, "size_gb": size_gb,
            "req": req, "load_class": model_class,
            "safety": "NSFW" if _is_nsfw(m) else "SFW", "type": "Photo"}

def _video_entry(m):
    model_id = m["id"]
    name = model_id.split("/")[-1].replace("-", " ").title()
    mid = model_id.lower()
    
    # Get actual size from Hugging Face tree API
    size_gb = _fetch_actual_size_gb(model_id)
    
    if size_gb is None:
        # Fallback to heuristics
        if "i2vgen" in mid or "stable-video" in mid:
            size_gb = 15.0
        elif "cogvideo" in mid or "videoworld" in mid:
            size_gb = 12.0
        elif "ltx-video" in mid or "ltxv" in mid:
            size_gb = 6.0
        elif "animatediff" in mid:
            size_gb = 5.0
        else:
            size_gb = 10.0
            
    if size_gb >= 14.0:
        req = "GPU: VRAM 14GB+"
    elif size_gb >= 10.0:
        req = "GPU: VRAM 12GB+"
    else:
        req = "GPU: VRAM 8GB+"
        
    _, desc = _get_author_and_desc(model_id, "video")
    
    return {"name": name, "id": model_id,
            "desc": desc,
            "size_gb": size_gb, "req": req, "load_class": "Видео",
            "safety": "NSFW" if _is_nsfw(m) else "SFW", "type": "Video"}

def _text_entry(m):
    model_id = m["id"]
    name = model_id.split("/")[-1].replace("-", " ").title()
    mid = model_id.lower()
    
    # Get actual size from Hugging Face tree API
    size_gb = _fetch_actual_size_gb(model_id)
    
    if size_gb is None:
        # Fallback to heuristics (improved with regex parameter matching)
        import re
        match = re.search(r'(\d+(?:\.\d+)?)[b]', mid)
        if match:
            params = float(match.group(1))
            is_quantized = any(q in mid for q in ("fp4", "nvfp4", "int4", "q4", "awq", "gptq", "gguf"))
            is_fp8 = any(q in mid for q in ("fp8", "int8", "q8"))
            if is_quantized:
                size_gb = max(1.0, params * 0.6)
            elif is_fp8:
                size_gb = max(1.0, params * 1.0)
            else:
                size_gb = max(1.5, params * 2.0)
        else:
            size_gb = 14.0
            
    # Classify requirements based on size
    if size_gb >= 35.0:
        req = "GPU: VRAM 24GB+"
    elif size_gb >= 20.0:
        req = "GPU: VRAM 16GB+"
    elif size_gb >= 10.0:
        req = "GPU: VRAM 8GB+"
    else:
        req = "GPU: VRAM 4GB+"
        
    _, desc = _get_author_and_desc(model_id, "text")
    
    return {"name": name, "id": model_id,
            "desc": desc,
            "size_gb": round(size_gb, 1), "req": req, "load_class": "Текст",
            "safety": "NSFW" if _is_nsfw(m) else "SFW", "type": "Text"}

def fetch_top_models():
    formatted_models = {"sfw": [], "nsfw": [], "video": [], "text": []}

    # 1. Image models — paginate until both SFW and NSFW reach PER_LIST (or exhausted)
    print("Fetching image models from Hugging Face (text-to-image)...")
    img_sfw_done = img_nsfw_done = False
    skip = 0
    while not (img_sfw_done and img_nsfw_done):
        page = _fetch_page("text-to-image", skip)
        if not page:
            break
        skip += len(page)
        if len(page) < PAGE:  # last page
            last = True
        else:
            last = False
        seen = _seen_ids(formatted_models)
        for m in page:
            model_id = m.get("id")
            if not model_id or model_id in seen:
                continue
            if "diffusers" not in m.get("tags", []):
                continue
            entry = _image_entry(m)
            if entry["safety"] == "NSFW":
                if len(formatted_models["nsfw"]) < PER_LIST:
                    formatted_models["nsfw"].append(entry)
                    seen.add(model_id)
            else:
                if len(formatted_models["sfw"]) < PER_LIST:
                    formatted_models["sfw"].append(entry)
                    seen.add(model_id)
        img_sfw_done = len(formatted_models["sfw"]) >= PER_LIST
        img_nsfw_done = len(formatted_models["nsfw"]) >= PER_LIST
        if last:
            break
    print(f"  image: SFW={len(formatted_models['sfw'])}, NSFW={len(formatted_models['nsfw'])}")

    # 2. Video models — fill SFW and NSFW buckets independently (NSFW is scarce on HF)
    print("Fetching video models from Hugging Face (text-to-video)...")
    vid_sfw = vid_nsfw = 0
    skip = 0
    while True:
        page = _fetch_page("text-to-video", skip)
        if not page:
            break
        skip += len(page)
        last = len(page) < PAGE
        seen = _seen_ids(formatted_models)
        for m in page:
            model_id = m.get("id")
            if not model_id or model_id in seen:
                continue
            entry = _video_entry(m)
            if entry["safety"] == "NSFW":
                if vid_nsfw < PER_LIST:
                    formatted_models["video"].append(entry)
                    seen.add(model_id)
                    vid_nsfw += 1
            else:
                if vid_sfw < PER_LIST:
                    formatted_models["video"].append(entry)
                    seen.add(model_id)
                    vid_sfw += 1
        if (vid_sfw >= PER_LIST and vid_nsfw >= PER_LIST) or last:
            break
    print(f"  video: SFW={vid_sfw}, NSFW={vid_nsfw}")

    # 3. Text models — fill SFW and NSFW buckets independently
    print("Fetching text models from Hugging Face (text-generation)...")
    txt_sfw = txt_nsfw = 0
    skip = 0
    while True:
        page = _fetch_page("text-generation", skip)
        if not page or not isinstance(page, list):
            break
        skip += len(page)
        last = len(page) < PAGE
        seen = _seen_ids(formatted_models)
        for m in page:
            model_id = m.get("id")
            if not model_id or model_id in seen:
                continue
            entry = _text_entry(m)
            if entry["safety"] == "NSFW":
                if txt_nsfw < PER_LIST:
                    formatted_models["text"].append(entry)
                    seen.add(model_id)
                    txt_nsfw += 1
            else:
                if txt_sfw < PER_LIST:
                    formatted_models["text"].append(entry)
                    seen.add(model_id)
                    txt_sfw += 1
        if (txt_sfw >= PER_LIST and txt_nsfw >= PER_LIST) or last:
            break
    print(f"  text: SFW={txt_sfw}, NSFW={txt_nsfw}")

    print(f"Done. photo: sfw={len(formatted_models['sfw'])} nsfw={len(formatted_models['nsfw'])} "
          f"| video={len(formatted_models['video'])} | text={len(formatted_models['text'])}")
    return formatted_models

if __name__ == "__main__":
    app_data = get_app_data_dir()
    os.makedirs(app_data, exist_ok=True)
    models_file = os.path.join(app_data, "models.json")
    models_dict = fetch_top_models()
    with open(models_file, "w", encoding="utf-8") as f:
        json.dump(models_dict, f, ensure_ascii=False, indent=4)
    print(f"Saved models to {models_file}")
