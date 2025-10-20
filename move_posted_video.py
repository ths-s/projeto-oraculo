import os
import shutil
import json
import re

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
STATE_PATH = "data/state.json"

def load_state():
    if not os.path.exists(STATE_PATH):
        return {"posted_videos": []}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"posted_videos": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

def extract_number(filename):
    """Extrai o primeiro número encontrado no nome do arquivo."""
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else float('inf')

def move_first_unposted_video():
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)

    state = load_state()
    posted = set(state.get("posted_videos", []))

    # Lista vídeos válidos ainda não movidos
    pending = [
        f for f in os.listdir(PENDING_DIR)
        if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))
        and f not in posted
    ]

    # Ordena numericamente (por número no nome)
    pending = sorted(pending, key=extract_number)

    if not pending:
        print("⚠️ Nenhum novo vídeo para mover (todos já postados).")
        return

    video = pending[0]
    src = os.path.join(PENDING_DIR, video)
    dst = os.path.join(POSTED_DIR, video)

    shutil.move(src, dst)

    # Atualiza histórico e salva
    posted.add(video)
    state["posted_videos"] = sorted(list(posted))
    save_state(state)

    print(f"✅ Vídeo movido com sucesso: {video}")

if __name__ == "__main__":
    move_first_unposted_video()
