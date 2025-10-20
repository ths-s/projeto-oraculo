import os
import shutil
import json

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"
STATE_PATH = "data/state.json"

def move_first_video():
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)

    # Carrega histórico
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError:
                state = {}
    else:
        state = {}

    posted_videos = set(state.get("posted_videos", []))

    # Lista vídeos ainda não postados
    pending_videos = [
        f for f in sorted(os.listdir(PENDING_DIR))
        if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))
        and f not in posted_videos
    ]

    if not pending_videos:
        print("⚠️ Nenhum novo vídeo para mover.")
        return

    first_video = pending_videos[0]
    src = os.path.join(PENDING_DIR, first_video)
    dst = os.path.join(POSTED_DIR, first_video)

    try:
        # Move o arquivo
        shutil.move(src, dst)

        # Confirma se realmente saiu da pasta original
        if os.path.exists(src):
            os.remove(src)

        # Atualiza histórico
        posted_videos.add(first_video)
        state["posted_videos"] = sorted(list(posted_videos))

        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)

        print(f"✅ Vídeo movido com sucesso: {first_video}")
    except Exception as e:
        print(f"❌ Erro ao mover vídeo '{first_video}': {e}")

if __name__ == "__main__":
    move_first_video()
