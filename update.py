import os
import sys
import json
import shutil
import tempfile
import urllib.request
import zipfile
import subprocess

def main():
    if len(sys.argv) < 2:
        print("No release URL supplied.")
        return

    release_url = sys.argv[1]
    base = os.path.dirname(os.path.abspath(__file__))
    temp_zip = os.path.join(tempfile.gettempdir(), "Ultimate2Mapper_update.zip")
    backup = os.path.join(tempfile.gettempdir(), "Ultimate2Mapper_backup")

    try:
        req = urllib.request.Request(release_url, headers={"User-Agent": "Ultimate2Mapper"})
        with urllib.request.urlopen(req, timeout=30) as r, open(temp_zip, "wb") as f:
            shutil.copyfileobj(r, f)

        if os.path.exists(backup):
            shutil.rmtree(backup)
        os.makedirs(backup)

        # Back up program files, but preserve user config outside the app folder.
        for name in os.listdir(base):
            if name in {"__pycache__"}:
                continue
            src = os.path.join(base, name)
            dst = os.path.join(backup, name)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst)

        with zipfile.ZipFile(temp_zip, "r") as z:
            z.extractall(base)

        print("Update installed.")
    except Exception as e:
        print("Update failed:", e)
        # Restore backup if possible.
        if os.path.isdir(backup):
            for name in os.listdir(backup):
                src = os.path.join(backup, name)
                dst = os.path.join(base, name)
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        return

    app = os.path.join(base, "ultimate2_mapper.py")
    subprocess.Popen([sys.executable, app], cwd=base)

if __name__ == "__main__":
    main()
