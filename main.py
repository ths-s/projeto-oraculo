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
    # Query aprimorada do seu main.py (aceita mais formatos e evita atalhos)
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
    # Usamos o /tmp para facilitar o serving do vídeo no GitHub Actions
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
        # Usamos diretamente a variável PASTA_PARA_POSTAR para remover o vínculo antigo
        # Isso evita o erro de 'Increasing the number of parents'
        service.files().update(
            fileId=file_id,
            addParents=PASTA_POSTADOS,
            removeParents=PASTA_PARA_POSTAR,
            supportsAllDrives=True
        ).execute()
        print(f"✅ Arquivo {file_id} movido para a pasta de postados no Drive.")
    except Exception as e:
        print(f"⚠️ Erro ao mover arquivo no Drive: {e}")

# ---------------- UTILITÁRIOS ---------------- #

def testar_url(video_url):
    print(f"🧪 Testando URL pública: {video_url}")
    headers = {"ngrok-skip-browser-warning": "true"}
    try:
        r = requests.get(video_url, headers=headers, stream=True, timeout=15)
        print("🔎 Status HTTP:", r.status_code)
        if r.status_code == 200:
            print("✅ URL validada com sucesso")
        else:
            print(f"⚠️ Aviso: Status {r.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar URL: {e}")

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

    # 1. INICIAR SERVIDOR LOCAL
    print("🌐 Iniciando servidor HTTP local na porta 8000...")
    server = subprocess.Popen(
        ["python", "serve_video.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)

    # 2. INICIAR NGROK
    print("🌐 Iniciando ngrok...")
    ngrok_token = os.environ.get("NGROK_AUTHTOKEN")
    
    with open("ngrok.log", "w") as log_file:
        ngrok = subprocess.Popen(
            ["ngrok", "http", "8000", "--authtoken", ngrok_token, "--log", "stdout"],
            stdout=log_file,
            stderr=log_file,
        )

    public_url = None
    print("⏳ Aguardando túnel do ngrok...")
    for i in range(15): 
        try:
            res = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if res.status_code == 200:
                tunnels = res.json().get("tunnels", [])
                for t in tunnels:
                    if t.get("proto") == "https":
                        public_url = t.get("public_url")
                        break
            if public_url:
                print(f"✅ Túnel ativo: {public_url}")
                break
        except:
            pass
        time.sleep(2)

    if not public_url:
        print("❌ ERRO: O ngrok não iniciou corretamente.")
        if os.path.exists("ngrok.log"):
            with open("ngrok.log", "r") as f: print(f.read())
        server.terminate()
        ngrok.terminate()
        raise RuntimeError("Falha ao obter URL do ngrok")

    video_url = f"{public_url}/{os.path.basename(video_path)}"
    
    # 3. TESTAR URL
    testar_url(video_url)

    # 4. UPLOAD YOUTUBE
    print("▶️ Iniciando Upload YouTube...")
    try:
        # O script do YouTube geralmente precisa do caminho do arquivo local
        env_yt = os.environ.copy()
        env_yt["VIDEO_PATH"] = video_path 
        subprocess.check_call(["python", "upload_youtube.py"], env=env_yt)
        print("✅ YouTube concluído")
    except Exception as e:
        print(f"❌ Erro no YouTube: {e}")

    # 5. UPLOAD INSTAGRAM
    print("▶️ Iniciando Upload Instagram...")
    env_ig = os.environ.copy()
    env_ig["VIDEO_URL"] = video_url
    
    result_ig = subprocess.run(
        ["python", "upload_instagram.py"],
        env=env_ig,
        capture_output=True,
        text=True,
    )
    print(result_ig.stdout)

    # Finalização
    if result_ig.returncode == 0:
        print("✅ Instagram concluído com sucesso")
        mover_video_drive(service, video["id"])
    else:
        print("❌ Falha no Instagram")
        print(result_ig.stderr)

    # Cleanup
    print("🧹 Finalizando processos...")
    server.terminate()
    ngrok.terminate()

if __name__ == "__main__":
    main()