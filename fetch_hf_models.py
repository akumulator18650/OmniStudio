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

def _image_entry(m):
    tags = m.get("tags", [])
    model_id = m["id"]
    name = model_id.split("/")[-1].replace("-", " ").title()
    if "stable-diffusion-xl" in tags or "sdxl" in model_id.lower() or "xl" in model_id.lower():
        model_class, req, size_gb = "Next-Gen", "GPU: VRAM 8GB+", 6.5
        desc = f"Тяжелая SDXL модель от {model_id.split('/')[0]}."
    elif "flux" in model_id.lower():
        model_class, req, size_gb = "Next-Gen", "GPU: VRAM 12GB+", 12.0
        desc = f"Сверхтяжелая Flux модель от {model_id.split('/')[0]}."
    else:
        model_class, req, size_gb = "Стандарт", "GPU: VRAM 6GB+", 4.0
        desc = f"Обычная SD 1.5/2.1 модель от {model_id.split('/')[0]}."
    return {"name": name, "id": model_id, "desc": desc, "size_gb": size_gb,
            "req": req, "load_class": model_class,
            "safety": "NSFW" if _is_nsfw(m) else "SFW", "type": "Photo"}

def _video_entry(m):
    model_id = m["id"]
    name = model_id.split("/")[-1].replace("-", " ").title()
    mid = model_id.lower()
    if "i2vgen" in mid or "stable-video" in mid:
        req, size_gb = "GPU: VRAM 14GB+", 15.0
    elif "cogvideo" in mid or "videoworld" in mid:
        req, size_gb = "GPU: VRAM 12GB+", 12.0
    elif "ltx-video" in mid or "ltxv" in mid:
        req, size_gb = "GPU: VRAM 8GB+", 6.0
    elif "animatediff" in mid:
        req, size_gb = "GPU: VRAM 8GB+", 5.0
    else:
        req, size_gb = "GPU: VRAM 12GB+", 10.0
    return {"name": name, "id": model_id,
            "desc": f"Видео-модель от {model_id.split('/')[0]}.",
            "size_gb": size_gb, "req": req, "load_class": "Видео",
            "safety": "NSFW" if _is_nsfw(m) else "SFW", "type": "Video"}

def _text_entry(m):
    model_id = m["id"]
    name = model_id.split("/")[-1].replace("-", " ").title()
    mid = model_id.lower()
    if "70b" in mid or "72b" in mid:
        req, size_gb = "GPU: VRAM 24GB+", 60.0
    elif "32b" in mid or "34b" in mid or "qwq" in mid:
        req, size_gb = "GPU: VRAM 24GB+", 40.0
    elif "14b" in mid or "13b" in mid:
        req, size_gb = "GPU: VRAM 16GB+", 26.0
    elif "7b" in mid or "8b" in mid:
        req, size_gb = "GPU: VRAM 8GB+", 15.0
    elif "1b" in mid or "1.5b" in mid or "3b" in mid or "mini" in mid:
        req, size_gb = "GPU: VRAM 4GB+", 4.0
    else:
        req, size_gb = "GPU: VRAM 8GB+", 14.0
    return {"name": name, "id": model_id,
            "desc": f"Текстовая нейросеть (LLM) от {model_id.split('/')[0]}.",
            "size_gb": size_gb, "req": req, "load_class": "Текст",
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
