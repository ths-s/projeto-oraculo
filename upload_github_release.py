import os
import requests
import subprocess
import json
from pathlib import Path
import re


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")  # user/repo

VIDEO_PATH = os.getenv("VIDEO_PATH")
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


def safe_name(path):
    name = Path(path).stem
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return f"{name}.mp4"


def upload_asset(upload_url, file_path):
    name = Path(file_path).name
    url = upload_url.split("{")[0] + f"?name={name}"

    with open(file_path, "rb") as f:
        r = requests.post(
            url,
            headers={
                **HEADERS,
                "Content-Type": "video/mp4"
            },
            data=f
        )
    r.raise_for_status()
    return r.json()["browser_download_url"]


if __name__ == "__main__":
    release = get_or_create_release()
    video_url = upload_asset(release["upload_url"], VIDEO_PATH)

    print("🌍 VIDEO_PUBLIC_URL=", video_url)
