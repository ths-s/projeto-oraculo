import os
import io
import subprocess
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "service_account.json"

PASTA_PARA_POSTAR = os.environ["PASTA_PARA_POSTAR"]
PASTA_POSTADOS = os.environ["PASTA_POSTADOS"]

if not PASTA_PARA_POSTAR or not PASTA_POSTADOS:
    raise RuntimeError("❌ PASTA_PARA_POSTAR ou PASTA_POSTADOS não definidos.")

# ---------------- DRIVE ---------------- #

def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

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
        corpora="allDrives",
    ).execute()

    print("📂 Arquivos encontrados no Drive:", res.get("files", []))
    return res.get("files", [])

def baixar_video(service, file_id, name):
    path = f"/tmp/{name}"

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
        removeParents=",".join(file["parents"]),
    ).execute()

# ---------------- MAIN ---------------- #

def main():
    service = drive_service()
    videos = listar_videos(service)

    if not videos:
        print("⚠️ Nenhum vídeo no Drive para postar.")
        return

    video = videos[0]
    print(f"🎬 Processando: {video['name']}")

    video_path = baixar_video(service, video["id"], video["name"])

    # 🔹 Upload para GitHub Release (gera URL pública)
    print("⬆️ Upload do vídeo para GitHub Release")

    env = os.environ.copy()
    env["VIDEO_PATH"] = video_path

    result = subprocess.run(
        ["python", "upload_github_release.py"],
        env=env,
        capture_output=True,
        text=True,
    )

    print(result.stdout)

    if result.returncode != 0:
        print("❌ Falha no upload para GitHub Release")
        print(result.stderr)
        return

    # 🔹 Extrair URL pública
    video_url = None
    for line in result.stdout.splitlines():
        if line.startswith("🌍 VIDEO_PUBLIC_URL="):
            video_url = line.split("=", 1)[1].strip()

    if not video_url:
        print("❌ Não foi possível obter a URL pública do vídeo.")
        return

    print("🌍 URL pública final:", video_url)

    # 🔹 Upload Instagram
    print("▶️ Upload Instagram")

    env["VIDEO_URL"] = video_url
    env["VIDEO_FILENAME"] = os.path.basename(video_path)

    result = subprocess.run(
        ["python", "upload_instagram.py"],
        env=env,
        capture_output=True,
        text=True,
    )

    print(result.stdout)

    if result.returncode != 0:
        print("❌ Falha no upload Instagram, vídeo NÃO será movido.")
        print(result.stderr)
        return

    mover_video_drive(service, video["id"])
    print("✅ Vídeo postado e movido no Drive.")

if __name__ == "__main__":
    main()
