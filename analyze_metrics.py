#!/usr/bin/env python3
# analyze_metrics_fixed.py
import json
import os
import re
import datetime
from statistics import mean
from collections import Counter

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
    if not values:
        return []
    max_v = max(values) if max(values) > 0 else 1
    return [v / max_v for v in values]

def title_match_text(source_text, gancho_data):
    """
    Verifica correspondência aproximada entre texto (título/caption) e um gancho.
    Checa title, description e tags do gancho para aumentar recall.
    """
    if not source_text:
        return False
    s = source_text.lower()
    # palavras do título do gancho
    g_title = gancho_data.get("title", "").lower()
    words = re.findall(r'\w+', g_title)
    # check first 3 words of title
    for w in words[:3]:
        if w and w in s:
            return True
    # check description
    g_desc = gancho_data.get("description", "")
    if g_desc and any(w in s for w in re.findall(r'\w+', g_desc.lower())[:4]):
        return True
    # check tags
    for tag in gancho_data.get("tags", []):
        if tag.lower() in s:
            return True
    return False

def time_weight_from_iso(timestamp_iso):
    """
    Retorna um peso de 0.5 a 1.0 baseado na recência (últimos 60 dias).
    Aceita timestamps como '2025-10-19T14:35:19Z' (publishedAt) ou '2025-10-16T16:19:45+0000'
    """
    if not timestamp_iso:
        return 1.0
    # normalize common formats
    ts = timestamp_iso
    # convert +0000 -> +00:00 for fromisoformat
    ts = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', ts)
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        days = (now - dt).days
        # decai linearmente até 0.5 em 60 dias
        return max(0.5, 1 - (days / 60))
    except Exception:
        return 1.0

def extract_hour_from_iso(timestamp_iso):
    if not timestamp_iso:
        return None
    ts = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', timestamp_iso)
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.hour
    except Exception:
        return None

# ======================
# Leitura de arquivos
# ======================
if not os.path.exists(METRICS_PATH):
    raise FileNotFoundError(f"{METRICS_PATH} não encontrado.")

if not os.path.exists(METADATA_PATH):
    raise FileNotFoundError(f"{METADATA_PATH} não encontrado.")

with open(METRICS_PATH, encoding="utf-8") as f:
    metrics = json.load(f)

with open(METADATA_PATH, encoding="utf-8") as f:
    metadata = json.load(f)

# ======================
# Preparar listas
# ======================
yt_videos = metrics.get("youtube", {}).get("videos", [])
ig_posts = metrics.get("instagram", {}).get("posts", [])

# ======================
# YouTube: normalização e scores (usa publishedAt)
# ======================
yt_views = [v.get("views", 0) for v in yt_videos]
yt_likes = [v.get("likes", 0) for v in yt_videos]
yt_comments = [v.get("comments", 0) for v in yt_videos]

norm_views = normalize(yt_views)
norm_likes = normalize(yt_likes)
norm_comments = normalize(yt_comments)

yt_hours = []
for i, v in enumerate(yt_videos):
    published = v.get("publishedAt") or v.get("timestamp") or ""
    weight = time_weight_from_iso(published)
    score = (norm_views[i]*0.6 + norm_likes[i]*0.3 + norm_comments[i]*0.1) * 100 * weight
    v["score"] = round(score, 2)
    h = extract_hour_from_iso(published)
    if h is not None:
        yt_hours.append(h)

# ======================
# Instagram: normalização e scores (usa timestamp)
# ======================
ig_likes_list = [p.get("likes", 0) for p in ig_posts] or [1]
ig_comments_list = [p.get("comments", 0) for p in ig_posts] or [1]
avg_likes = mean(ig_likes_list) if ig_likes_list else 1
avg_comments = mean(ig_comments_list) if ig_comments_list else 1

