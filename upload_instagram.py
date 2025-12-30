import os
import requests
import time
import json
import random
import shutil

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

# ID do arquivo no Drive (vem do main.py ou metadata)
DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID")

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
DATA_DIR = "data"

METADATA_FILE = "metadata.json"
GANCHO_FILE = "gancho_data.json"
STATE_FILE = os.path.join(DATA_DIR, "state.json")


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_drive_download_url(file_id):
    # Link direto HTTPS (funciona para Instagram)
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def wait_for_processing(container_id):
    print("⏳ Aguardando processamento...")
    for attempt in range(30):
        status_url = (
            f"https://graph.facebook.com/v20.0/{container_id}"
            f"?fields=status_code&access_token={ACCESS_TOKEN}"
        )
        res = requests.get(status_url).json()
        status = res.get("status_code")

        print(f"🔄 Tentativa {attempt + 1}/30 → Status: {status}")

        if status == "FINISHED":
            print("✅ Vídeo processado com sucesso!")
            return True
        if status == "ERROR":
            print("❌ Erro no processamento:", res)
            return False

        time.sleep(10)

    print("⚠️ Tempo limite atingido.")
    return False


def upload_reels(video_url, caption):
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    data = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN,
    }
    return requests.post(url, data=data).json()


def publish_reels(container_id):
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    data = {
        "creation_id": container_id,
        "access_token": ACCESS_TOKEN,
    }
    return requests.post(url, data=data).json()


if __name__ == "__main__":
    if not DRIVE_FILE_ID:
        raise RuntimeError("❌ DRIVE_FILE_ID não definido.")

    state = load_json(STATE_FILE)
    ganchos = load_json(GANCHO_FILE)
    metadata = load_json(METADATA_FILE)

    gancho_id = state.get("proximo_gancho") or random.choice(list(ganchos.keys()))
    gancho = ganchos.get(gancho_id, {})

    gancho_titulo = gancho.get("title", "📢 Novo vídeo!")
    gancho_texto = gancho.get("text", gancho.get("description", ""))
    caption_base = "🚀 Postagem automática via API"

    caption = f"{gancho_titulo}\n{gancho_texto}\n{caption_base}".strip()

    print("🪝 Gancho:", gancho_id)
    print("💬 Legenda:\n", caption)

    video_url = build_drive_download_url(DRIVE_FILE_ID)
    print("🌍 URL pública do Drive:", video_url)

    upload_resp = upload_reels(video_url, caption)
    print("📤 Upload response:", upload_resp)

    if "id" not in upload_resp:
        raise RuntimeError(f"❌ Erro no upload: {upload_resp}")

    container_id = upload_resp["id"]

    if not wait_for_processing(container_id):
        raise RuntimeError("❌ Vídeo não ficou pronto a tempo.")

    publish_resp = publish_reels(container_id)
    print("📣 Publish response:", publish_resp)

    if "id" not in publish_resp:
        raise RuntimeError(f"❌ Erro ao publicar: {publish_resp}")

    print("✅ Vídeo publicado com sucesso no Instagram!")

    state["ultimo_gancho_postado"] = gancho_id
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
