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
