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
METADATA_FILE = "metadata.json"


def start_ngrok():
    """Inicia ngrok e retorna a URL pública"""
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
    """Seleciona aleatoriamente um item do metadata.json"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        if metadata:
            key = random.choice(list(metadata.keys()))
            return metadata[key]
    return {}


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

    files = sorted([f for f in os.listdir(PENDING_DIR) if f.endswith(".mp4")])
    print("📂 Arquivos encontrados:", files)

    if not files:
        print("⚠️ Nenhum vídeo para postar.")
        exit(0)

    video_file = files[0]
    video_path = os.path.join(PENDING_DIR, video_file)

    if not os.path.isfile(video_path):
        print(f"❌ Arquivo não encontrado: {video_path}")
        exit(1)

    meta = get_metadata()
    caption = meta.get("description", "🚀 Postagem automática via API")

    print(f"➡️ Preparando vídeo: {video_file} | Legenda: {caption}")

    # Servidor HTTP local
    subprocess.Popen(["python3", "-m", "http.server", "8000", "--directory", PENDING_DIR])
    base_url = start_ngrok()
    video_url = f"{base_url}/{video_file}"
    print(f"🌍 URL pública: {video_url}")

    upload_resp = upload_reels(video_url, caption)
    print("Upload response:", upload_resp)

    if "id" in upload_resp:
        container_id = upload_resp["id"]
        print("⏳ Aguardando processamento...")
        time.sleep(30)

        publish_resp = publish_reels(container_id)
        print("Publish response:", publish_resp)

        if "id" in publish_resp:
            print(f"✅ Vídeo {video_file} postado com sucesso no Instagram.")

            # ========================================
            # 📦 Mover vídeo postado para /videos/posted
            # ========================================
            os.makedirs(POSTED_DIR, exist_ok=True)
            source = os.path.join(PENDING_DIR, video_file)
            dest = os.path.join(POSTED_DIR, video_file)

            try:
                shutil.move(source, dest)
                print(f"📁 Vídeo movido para {dest}")
            except Exception as e:
                print(f"⚠️ Não foi possível mover o vídeo: {e}")

        else:
            print("❌ Erro ao publicar:", publish_resp)
    else:
        print("❌ Erro no upload:", upload_resp)
