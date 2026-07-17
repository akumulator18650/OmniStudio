import os

models_dir = os.path.join(os.path.expanduser("~"), "OmniStudioData", "models")
os.environ["HF_HOME"] = models_dir
os.environ["HF_HUB_CACHE"] = models_dir
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from huggingface_hub import snapshot_download
models_to_download = [
    "SG161222/RealVisXL_V4.0_Lightning",
    "John6666/biglustydonutmix-nsfw-realism-v12-sdxl"
]

print(f"Downloading models to {models_dir}...")
for model_id in models_to_download:
    print(f"Downloading {model_id}...")
    try:
        # Ignore unnecessary files to save space and time (e.g., fp32 safetensors if fp16 is available, ONNX models, etc.)
        snapshot_download(
            repo_id=model_id,
            cache_dir=models_dir,
            allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model"],
            ignore_patterns=["*openvino*", "*onnx*", "*fp32*", "*non_ema*"],
            max_workers=4
        )
        print(f"Successfully downloaded {model_id}")
    except Exception as e:
        print(f"Failed to download {model_id}: {e}")

print("All downloads completed.")
