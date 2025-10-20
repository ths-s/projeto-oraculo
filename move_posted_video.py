import os
import shutil
import json

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
STATE_PATH = "data/state.json"
METADATA_PATH = "metadata.json"

def load_json(path, default=None):
    """Carrega JSON com fallback seguro."""
    if not os.path.exists(path):
        return default or {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default or {}

def save_json(path, data):
    """Salva JSON formatado."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def move_unlisted_videos():
    """Move todos os vídeos que NÃO estão listados em metadata.json."""
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)

    # Carrega metadados e estado
    metadata = load_json(METADATA_PATH, {})
    state = load_json(STATE_PATH, {"moved_videos": []})

    # Obtém nomes de vídeos já em metadata.json
    listed_videos = set()
    if "videos" in metadata and isinstance(metadata["videos"], list):
        for item in metadata["videos"]:
            if isinstance(item, dict) and "filename" in item:
                listed_videos.add(item["filename"])
            elif isinstance(item, str):
                listed_videos.add(item)

    moved = set(state.get("moved_videos", []))

    # Lista todos os vídeos pendentes
    pending_videos = sorted([
        f for f in os.listdir(PENDING_DIR)
        if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))
        and f not in listed_videos
        and f not in moved
    ])

    if not pending_videos:
        print("⚠️ Nenhum vídeo para mover (todos estão no metadata.json ou já foram movidos).")
        return

    for video in pending_videos:
        src = os.path.join(PENDING_DIR, video)
        dst = os.path.join(POSTED_DIR, video)
        try:
            shutil.move(src, dst)
            moved.add(video)
            print(f"✅ Vídeo movido: {video}")
        except Exception as e:
            print(f"❌ Erro ao mover '{video}': {e}")

    # Atualiza o estado
    state["moved_videos"] = sorted(list(moved))
    save_json(STATE_PATH, state)

if __name__ == "__main__":
    move_unlisted_videos()
