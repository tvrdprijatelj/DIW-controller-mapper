import os
import sys
import json
import urllib.request
import subprocess
import tempfile
import zipfile

APP_VERSION = "1.0.0"
MANIFEST_URL = "https://raw.githubusercontent.com/tvrdprijatelj/Ultimate2Mapper/main/version.json"

def get_latest():
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "Ultimate2Mapper"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))

def version_tuple(v):
    return tuple(int(x) for x in v.lstrip("v").split("."))

def start_app():
    app = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ultimate2_mapper.py")
    subprocess.Popen([sys.executable, app], cwd=os.path.dirname(app))

def main():
    try:
        latest = get_latest()
        latest_version = latest.get("version", APP_VERSION)
        if version_tuple(latest_version) > version_tuple(APP_VERSION):
            print(f"New version available: {latest_version}")
            # A release ZIP URL can be added to version.json later.
            # The launcher intentionally does not overwrite files automatically
            # unless a valid release_url is present.
            release_url = latest.get("release_url")
            if release_url:
                updater = os.path.join(os.path.dirname(os.path.abspath(__file__)), "update.py")
                subprocess.Popen([sys.executable, updater, release_url, latest_version])
                return
    except Exception as e:
        print("Update check skipped:", e)

    start_app()

if __name__ == "__main__":
    main()
