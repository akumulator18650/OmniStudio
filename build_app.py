import os
import subprocess
import sys


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE = os.path.join(PROJECT_DIR, "OmniStudio.spec")


def main() -> None:
    print("Installing PyInstaller if needed...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    print("Building OmniStudio...")
    subprocess.check_call(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--onedir",
            "--windowed",
            "--name=OmniStudio",
            "--icon=assets/icons/app_icon.ico",
            "--runtime-hook", "pyi_rth_pyqt6_dll.py",
            "--copy-metadata", "requests",
            "--copy-metadata", "transformers",
            "--copy-metadata", "diffusers",
            "--copy-metadata", "huggingface-hub",
            "--copy-metadata", "torch",
            "--copy-metadata", "numpy",
            "--copy-metadata", "filelock",
            "--copy-metadata", "tqdm",
            "--copy-metadata", "regex",
            "--copy-metadata", "packaging",
            "--copy-metadata", "tokenizers",
            "--copy-metadata", "accelerate",
            "--copy-metadata", "bitsandbytes",
            "--copy-metadata", "scipy",
            "--copy-metadata", "imageio-ffmpeg",
            "--copy-metadata", "rembg",
            "--copy-metadata", "onnxruntime-gpu",
            "--hidden-import", "cv2",
            "--hidden-import", "imageio_ffmpeg",
            "--hidden-import", "unicodedata",
            "--hidden-import", "rembg",
            "--hidden-import", "onnxruntime",
            "--collect-binaries", "imageio_ffmpeg",
            "--add-data", f"assets{os.pathsep}assets",
            "--add-data", f"style.qss{os.pathsep}.",
            "--add-data", f"web{os.pathsep}web",
            "main_pyqt.py"
        ],
        cwd=PROJECT_DIR,
    )

    exe_path = os.path.join(PROJECT_DIR, "dist", "OmniStudio", "OmniStudio.exe")
    print("Build completed successfully.")
    print(f"Ready application: {exe_path}")


if __name__ == "__main__":
    main()
