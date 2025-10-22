import os
import requests
import time
import subprocess
import json
import random
import shutil

ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

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


def start_ngrok():
    ngrok = subprocess.Popen(["ngrok", "http", "8000"], stdout=subprocess.PIPE)
    time.sleep(5)
    try:
        url = requests.get("http://127.0.0.1:4040/api/tunnels").json()["tunnels"][0]["public_url"]
        return url
    except Exception as e:
        print(f"❌ Erro ao iniciar ngrok: {e}")
        ngrok.terminate()
        exit(1)


def get_metadata():
    metadata = load_json(METADATA_FILE)
    if metadata:
        key = random.choice(list(metadata.keys()))
        return metadata[key]
    return {}


def wait_for_processing(container_id):
    print("⏳ Aguardando processamento...")
    for attempt in range(20):
        status_url = f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code&access_token={ACCESS_TOKEN}"
        res = requests.get(status_url).json()
        status = res.get("status_code")

        print(f"🔄 Tentativa {attempt+1}/20 → Status: {status}")

        if status == "FINISHED":
            print("✅ Vídeo processado com sucesso!")
            return True
        elif status == "ERROR":
            print("❌ Erro no processamento:", res)
            return False
        time.sleep(5)
    print("⚠️ Tempo limite atingido. O vídeo pode não estar pronto ainda.")
    return False


def upload_reels(video_url, caption):
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    data = {
        "caption": caption,
        "media_type": "REELS",
        "video_url": video_url,
        "access_token": ACCESS_TOKEN,
    }
    return requests.post(url, data=data).json()


def publish_reels(container_id):
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
    data = {"creation_id": container_id, "access_token": ACCESS_TOKEN}
    return requests.post(url, data=data).json()


if __name__ == "__main__":
    if not os.path.exists(PENDING_DIR):
        print(f"⚠️ Pasta {PENDING_DIR} não existe.")
        exit(0)

    metadata = load_json(METADATA_FILE)
    # 🚫 Ignora vídeos que já estão no metadata (postados no YouTube)
    all_files = sorted([f for f in os.listdir(PENDING_DIR) if f.endswith(".mp4")])
    files = [f for f in all_files if f not in metadata]

    print("📂 Arquivos disponíveis para Instagram:", files)

    if not files:
        print("⚠️ Nenhum vídeo novo para postar no Instagram.")
        exit(0)

    video_file = files[0]
    video_path = os.path.join(PENDING_DIR, video_file)

    state = load_json(STATE_FILE)
    ganchos = load_json(GANCHO_FILE)
    meta = get_metadata()

    proximo_gancho_id = state.get("proximo_gancho")
    gancho_info = ganchos.get(proximo_gancho_id, {})

    gancho_titulo = gancho_info.get("title", "📢 Novo vídeo!")
    gancho_texto = gancho_info.get("text", gancho_info.get("description", ""))
    caption_base = meta.get("description", "🚀 Postagem automática via API")
    caption = f"{gancho_titulo}\n{gancho_texto}\n{caption_base}".strip()

    print("🎯 Gancho recomendado:", proximo_gancho_id or "(nenhum)")
    print("🪝 Título:", gancho_titulo)
    print("💬 Legenda final:\n", caption)

    subprocess.Popen(["python3", "-m", "http.server", "8000", "--directory", PENDING_DIR])
    base_url = start_ngrok()
    video_url = f"{base_url}/{video_file}"
    print(f"🌍 URL pública: {video_url}")

    upload_resp = upload_reels(video_url, caption)
    print("Upload response:", upload_resp)

    if "id" in upload_resp:
        container_id = upload_resp["id"]
        if wait_for_processing(container_id):
            publish_resp = publish_reels(container_id)
            print("Publish response:", publish_resp)

            if "id" in publish_resp:
                print(f"✅ Vídeo {video_file} postado com sucesso no Instagram.")
                os.makedirs(POSTED_DIR, exist_ok=True)
                try:
                    shutil.move(video_path, os.path.join(POSTED_DIR, video_file))
                    print(f"📁 Vídeo movido para {POSTED_DIR}/{video_file}")
                except Exception as e:
                    print(f"⚠️ Não foi possível mover o vídeo: {e}")

                state["ultimo_gancho_postado"] = proximo_gancho_id
                state["ultimo_video_postado"] = video_file
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            else:
                print("❌ Erro ao publicar:", publish_resp)
        else:
            print("⚠️ O vídeo não ficou pronto para publicação a tempo.")
    else:
        print("❌ Erro no upload:", upload_resp)
