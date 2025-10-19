import json
import os
import re
import datetime
from statistics import mean

# ======================
# Caminhos
# ======================
DATA_DIR = "data"
METRICS_PATH = os.path.join(DATA_DIR, "metrics.json")
METADATA_PATH = "metadata.json"
RANKING_PATH = os.path.join(DATA_DIR, "gancho_ranking.json")

# ======================
# Funções de apoio
# ======================
def normalize(values):
    """Normaliza uma lista para 0–1"""
    if not values or max(values) == 0:
        return [0 for _ in values]
    max_v = max(values)
    return [v / max_v for v in values]

def title_match(title, gancho_title):
    """Verifica correspondência aproximada entre título do vídeo e título do gancho"""
    title = title.lower()
    gancho_title = gancho_title.lower()
    words = re.findall(r'\w+', gancho_title)
    return any(w in title for w in words[:3])

def time_weight(timestamp):
    """Retorna um peso de 0.5 a 1.0 baseado na recência (últimos 30 dias)"""
    try:
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        days = (datetime.datetime.now(datetime.timezone.utc) - dt).days
        return max(0.5, 1 - (days / 60))  # decai até 0.5 em 60 dias
    except Exception:
        return 1.0

def extract_hour(timestamp):
    try:
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.hour
    except Exception:
        return None

# ======================
# Carregar dados
# ======================
with open(METRICS_PATH, encoding="utf-8") as f:
    metrics = json.load(f)

with open(METADATA_PATH, encoding="utf-8") as f:
    metadata = json.load(f)

# ======================
# Análise YouTube
# ======================
yt_videos = metrics.get("youtube", {}).get("videos", [])
yt_scores = []
yt_hours = []

if yt_videos:
    yt_views = [v.get("views", 0) for v in yt_videos]
    yt_likes = [v.get("likes", 0) for v in yt_videos]
    yt_comments = [v.get("comments", 0) for v in yt_videos]

    norm_views = normalize(yt_views)
    norm_likes = normalize(yt_likes)
    norm_comments = normalize(yt_comments)

    for i, v in enumerate(yt_videos):
        weight = time_weight(v.get("timestamp", ""))
        score = (norm_views[i]*0.6 + norm_likes[i]*0.3 + norm_comments[i]*0.1) * 100 * weight
        v["score"] = round(score, 2)
        yt_scores.append(v["score"])

        h = extract_hour(v.get("timestamp", ""))
        if h is not None:
            yt_hours.append(h)

# ======================
# Análise Instagram
# ======================
ig_posts = metrics.get("instagram", {}).get("posts", [])
ig_scores = []
ig_hours = []

if ig_posts:
    avg_likes = mean([p.get("likes", 0) for p in ig_posts]) if ig_posts else 1
    avg_comments = mean([p.get("comments", 0) for p in ig_posts]) if ig_posts else 1

    for p in ig_posts:
        weight = time_weight(p.get("timestamp", ""))
        score = ((p.get("likes", 0)/avg_likes)*0.7 + (p.get("comments", 0)/avg_comments)*0.3) * 100 * weight
        p["score"] = min(round(score, 2), 100)
        ig_scores.append(p["score"])

        h = extract_hour(p.get("timestamp", ""))
        if h is not None:
            ig_hours.append(h)

# ======================
# Relacionar ganchos
# ======================
for gancho_key, gancho_data in metadata.items():
    g_title = gancho_data["title"]

    yt_match_scores = [v["score"] for v in yt_videos if title_match(v["title"], g_title)]
    ig_match_scores = [p["score"] for p in ig_posts if p.get("caption") and title_match(p["caption"], g_title)]

    score_youtube = mean(yt_match_scores) if yt_match_scores else 0
    score_instagram = mean(ig_match_scores) if ig_match_scores else 0
    score_total = round(score_youtube*0.6 + score_instagram*0.4, 2)

    gancho_data["score_youtube"] = round(score_youtube, 2)
    gancho_data["score_instagram"] = round(score_instagram, 2)
    gancho_data["score_total"] = score_total

# ======================
# Normalização final (0–100)
# ======================
all_scores = [g["score_total"] for g in metadata.values()]
if any(all_scores):
    max_score = max(all_scores)
    for g in metadata.values():
        g["score_total_normalized"] = round((g["score_total"]/max_score)*100, 2) if max_score > 0 else 0
else:
    for g in metadata.values():
        g["score_total_normalized"] = 0

# ======================
# Ranking geral
# ======================
ranking = sorted(
    [{"title": g["title"], "score": g["score_total_normalized"]} for g in metadata.values()],
    key=lambda x: x["score"],
    reverse=True
)

# ======================
# Análise de horário
# ======================
def best_hour(hours_list):
    if not hours_list:
        return None
    # agrupa e pega hora mais frequente
    from collections import Counter
    return Counter(hours_list).most_common(1)[0][0]

best_yt_hour = best_hour(yt_hours)
best_ig_hour = best_hour(ig_hours)

summary = {
    "melhor_horario_youtube": f"{best_yt_hour:02d}:00" if best_yt_hour is not None else "Indefinido",
    "melhor_horario_instagram": f"{best_ig_hour:02d}:00" if best_ig_hour is not None else "Indefinido",
    "total_ganchos": len(metadata),
    "total_videos_analisados": len(yt_videos),
    "total_posts_analisados": len(ig_posts),
}

# ======================
# Salvar resultados
# ======================
with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

with open(RANKING_PATH, "w", encoding="utf-8") as f:
    json.dump({"ranking": ranking, "resumo": summary}, f, ensure_ascii=False, indent=2)

print("✅ Análise concluída!")
print(f"🏆 Ranking salvo em {RANKING_PATH}")
print(f"🕒 Melhor horário YouTube: {summary['melhor_horario_youtube']}")
print(f"🕒 Melhor horário Instagram: {summary['melhor_horario_instagram']}")
