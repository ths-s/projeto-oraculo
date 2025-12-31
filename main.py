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

PASTA_PARA_POSTAR = os.environ["PASTA_PARA_POSTAR"]
PASTA_POSTADOS = os.environ["PASTA_POSTADOS"]

if not PASTA_PARA_POSTAR or not PASTA_POSTADOS:
    raise RuntimeError("❌ Variáveis de ambiente do Drive não definidas")

# ---------------- DRIVE ---------------- #

def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def listar_videos(service):
    query = f"'{PASTA_PARA_POSTAR}' in parents and mimeType contains 'video/'"
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

    print("✅ Vídeo baixado:", path)
    return path

def mover_video_drive(service, file_id):
    file = service.files().get(fileId=file_id, fields="parents").execute()
    service.files().update(
        fileId=file_id,
        addParents=PASTA_POSTADOS,
        removeParents=",".join(file["parents"]),
    ).execute()

# ---------------- TESTES ---------------- #

def testar_url(video_url):
    print("🧪 Testando URL pública...")

    if "github.com" in video_url.lower():
        raise RuntimeError("❌ ERRO CRÍTICO: GitHub NÃO é permitido como host de vídeo")

    r = requests.get(video_url, stream=True, timeout=10)

    print("🔎 Status HTTP:", r.status_code)
    print("🔎 Content-Type:", r.headers.get("Content-Type"))
    print("🔎 Content-Length:", r.headers.get("Content-Length"))

    if r.status_code != 200:
        raise RuntimeError("❌ URL não acessível publicamente")

    if "video" not in (r.headers.get("Content-Type") or ""):
        raise RuntimeError("❌ URL não retorna vídeo")

    print("✅ URL validada com sucesso")

# ---------------- MAIN ---------------- #

def main():
    service = drive_service()
    videos = listar_videos(service)

    if not videos:
        print("⚠️ Nenhum vídeo para postar")
        return

    video = videos[0]
    print(f"🎬 Processando: {video['name']}")

    video_path = baixar_video(service, video["id"], video["name"])

    # ---------------- SERVIDOR LOCAL ---------------- #

    print("🌐 Iniciando servidor HTTP local")
    server = subprocess.Popen(
        ["python", "serve_video.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(3)

    # ---------------- NGROK ---------------- #

    print("🌐 Iniciando ngrok")
    ngrok = subprocess.Popen(
        ["ngrok", "http", "8000", "--log=stdout", "--log-format=json"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


    time.sleep(5)

    tunnels = requests.get("http://127.0.0.1:4040/api/tunnels").json()["tunnels"]

    public_url = None

    for _ in range(10):
        try:
            tunnels = requests.get(
                "http://127.0.0.1:4040/api/tunnels", timeout=2
            ).json().get("tunnels", [])

            for t in tunnels:
                if t.get("proto") == "https":
                    public_url = t.get("public_url")
                    break

            if public_url:
                break

        except Exception:
            time.sleep(1)

    if not public_url:
        raise RuntimeError("❌ Ngrok não inicializou a API local (4040)")


    video_url = f"{public_url}/{os.path.basename(video_path)}"
    print("🌍 URL pública:", video_url)

    # ---------------- TESTES ---------------- #

    testar_url(video_url)

    # ---------------- INSTAGRAM ---------------- #

    env = os.environ.copy()
    env["VIDEO_URL"] = video_url

    result = subprocess.run(
        ["python", "upload_instagram.py"],
        env=env,
        capture_output=True,
        text=True,
    )

    print(result.stdout)

    if result.returncode != 0:
        print("❌ Falha no Instagram")
        print(result.stderr)
        server.terminate()
        ngrok.terminate()
        return

    mover_video_drive(service, video["id"])
    print("✅ Vídeo postado e movido")

    server.terminate()
    ngrok.terminate()

if __name__ == "__main__":
    main()