ig_hours = []
for p in ig_posts:
    ts = p.get("timestamp") or p.get("created_time") or ""
    weight = time_weight_from_iso(ts)
    # evita divisão por zero
    likes_ratio = (p.get("likes", 0) / avg_likes) if avg_likes > 0 else 0
    comments_ratio = (p.get("comments", 0) / avg_comments) if avg_comments > 0 else 0
    score = ((likes_ratio)*0.7 + (comments_ratio)*0.3) * 100 * weight
    p["score"] = round(min(score, 100), 2)
    h = extract_hour_from_iso(ts)
    if h is not None:
        ig_hours.append(h)

# ======================
# Relacionar ganchos e calcular scores por gancho
# ======================
skipped = []
for gancho_key, gancho_data in list(metadata.items()):
    if not isinstance(gancho_data, dict):
        skipped.append((gancho_key, "não é objeto/dict"))
        continue
    if "title" not in gancho_data and "description" not in gancho_data:
        skipped.append((gancho_key, "sem campo 'title' ou 'description'"))
        continue
    if "title" not in gancho_data:
        gancho_data["title"] = gancho_data.get("description", "")


    # buscar correspondências no Youtube (título)
    yt_matches = [v["score"] for v in yt_videos if title_match_text(v.get("title", ""), gancho_data)]
    # buscar correspondências no Instagram (caption)
    ig_matches = [p["score"] for p in ig_posts if p.get("caption") and title_match_text(p.get("caption", ""), gancho_data)]

    score_youtube = mean(yt_matches) if yt_matches else 0.0
    score_instagram = mean(ig_matches) if ig_matches else 0.0
    score_total = round(score_youtube*0.6 + score_instagram*0.4, 2)

    # grava no metadata
    gancho_data["score_youtube"] = round(score_youtube, 2)
    gancho_data["score_instagram"] = round(score_instagram, 2)
    gancho_data["score_total"] = score_total

# ======================
# Normalização final (0–100)
# ======================
all_scores = [g.get("score_total", 0) for g in metadata.values() if isinstance(g, dict)]
max_score = max(all_scores) if all_scores else 0
for k, g in metadata.items():
    if isinstance(g, dict):
        g["score_total_normalized"] = round((g.get("score_total", 0) / max_score) * 100, 2) if max_score > 0 else 0

# ======================
# Ranking
# ======================
ranking = sorted(
    [
        {"key": k, "title": g.get("title", ""), "score": g.get("score_total_normalized", 0)}
        for k, g in metadata.items() if isinstance(g, dict)
    ],
    key=lambda x: x["score"],
    reverse=True
)

# ======================
# Melhor horário (hora mais frequente)
# ======================
def best_hour(hours_list):
    if not hours_list:
        return None
    return Counter(hours_list).most_common(1)[0][0]

best_yt_hour = best_hour(yt_hours)
best_ig_hour = best_hour(ig_hours)

summary = {
    "melhor_horario_youtube": f"{best_yt_hour:02d}:00" if best_yt_hour is not None else "Indefinido",
    "melhor_horario_instagram": f"{best_ig_hour:02d}:00" if best_ig_hour is not None else "Indefinido",
    "total_ganchos": sum(1 for v in metadata.values() if isinstance(v, dict)),
    "total_videos_analisados": len(yt_videos),
    "total_posts_analisados": len(ig_posts),
    "skipped_metadata_entries": skipped
}

# ======================
# Salvar arquivos
# ======================
with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

os.makedirs(DATA_DIR, exist_ok=True)
with open(RANKING_PATH, "w", encoding="utf-8") as f:
    json.dump({"ranking": ranking, "resumo": summary}, f, ensure_ascii=False, indent=2)

# ======================
# Relatório final
# ======================
print("✅ Análise concluída!")
print(f"🏆 Ranking salvo em {RANKING_PATH}")
print(f"🕒 Melhor horário YouTube: {summary['melhor_horario_youtube']}")
print(f"🕒 Melhor horário Instagram: {summary['melhor_horario_instagram']}")
if skipped:
    print("⚠️ Entradas puladas em metadata.json:")
    for key, reason in skipped:
        print(f"  - {key}: {reason}")
