import os
import json
import datetime
import requests
from googleapiclient.discovery import build
import pickle
import base64
import subprocess

# Caminhos
os.makedirs("data", exist_ok=True)
metrics_path = "data/metrics.json"
metadata_path = "metadata.json"

# Variáveis de ambiente (GitHub Secrets)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

# =======================
# 🔹 FUNÇÃO ATUALIZADA — COLETA AUTOMÁTICA DE TODOS OS VÍDEOS
# =======================
def get_youtube_metrics(youtube, metadata):
    print("🎥 Coletando métricas do YouTube...")

    # 🔸 1. Coleta dados gerais do canal
    channel_stats = youtube.channels().list(part="statistics", mine=True).execute()
    channel_data = channel_stats["items"][0]["statistics"]

    # 🔸 2. Descobre o ID do canal
    channel_id = channel_stats["items"][0]["id"]

    # 🔸 3. Busca todos os vídeos do canal (com paginação)
    all_video_ids = []
    next_page_token = None

    while True:
        res = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=50,
            type="video",
            order="date",
            pageToken=next_page_token
        ).execute()

        for item in res.get("items", []):
            vid = item["id"]["videoId"]
            all_video_ids.append(vid)

        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

    print(f"🔎 Encontrados {len(all_video_ids)} vídeos no canal.")

    # 🔸 4. Busca métricas de cada vídeo em lotes de 50 (limite da API)
    video_metrics = []
    for i in range(0, len(all_video_ids), 50):
        batch = all_video_ids[i:i + 50]
        stats_res = youtube.videos().list(part="snippet,statistics", id=",".join(batch)).execute()

        for item in stats_res.get("items", []):
            vid = item["id"]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})

            video_metrics.append({
                "video_id": vid,
                "title": snippet.get("title", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "publishedAt": snippet.get("publishedAt", "")
            })

    summary = {
        "viewCount": int(channel_data.get("viewCount", 0)),
        "subscriberCount": int(channel_data.get("subscriberCount", 0)),
        "videoCount": int(channel_data.get("videoCount", 0)),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

    print(f"✅ Coletadas métricas de {len(video_metrics)} vídeos do YouTube.")

    return {
        "summary": summary,
        "videos": video_metrics
    }

# =======================
# 🔹 FUNÇÕES DO INSTAGRAM
# =======================
def get_instagram_metrics(metadata):
    print("📸 Coletando métricas do Instagram...")

    base_url = "https://graph.facebook.com"
    fields = (
        "id,caption,media_type,media_url,thumbnail_url,timestamp,"
        "permalink,like_count,comments_count,children{media_url,media_type}"
    )
    url = f"{base_url}/{IG_USER_ID}/media?fields={fields}&access_token={GRAPH_API_TOKEN}"

    all_posts = []
    try:
        # 🔁 Paginação — busca todas as páginas
        while url:
            r = requests.get(url)
            data = r.json()

            if "error" in data:
                print("❌ Erro retornado pela API:", data["error"])
                break

            posts = data.get("data", [])
            all_posts.extend(posts)

            # Verifica se há próxima página
            url = data.get("paging", {}).get("next")

    except Exception as e:
        print("❌ Erro ao acessar a API do Instagram:", e)
        return {"summary": {}, "posts": []}

    if not all_posts:
        print("⚠️ Nenhum post encontrado. Verifique GRAPH_API_TOKEN e IG_USER_ID.")
        return {"summary": {}, "posts": []}

    insta_metrics = []
    total_likes = total_comments = 0

    for post in all_posts:
        caption = post.get("caption", "")
        like_count = post.get("like_count", 0)
        comments_count = post.get("comments_count", 0)
        total_likes += like_count
        total_comments += comments_count

        # tenta associar o post com metadados existentes
        match = next(
            (v for k, v in metadata.items() if caption and caption.strip() in v.get("description", "")),
            None
        )

        insta_metrics.append({
            "id": post.get("id"),
            "caption": caption,
            "media_type": post.get("media_type"),
            "media_url": post.get("media_url"),
            "thumbnail_url": post.get("thumbnail_url"),
            "permalink": post.get("permalink"),
            "timestamp": post.get("timestamp"),
            "likes": like_count,
            "comments": comments_count,
            "children": post.get("children", {}).get("data", []),
            "matched_metadata": match
        })

    summary = {
        "totalPosts": len(insta_metrics),
        "totalLikes": total_likes,
        "totalComments": total_comments,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

    print(f"✅ Coletados {len(insta_metrics)} posts do Instagram.")

    return {"summary": summary, "posts": insta_metrics}


# =======================
# 🔹 AUTENTICAÇÃO YOUTUBE
# =======================
def get_youtube_service():
    token_pickle_data = os.getenv("TOKEN_PICKLE_COMPLETE")
    if not token_pickle_data:
        raise Exception("TOKEN_PICKLE_COMPLETE não encontrado!")

    token_pickle_bytes = pickle.loads(base64.b64decode(token_pickle_data))
    return build("youtube", "v3", credentials=token_pickle_bytes)

# =======================
# 🔹 EXECUÇÃO PRINCIPAL
# =======================
def main():
    print("📊 Coletando métricas...")

    if not os.path.exists(metadata_path):
        raise FileNotFoundError("metadata.json não encontrado!")

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    youtube = get_youtube_service()
    youtube_data = get_youtube_metrics(youtube, metadata)
    instagram_data = get_instagram_metrics(metadata)

    final_data = {
        "youtube": youtube_data,
        "instagram": instagram_data
    }

    with open(metrics_path, "w") as f:
        json.dump(final_data, f, indent=4)

    print("✅ Métricas salvas em", metrics_path)

if __name__ == "__main__":
    main()

# =======================
# 🔹 COMMIT AUTOMÁTICO
# =======================
def git_commit_metrics():
    subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", "data/metrics.json"], check=True)
    subprocess.run(["git", "commit", "-m", "Atualiza métricas do YouTube e Instagram"], check=False)
    subprocess.run(["git", "push"], check=False)

git_commit_metrics()
