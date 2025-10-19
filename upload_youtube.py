import os
import pickle
import base64
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http
from google.auth.transport.requests import Request
import json

VIDEO_FOLDER = "videos/pending"
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"
METADATA_FILE = "metadata.json"
GANCHO_FILE = "gancho_data.json"
STATE_FILE = "data/state.json"


def setup_credentials_files():
    client_secret_json = os.getenv("YOUTUBE_CLIENT_SECRET_JSON")
    token_pickle_b64 = os.getenv("YOUTUBE_TOKEN_PICKLE")

    if not client_secret_json:
        raise ValueError("❌ Variável YOUTUBE_CLIENT_SECRET_JSON não encontrada.")

    with open(CLIENT_SECRETS_FILE, "w") as f:
        f.write(client_secret_json)

    if token_pickle_b64:
        token_bytes = base64.b64decode(token_pickle_b64.encode())
        with open(TOKEN_FILE, "wb") as f:
            f.write(token_bytes)


def get_authenticated_service():
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    credentials = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            credentials = pickle.load(f)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, scopes
            )
            credentials = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)

    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


def find_videos(folder=VIDEO_FOLDER):
    if not os.path.exists(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
    ]


def load_gancho_data():
    if not os.path.exists(GANCHO_FILE):
        raise FileNotFoundError("❌ Arquivo gancho_data.json não encontrado!")
    with open(GANCHO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_metadata(metadata):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)


def upload_video(file_path, title, description, tags=None, category_id="22", privacy="public"):
    youtube = get_authenticated_service()
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags if tags else [],
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy},
    }

    media = googleapiclient.http.MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
    response = request.execute()
    print("✅ Upload concluído no YouTube! ID:", response["id"])
    return response


if __name__ == "__main__":
    setup_credentials_files()
    videos = find_videos()
    gancho_data = load_gancho_data()
    metadata = load_metadata()
    state = load_state()

    if not videos:
        print("⚠️ Nenhum vídeo encontrado em", VIDEO_FOLDER)
    else:
        # Verificar horário
        agora = datetime.datetime.utcnow()
        proximo_horario = state.get("proximo_horario_yt")
        if agora.hour != proximo_horario:
            print(f"⚠️ Não é a hora certa para postar no YouTube ({proximo_horario}:00). Aguardando.")
            exit(0)

        # Usar gancho sugerido do state
        gancho_name = state.get("proximo_gancho_yt")
        if not gancho_name or gancho_name not in gancho_data:
            gancho_name = random.choice(list(gancho_data.keys()))  # Fallback

        gancho = gancho_data[gancho_name]

        video_path = videos[0]
        video_name = os.path.basename(video_path)

        # Upload
        response = upload_video(
            file_path=video_path,
            title=gancho["title"],
            description=gancho["description"],
            tags=gancho["tags"],
        )

        video_id = response.get("id")

        # Salvar metadata
        metadata[video_name] = {
            "gancho": gancho_name,
            "youtube_id": video_id,
        }
        save_metadata(metadata)
        print(f"📁 Metadata atualizado com ID do vídeo ({video_id}) e gancho {gancho_name}.")

        # Atualizar state
        state["ultimo_gancho_postado"] = gancho_name  # Compatibilidade, mas pode remover se separado
        state["ultimo_post_youtube"] = agora.isoformat()
        save_state(state)