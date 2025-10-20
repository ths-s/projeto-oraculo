import os
import json
import shutil

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
DATA_DIR = "data"

METADATA_FILE = "metadata.json"
STATE_FILE = os.path.join(DATA_DIR, "state.json")

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def move_video_in_same_order():
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    metadata = load_json(METADATA_FILE)
    all_files = sorted([f for f in os.listdir(PENDING_DIR) if f.endswith(".mp4")])
    files = [f for f in all_files if f not in metadata]

    if not files:
        print("⚠️ Nenhum vídeo novo encontrado para mover.")
        return

    # mesmo vídeo que o upload_instagram usaria
    video_file = files[0]
    src = os.path.join(PENDING_DIR, video_file)
    dst = os.path.join(POSTED_DIR, video_file)

    try:
        shutil.move(src, dst)
        print(f"✅ Vídeo movido com sucesso: {video_file}")

        # Atualiza o state.json com o último movido
        state = load_json(STATE_FILE)
        state["ultimo_video_movido"] = video_file
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Erro ao mover vídeo '{video_file}': {e}")

if __name__ == "__main__":
    move_video_in_same_order()
