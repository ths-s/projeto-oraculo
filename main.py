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


def normalize_video(input_path):
    output_path = "normalized.mp4"
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-profile:v", "main",
        "-level", "4.1",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        output_path
    ])
    return output_path


VIDEOS_PENDING = "videos/pending"

def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)


def listar_videos(service):
    query = (
        f"'{PASTA_PARA_POSTAR}' in parents and "
        "("
        "mimeType contains 'video/' or "
        "name contains '.mp4' or "
        "name contains '.mov' or "
        "name contains '.mkv'"
        ") and "
        "mimeType != 'application/vnd.google-apps.shortcut'"
    )

    res = service.files().list(
        q=query,
        fields="files(id,name,mimeType)",
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

def main():
    service = drive_service()
    videos = listar_videos(service)

    if not videos:
        print("⚠️ Nenhum vídeo no Drive para postar.")
        return

    video = videos[0]
    print(f"🎬 Processando: {video['name']}")

    baixar_video(service, video["id"], video["name"])

    video_local_path = baixar_video(service, video["id"], video["name"])

    env = os.environ.copy()
    env["VIDEO_PATH"] = video_local_path

    result = subprocess.check_output(
        ["python", "upload_github_release.py"],
        env=env,
        text=True
    )

    for line in result.splitlines():
        if line.startswith("🌍 VIDEO_PUBLIC_URL="):
            public_url = line.split("=", 1)[1]
            break
    else:
        raise RuntimeError("❌ URL pública não encontrada.")

    env["VIDEO_URL"] = public_url
    env["DRIVE_FILE_ID"] = video["id"]

    subprocess.check_call(
        ["python", "upload_instagram.py"],
        env=env
    )


    # print("▶️ Upload YouTube")
    #subprocess.check_call(["python", "upload_youtube.py"])

    mover_video_drive(service, video["id"])
    print("✅ Vídeo postado e movido no Drive.")

if __name__ == "__main__":
    main()
