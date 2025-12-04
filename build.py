# build.py
import os
import shutil
import subprocess

def clean():
    for path in ["build", "dist"]:
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)

def build():
    subprocess.run([
        "pyinstaller",
        "--noconfirm",
        "JarvisTray.spec"
    ], check=True)


if __name__ == "__main__":
    clean()
    build()
