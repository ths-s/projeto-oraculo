import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ================= CONFIG =================
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'

PASTA_PARA_POSTAR = os.environ['PASTA_PARA_POSTAR']
PASTA_POSTADOS = os.environ['PASTA_POSTADOS']
# =========================================

def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

def listar_videos(service):
    query = f"'{PASTA_PARA_POSTAR}' in parents and mimeType contains 'video/'"
    results = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

def baixar_video(service, file_id, nome):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(nome, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

def mover_video(service, file_id):
    file = service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    service.files().update(
        fileId=file_id,
        addParents=PASTA_POSTADOS,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()

def postar_video(caminho):
    """
    AQUI você pluga:
    - YouTube API
    - Instagram Graph API
    - Outro serviço
    """
    print(f"Postando vídeo: {caminho}")
    # exemplo:
    # youtube_upload(caminho)

def main():
    service = drive_service()
    videos = listar_videos(service)

    if not videos:
        print("Nenhum vídeo para postar.")
        return

    video = videos[0]
    nome = video['name']
    file_id = video['id']

    baixar_video(service, file_id, nome)
    postar_video(nome)
    mover_video(service, file_id)

    print(f"Vídeo '{nome}' postado e movido com sucesso.")

if __name__ == "__main__":
    main()
