import os
import requests
import time

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
VIDEO_URL = os.getenv("VIDEO_URL")

if not VIDEO_URL:
    raise RuntimeError("❌ VIDEO_URL não definida")

def wait_for_processing(container_id):
    for i in range(30):
        res = requests.get(
            f"https://graph.facebook.com/v20.0/{container_id}",
            params={
                "fields": "status_code",
                "access_token": ACCESS_TOKEN
            }
        ).json()

        status = res.get("status_code")
        print(f"🔄 Tentativa {i+1}/30 → {status}")

        if status == "FINISHED":
            return True
        if status == "ERROR":
            print("❌ Erro no processamento:", res)
            return False

        time.sleep(10)

    return False


def main():
    upload = requests.post(
        f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": VIDEO_URL,
            "caption": "🚀 Postagem automática via API",
            "access_token": ACCESS_TOKEN
        }
    ).json()

    print("📤 Upload response:", upload)

    if "id" not in upload:
        raise RuntimeError(upload)

    container_id = upload["id"]

    if not wait_for_processing(container_id):
        print("⚠️ Vídeo ignorado.")
        return

    publish = requests.post(
        f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN
        }
    ).json()

    print("📣 Publish response:", publish)

    if "id" not in publish:
        raise RuntimeError(publish)

    print("✅ Vídeo publicado com sucesso!")


if __name__ == "__main__":
    main()
