# build.py
import os
import shutil
import subprocess

def clean():
    for path in ["build", "dist", "run_tray.spec"]:
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)

def build():
    subprocess.run([
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "JarvisTray",
        "--manifest", "JarvisTray.exe.manifest",
        "--paths", "src",
        "run_tray.py"
    ], check=True)


if __name__ == "__main__":
    clean()
    build()
