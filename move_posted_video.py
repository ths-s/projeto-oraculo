import os
import shutil

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"

def move_first_video():
    # Garante que os diretórios existem
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)

    # Lista arquivos de vídeo (qualquer formato comum)
    video_files = [f for f in os.listdir(PENDING_DIR)
                   if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))]

    if not video_files:
        print("⚠️ Nenhum vídeo encontrado em 'videos/pending'. Nada a mover.")
        return

    # Seleciona o primeiro arquivo
    first_video = sorted(video_files)[0]
    src_path = os.path.join(PENDING_DIR, first_video)
    dest_path = os.path.join(POSTED_DIR, first_video)

    # Move o arquivo
    shutil.move(src_path, dest_path)
    print(f"✅ Vídeo movido de '{PENDING_DIR}' para '{POSTED_DIR}': {first_video}")

if __name__ == "__main__":
    move_first_video()
