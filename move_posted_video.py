import os
import shutil
import json

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
STATE_PATH = "data/state.json"

def load_state():
    """Carrega o arquivo de estado (vídeos já movidos)."""
    if not os.path.exists(STATE_PATH):
        return {"posted_videos": []}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"posted_videos": []}

def save_state(state):
    """Salva o estado atualizado."""
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

def move_next_video():
    """Move o primeiro vídeo (ordem alfabética) ainda não postado."""
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)

    state = load_state()
    posted = set(state.get("posted_videos", []))

    # Lista e ordena os vídeos por nome (ordem alfabética)
    pending_videos = sorted([
        f for f in os.listdir(PENDING_DIR)
        if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))
        and f not in posted
    ])

    if not pending_videos:
        print("⚠️ Nenhum novo vídeo para mover (todos já postados).")
        return

    # Pega o primeiro da ordem
    next_video = pending_videos[0]
    src_path = os.path.join(PENDING_DIR, next_video)
    dst_path = os.path.join(POSTED_DIR, next_video)

    try:
        shutil.move(src_path, dst_path)
        posted.add(next_video)
        state["posted_videos"] = sorted(list(posted))
        save_state(state)
        print(f"✅ Vídeo movido (ordem alfabética): {next_video}")
    except Exception as e:
        print(f"❌ Erro ao mover '{next_video}': {e}")

if __name__ == "__main__":
    move_next_video()
