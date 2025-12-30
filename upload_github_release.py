import os
import requests
import subprocess
import json
from pathlib import Path
import re
import uuid

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")  # user/repo

VIDEO_PATH = os.getenv("VIDEO_PATH")

original_name = os.path.basename(VIDEO_PATH)

safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", original_name)
safe_name = f"{uuid.uuid4()}_{safe_name}"

RELEASE_TAG = "videos-auto"
RELEASE_NAME = "Vídeos Automáticos"

if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, VIDEO_PATH]):
    raise RuntimeError("❌ Variáveis obrigatórias ausentes.")

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def get_or_create_release():
    url = f"{API}/repos/{GITHUB_REPOSITORY}/releases/tags/{RELEASE_TAG}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code == 200:
        return r.json()

    r = requests.post(
        f"{API}/repos/{GITHUB_REPOSITORY}/releases",
        headers=HEADERS,
        json={
            "tag_name": RELEASE_TAG,
            "name": RELEASE_NAME,
            "draft": False,
            "prerelease": False
        }
    )
    r.raise_for_status()
    return r.json()


def upload_asset(upload_url, file_path, asset_name):
    params = {"name": asset_name}
    url = upload_url.split("{")[0] + f"?name={asset_name}"

    with open(file_path, "rb") as f:
        r = requests.post(
            url,
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Content-Type": "video/mp4",
            },
            data=f
        )
    r.raise_for_status()
    return r.json()["browser_download_url"]


if __name__ == "__main__":
    release = get_or_create_release()
    video_url = upload_asset(release["upload_url"], VIDEO_PATH, safe_name)

    print("🌍 VIDEO_PUBLIC_URL=", video_url)
