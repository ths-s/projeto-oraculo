import os
import requests
import time
import json
import random

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

VIDEO_URL = os.getenv("VIDEO_URL")  # URL FINAL DO VÍDEO (GitHub)

DATA_DIR = "data"
METADATA_FILE = "metadata.json"
GANCHO_FILE = "gancho_data.json"
STATE_FILE = os.path.join(DATA_DIR, "state.json")

# ---------------- UTILS ---------------- #

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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
            raise RuntimeError(
                f"❌ Instagram falhou ao processar o vídeo.\n"
                f"Detalhes: {json.dumps(res, indent=2)}"
            )

        time.sleep(10)

    raise RuntimeError("❌ Timeout no processamento do vídeo.")

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

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    if not VIDEO_URL:
        raise RuntimeError("❌ VIDEO_URL não definido.")

    state = load_json(STATE_FILE)
    ganchos = load_json(GANCHO_FILE)

    gancho_id = state.get("proximo_gancho") or random.choice(list(ganchos.keys()))
    gancho = ganchos.get(gancho_id, {})

    caption = (
        f"{gancho.get('title', '📢 Novo vídeo!')}\n"
        f"{gancho.get('text', gancho.get('description', ''))}\n"
        "🚀 Postagem automática via API"
    ).strip()

    print("🪝 Gancho:", gancho_id)
    print("💬 Legenda:\n", caption)

    print("🌍 URL do vídeo:", VIDEO_URL)

    upload_resp = upload_reels(VIDEO_URL, caption)
    print("📤 Upload response:", upload_resp)

    if "id" not in upload_resp:
        raise RuntimeError(f"❌ Erro no upload: {upload_resp}")

    container_id = upload_resp["id"]

    wait_for_processing(container_id)

    publish_resp = publish_reels(container_id)
    print("📣 Publish response:", publish_resp)

    if "id" not in publish_resp:
        raise RuntimeError(f"❌ Erro ao publicar: {publish_resp}")

    print("✅ Vídeo publicado com sucesso no Instagram!")

    state["ultimo_gancho_postado"] = gancho_id
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
