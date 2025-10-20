import os
import shutil

PENDING_DIR = "videos/pending"
POSTED_DIR = "videos/posted"

def move_first_video():
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)

    # Filtra apenas vídeos comuns
    video_files = [f for f in os.listdir(PENDING_DIR)
                   if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))]

    if not video_files:
        print("⚠️ Nenhum vídeo encontrado em 'videos/pending'.")
        return

    # Ordena e seleciona o primeiro
    first_video = sorted(video_files)[0]
    src_path = os.path.join(PENDING_DIR, first_video)
    dest_path = os.path.join(POSTED_DIR, first_video)

    try:
        # Move com verificação de sucesso
        shutil.move(src_path, dest_path)

        # Confere se foi realmente movido
        if not os.path.exists(dest_path):
            raise Exception("❌ Falha ao mover o arquivo — destino não encontrado.")

        if os.path.exists(src_path):
            os.remove(src_path)  # força exclusão se ainda existir

        print(f"✅ Vídeo movido com sucesso: {first_video}")
    except Exception as e:
        print(f"⚠️ Erro ao mover '{first_video}': {e}")

if __name__ == "__main__":
    move_first_video()
