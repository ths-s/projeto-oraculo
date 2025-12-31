import os
import io
import subprocess
import time
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ---------------- CONFIG ---------------- #
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "service_account.json"

PASTA_PARA_POSTAR = os.environ.get("PASTA_PARA_POSTAR")
PASTA_POSTADOS = os.environ.get("PASTA_POSTADOS")

if not PASTA_PARA_POSTAR or not PASTA_POSTADOS:
    raise RuntimeError("❌ Variáveis de ambiente PASTA_PARA_POSTAR ou PASTA_POSTADOS não definidas")

# ---------------- DRIVE ---------------- #

def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def listar_videos(service):
    # Busca por vídeos na pasta PARA_POSTAR
    query = (
        f"'{PASTA_PARA_POSTAR}' in parents and "
        "(mimeType contains 'video/' or name contains '.mp4') and "
        "mimeType != 'application/vnd.google-apps.shortcut'"
    )
    
    res = service.files().list(
        q=query,
        fields="files(id,name,mimeType)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="allDrives",
    ).execute()

    files = res.get("files", [])
    print(f"📂 Arquivos encontrados no Drive: {len(files)}")
    return files

def baixar_video(service, file_id, name):
    path = f"/tmp/{name}"
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(path, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    print("✅ Vídeo baixado:", path)
    return path

def mover_video_drive(service, file_id):
    try:
        service.files().update(
            fileId=file_id,
            addParents=PASTA_POSTADOS,
            removeParents=PASTA_PARA_POSTAR,
            supportsAllDrives=True,
            fields="id, parents"
        ).execute()

        print("✅ Vídeo movido com sucesso para a pasta POSTADOS.")

    except Exception as e:
        print(f"❌ Erro ao mover arquivo no Drive: {e}")

# ---------------- MAIN ---------------- #

def main():
    service = drive_service()
    videos = listar_videos(service)

    if not videos:
        print("⚠️ Nenhum vídeo pendente na pasta PARA_POSTAR.")
        return

    # GARANTE APENAS UM VÍDEO: Pegamos sempre o primeiro da lista
    video = videos[0]
    print(f"🎬 Processando vídeo único da rodada: {video['name']}")
    video_path = baixar_video(service, video["id"], video["name"])

    # 1. INICIAR SERVIDOR LOCAL
    server = subprocess.Popen(["python", "serve_video.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    # 2. INICIAR NGROK
    ngrok_token = os.environ.get("NGROK_AUTHTOKEN")
    with open("ngrok.log", "w") as log_file:
        ngrok = subprocess.Popen(
            ["ngrok", "http", "8000", "--authtoken", ngrok_token, "--log", "stdout"],
            stdout=log_file, stderr=log_file
        )

    public_url = None
    for i in range(15):
        try:
            res = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if res.status_code == 200:
                tunnels = res.json().get("tunnels", [])
                for t in tunnels:
                    if t.get("proto") == "https":
                        public_url = t.get("public_url")
                        break
            if public_url: break
        except: pass
        time.sleep(2)

    if not public_url:
        server.terminate()
        ngrok.terminate()
        raise RuntimeError("Falha ao obter túnel ngrok")

    video_url = f"{public_url}/{os.path.basename(video_path)}"
    """
    # 3. UPLOAD YOUTUBE
    print("▶️ Enviando para o YouTube...")
    try:
        env_yt = os.environ.copy()
        env_yt["VIDEO_PATH"] = video_path 
        subprocess.check_call(["python", "upload_youtube.py"], env=env_yt)
        yt_success = True
    except:
        yt_success = False
        print("❌ Erro no upload do YouTube")

    # 4. UPLOAD INSTAGRAM
    print("▶️ Enviando para o Instagram...")
    env_ig = os.environ.copy()
    env_ig["VIDEO_URL"] = video_url
    result_ig = subprocess.run(["python", "upload_instagram.py"], env=env_ig, capture_output=True, text=True)
    print(result_ig.stdout)

    # FINALIZAÇÃO
    if result_ig.returncode == 0 and yt_success:
        print("✨ Sucesso total! Movendo arquivo no Drive...")
        mover_video_drive(service, video["id"])
    else:
        print("⚠️ O vídeo não foi movido pois um dos uploads falhou.")
    """
    mover_video_drive(service, video["id"])

    server.terminate()
    ngrok.terminate()

if __name__ == "__main__":
    main()