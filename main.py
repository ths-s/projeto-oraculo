import os
import io
import subprocess
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'

PASTA_PARA_POSTAR = os.environ['PASTA_PARA_POSTAR']
PASTA_POSTADOS = os.environ['PASTA_POSTADOS']


if not PASTA_PARA_POSTAR or not PASTA_POSTADOS:
    raise RuntimeError(
        "❌ PASTA_PARA_POSTAR ou PASTA_POSTADOS não definidos nos secrets."
    )


VIDEOS_PENDING = "videos/pending"

res = service.files().list(
    q=f"'{PASTA_PARA_POSTAR}' in parents",
    fields="files(id,name,mimeType)"
).execute()

print(res)


def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

def listar_videos(service):
    query = f"'{PASTA_PARA_POSTAR}' in parents and mimeType contains 'video/'"
    res = service.files().list(q=query, fields="files(id,name)").execute()
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

def main():
    service = drive_service()
    videos = listar_videos(service)

    if not videos:
        print("⚠️ Nenhum vídeo no Drive para postar.")
        return

    video = videos[0]
    print(f"🎬 Processando: {video['name']}")

    baixar_video(service, video["id"], video["name"])

    print("▶️ Upload YouTube")
    subprocess.check_call(["python", "upload_youtube.py"])

    print("▶️ Upload Instagram")
    subprocess.check_call(["python", "upload_instagram.py"])

    mover_video_drive(service, video["id"])
    print("✅ Vídeo postado e movido no Drive.")

if __name__ == "__main__":
    main()
