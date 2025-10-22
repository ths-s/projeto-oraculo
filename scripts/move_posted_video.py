import os
import json
import shutil

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
STATE_PATH = "data/state.json"

def load_state():
    """Carrega o arquivo de estado JSON."""
    if not os.path.exists(STATE_PATH):
        print("⚠️ Arquivo state.json não encontrado.")
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Erro ao ler state.json (JSON inválido).")
        return {}

def move_posted_video():
    """Move o último vídeo postado do pending para posted."""
    state = load_state()
    video_name = state.get("ultimo_video_postado")

    if not video_name:
        print("⚠️ Nenhum vídeo registrado como postado.")
        return

    src = os.path.join(PENDING_DIR, video_name)
    dst = os.path.join(POSTED_DIR, video_name)

    if not os.path.exists(src):
        print(f"⚠️ Arquivo não encontrado: {src}")
        return

    os.makedirs(POSTED_DIR, exist_ok=True)

    try:
        shutil.move(src, dst)
        print(f"✅ Vídeo movido com sucesso: {video_name}")
        print(f"📁 Novo local: {dst}")
    except Exception as e:
        print(f"❌ Erro ao mover vídeo: {e}")

if __name__ == "__main__":
    move_posted_video()
