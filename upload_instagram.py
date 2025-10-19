import os
import requests
import time
import subprocess
import json
import random
import shutil

# =======================
# 🔧 Configurações
# =======================
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")
PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
DATA_DIR = "data"

# =======================
# 📁 Arquivos
# =======================
METADATA_FILE = "metadata.json"
GANCHO_FILE = "gancho_data.json"
STATE_FILE = os.path.join(DATA_DIR, "state.json")


# =======================
# ⚙️ Funções utilitárias
# =======================
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    metadata = load_json(METADATA_FILE)
    if metadata:
        key = random.choice(list(metadata.keys()))
        return metadata[key]
    return {}


def upload_to_instagram(video_path, caption, access_token, ig_user_id, ngrok_url):
    print(f"➡️ Preparando vídeo: {os.path.basename(video_path)} | Legenda: {caption}")

    # 1️⃣ Upload do vídeo
    upload_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    payload = {
        "video_url": ngrok_url,
        "caption": caption,
        "access_token": access_token
    }
    upload_res = requests.post(upload_url, data=payload).json()
    print("Upload response:", upload_res)

    if "id" not in upload_res:
        print("❌ Falha no upload:", upload_res)
        return False

    creation_id = upload_res["id"]

    # 2️⃣ Esperar até o processamento do vídeo terminar
    print("⏳ Aguardando processamento...")
    for i in range(20):  # tenta por até 100 segundos
        status_url = f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={access_token}"
        status_res = requests.get(status_url).json()
        status = status_res.get("status_code")
        print(f"🔄 Status [{i+1}/20]: {status}")
        if status == "FINISHED":
            print("✅ Vídeo processado e pronto para publicar!")
            break
        elif status == "ERROR":
            print("❌ Erro no processamento:", status_res)
            return False
        time.sleep(5)
    else:
        print("⚠️ Tempo limite atingido. O vídeo pode não ter sido processado a tempo.")
        return False

    # 3️⃣ Publicar o vídeo
    publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
    publish_payload = {"creation_id": creation_id, "access_token": access_token}
    publish_res = requests.post(publish_url, data=publish_payload).json()
    print("Publish response:", publish_res)

    if "id" in publish_res:
        print(f"✅ Vídeo {os.path.basename(video_path)} postado com sucesso no Instagram.")
        return True
    else:
        print(f"❌ Erro ao publicar:", publish_res)
        return False


# =======================
# 🚀 Execução principal
# =======================
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

    # =======================
    # 📊 Dados de análise
    # =======================
    state = load_json(STATE_FILE)
    ganchos = load_json(GANCHO_FILE)
    meta = get_metadata()

    proximo_gancho_id = state.get("proximo_gancho")
    gancho_info = ganchos.get(proximo_gancho_id, {})

    gancho_titulo = gancho_info.get("title", "")
    gancho_texto = gancho_info.get("text", gancho_info.get("description", ""))

    caption_base = meta.get("description", "🚀 Postagem automática via API")
    caption = f"{gancho_titulo}\n\n{gancho_texto}\n\n{caption_base}".strip()

    print("🎯 Gancho recomendado:", proximo_gancho_id or "(nenhum)")
    print("🪝 Título:", gancho_titulo)
    print("💬 Legenda final:\n", caption)

    # =======================
    # 🌍 Publicação
    # =======================
    subprocess.Popen(["python3", "-m", "http.server", "8000", "--directory", PENDING_DIR])
    base_url = start_ngrok()
    video_url = f"{base_url}/{video_file}"
    print(f"🌍 URL pública: {video_url}")

    # 🚀 Faz o upload e publicação com espera
    sucesso = upload_to_instagram(video_path, caption, ACCESS_TOKEN, IG_USER_ID, video_url)

    if sucesso:
        # =======================
        # 📦 Mover vídeo postado
        # =======================
        os.makedirs(POSTED_DIR, exist_ok=True)
        source = os.path.join(PENDING_DIR, video_file)
        dest = os.path.join(POSTED_DIR, video_file)

        try:
            shutil.move(source, dest)
            print(f"📁 Vídeo movido para {dest}")
        except Exception as e:
            print(f"⚠️ Não foi possível mover o vídeo: {e}")

        # Atualiza o histórico no state.json
        state["ultimo_gancho_postado"] = proximo_gancho_id
        state["ultimo_video_postado"] = video_file
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
