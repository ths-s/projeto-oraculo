import os
import requests
import time
import json

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
VIDEO_URL = os.getenv("VIDEO_URL")

def wait_for_processing(container_id):
    for i in range(30):
        res = requests.get(
            f"https://graph.facebook.com/v20.0/{container_id}",
            params={
                "fields": "status_code",
                "access_token": ACCESS_TOKEN,
            },
        ).json()

        print(f"🔄 Tentativa {i+1}/30 →", res)

        if res.get("status_code") == "FINISHED":
            return

        if res.get("status_code") == "ERROR":
            raise RuntimeError(json.dumps(res, indent=2))

        time.sleep(10)

    raise RuntimeError("❌ Timeout no processamento")

if __name__ == "__main__":
    print("🌍 VIDEO_URL recebida:", VIDEO_URL)

    upload = requests.post(
        f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": VIDEO_URL,
            "access_token": ACCESS_TOKEN,
        },
    ).json()

    print("📤 Upload response:", upload)

    if "id" not in upload:
        raise RuntimeError(upload)

    wait_for_processing(upload["id"])

    publish = requests.post(
        f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish",
        data={
            "creation_id": upload["id"],
            "access_token": ACCESS_TOKEN,
        },
    ).json()

    print("📣 Publish response:", publish)
