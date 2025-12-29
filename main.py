import os
import io
import time
import subprocess
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'

PASTA_PARA_POSTAR = os.environ['PASTA_PARA_POSTAR']
PASTA_POSTADOS = os.environ['PASTA_POSTADOS']

VIDEOS_PENDING = "videos/pending"


def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)


def listar_videos(service):
    query = f"'{PASTA_PARA_POSTAR}' in parents and mimeType contains 'video/'"
    res = service.files().list(
        q=query,
        fields="files(id,name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="allDrives"
    ).execute()

    print("📂 Arquivos encontrados no Drive:", res.get("files", []))
    return res.get("files", [])


def baixar_video(service, file_id, name):
    os.makedirs(VIDEOS_PENDING, exist_ok=True)
    path = os.path.join(VIDEOS_PENDING, name)

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(path, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    return path


def mover_video_drive(service, file_id):
    file = service.files().get(fileId=file_id, fields="parents").execute()
    service.files().update(
        fileId=file_id,
        addParents=PASTA_POSTADOS,
        removeParents=",".join(file["parents"])
    ).execute()


def start_ngrok():
    subprocess.Popen(["ngrok", "http", "8000"], stdout=subprocess.DEVNULL)
    time.sleep(5)

    res = requests.get("http://localhost:4040/api/tunnels").json()
    for tunnel in res["tunnels"]:
        if tunnel["proto"] == "https":
            return tunnel["public_url"]

    raise RuntimeError("❌ Não foi possível obter URL do ngrok")


def main():
    service = drive_service()
    videos = listar_videos(service)

    if not videos:
        print("⚠️ Nenhum vídeo para postar.")
        return

    video = videos[0]
    print(f"🎬 Processando: {video['name']}")

    baixar_video(service, video["id"], video["name"])

    # Servidor HTTP local
    subprocess.Popen(["python", "serve_videos.py"])
    time.sleep(2)

    # ngrok
    public_url = start_ngrok()
    video_url = f"{public_url}/{video['name']}"
    print("🌍 URL pública:", video_url)

    env = os.environ.copy()
    env["VIDEO_URL"] = video_url

    print("▶️ Upload Instagram")
    subprocess.check_call(
        ["python", "upload_instagram.py"],
        env=env
    )

    mover_video_drive(service, video["id"])
    print("✅ Vídeo postado e movido no Drive.")


if __name__ == "__main__":
    main()
