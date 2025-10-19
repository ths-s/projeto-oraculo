import json
import datetime
import random
from statistics import mean, median
import matplotlib.pyplot as plt
import os
import subprocess

# =======================
# 📁 Caminhos
# =======================
DATA_DIR = "data"
METRICS_PATH = os.path.join(DATA_DIR, "metrics.json")
METADATA_PATH = "metadata.json"
GANCHO_PATH = "gancho_data.json"
RESULT_PATH = os.path.join(DATA_DIR, "analise_ganchos.json")
STATE_PATH = os.path.join(DATA_DIR, "state.json")

# =======================
# ⚙️ Configurações
# =======================
MIN_HOURS_BETWEEN_POSTS = 12
POST_HOURS = list(range(6, 24))  # horários possíveis (6h às 23h)
POINT_THRESHOLD = 3

# Pesos (diferentes para plataformas)
YT_WEIGHTS = {"views": 1.0, "likes": 0.5, "comments": 2.0}
IG_WEIGHTS = {"likes": 1.5, "comments": 1.0}

# =======================
# 🔹 Utilitários
# =======================
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =======================
# 🔹 Análise de desempenho
# =======================
def analisar_desempenho(metrics, metadata, ganchos):
    # Reset points in metadata
    for meta in metadata.values():
        meta["points"] = {"youtube": 0, "instagram": 0}
        # hour is set per video when processing

    # YouTube
    yt_videos = metrics["youtube"]["videos"]
    all_yt_views = [v["views"] for v in yt_videos]
    all_yt_likes = [v["likes"] for v in yt_videos]
    all_yt_comments = [v["comments"] for v in yt_videos]
    med_yt_views = median(all_yt_views) if all_yt_views else 0
    med_yt_likes = median(all_yt_likes) if all_yt_likes else 0
    med_yt_comments = median(all_yt_comments) if all_yt_comments else 0

    yt_analise = {}
    yt_horarios = {}
    for v in yt_videos:
        for file, meta in metadata.items():
            if meta.get("youtube_id") == v["video_id"]:
                g = meta["gancho"]
                yt_analise.setdefault(g, {"views": [], "likes": [], "comments": [], "horarios": []})
                yt_analise[g]["views"].append(v["views"])
                yt_analise[g]["likes"].append(v["likes"])
                yt_analise[g]["comments"].append(v["comments"])
                pub_time = datetime.datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00"))
                hora = pub_time.hour
                meta["hour"] = hora
                yt_analise[g]["horarios"].append(hora)
                yt_horarios.setdefault(hora, {"views": [], "likes": [], "comments": []})
                yt_horarios[hora]["views"].append(v["views"])
                yt_horarios[hora]["likes"].append(v["likes"])
                yt_horarios[hora]["comments"].append(v["comments"])

                # Distribuir pontos
                points = 0.0
                if v["views"] > med_yt_views:
                    points += YT_WEIGHTS["views"]
                if v["likes"] > med_yt_likes:
                    points += YT_WEIGHTS["likes"]
                if v["comments"] > med_yt_comments:
                    points += YT_WEIGHTS["comments"]
                meta["points"]["youtube"] = points

    # Instagram
    ig_posts = metrics["instagram"]["posts"]
    all_ig_likes = [p["likes"] for p in ig_posts]
    all_ig_comments = [p["comments"] for p in ig_posts]
    med_ig_likes = median(all_ig_likes) if all_ig_likes else 0
    med_ig_comments = median(all_ig_comments) if all_ig_comments else 0

    ig_analise = {}
    ig_horarios = {}
    for p in ig_posts:
        for file, meta in metadata.items():
            if meta.get("instagram_id") == p["id"]:
                g = meta["gancho"]
                ig_analise.setdefault(g, {"likes": [], "comments": [], "horarios": []})
                ig_analise[g]["likes"].append(p["likes"])
                ig_analise[g]["comments"].append(p["comments"])
                pub_time = datetime.datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00"))
                hora = pub_time.hour
                meta["hour"] = hora
                ig_analise[g]["horarios"].append(hora)
                ig_horarios.setdefault(hora, {"likes": [], "comments": []})
                ig_horarios[hora]["likes"].append(p["likes"])
                ig_horarios[hora]["comments"].append(p["comments"])

                # Distribuir pontos
                points = 0.0
                if p["likes"] > med_ig_likes:
                    points += IG_WEIGHTS["likes"]
                if p["comments"] > med_ig_comments:
                    points += IG_WEIGHTS["comments"]
                meta["points"]["instagram"] = points

    # Salvar metadata atualizado com points e hours
    save_json(metadata, METADATA_PATH)

    # Calcular médias e scores
    resultados = []
    for g in ganchos:
        yt_views = yt_analise.get(g, {}).get("views", [])
        yt_likes = yt_analise.get(g, {}).get("likes", [])
        yt_comments = yt_analise.get(g, {}).get("comments", [])
        ig_likes = ig_analise.get(g, {}).get("likes", [])
        ig_comments = ig_analise.get(g, {}).get("comments", [])
        avg_views = mean(yt_views) if yt_views else 0
        avg_likes = mean(yt_likes + ig_likes) if yt_likes or ig_likes else 0
        avg_comments = mean(yt_comments + ig_comments) if yt_comments or ig_comments else 0
        score = avg_views * YT_WEIGHTS["views"] + avg_likes * (YT_WEIGHTS["likes"] + IG_WEIGHTS["likes"]) / 2 + avg_comments * (YT_WEIGHTS["comments"] + IG_WEIGHTS["comments"]) / 2
        hora_media = mean(yt_analise.get(g, {}).get("horarios", []) + ig_analise.get(g, {}).get("horarios", [])) if yt_analise.get(g, {}).get("horarios", []) or ig_analise.get(g, {}).get("horarios", []) else None

        resultados.append({
            "gancho": g,
            "titulo": ganchos[g]["title"],
            "views_medio": round(avg_views),
            "likes_medio": round(avg_likes),
            "comentarios_medio": round(avg_comments),
            "score": round(score),
            "melhor_horario": round(hora_media) if hora_media is not None else None
        })

    return resultados, yt_horarios, ig_horarios

# =======================
# 🔹 Escolha inteligente
# =======================
def escolher_proximo_gancho(metadata, platform, ganchos):
    gancho_points = {}
    for meta in metadata.values():
        g = meta["gancho"]
        p = meta["points"][platform]
        gancho_points.setdefault(g, []).append(p)

    avg_gancho_points = {g: mean(lst) if lst else 0 for g in gancho_points}
    high = [g for g, avg in avg_gancho_points.items() if avg >= POINT_THRESHOLD]
    if not high:
        high = list(ganchos.keys())
    escolha = random.choice(high)
    return escolha

def escolher_horario(metadata, platform, state, horarios_data):
    hora_points = {}
    for meta in metadata.values():
        h = meta.get("hour")
        if h is not None:
            p = meta["points"][platform]
            hora_points.setdefault(h, []).append(p)

    avg_hora_points = {h: mean(lst) if lst else 0 for h in hora_points}
    high = [h for h, avg in avg_hora_points.items() if avg >= POINT_THRESHOLD]
    if not high:
        high = POST_HOURS

    escolha_h = random.choice(high)

    # Garante espaçamento
    ultimo_post = state.get(f"ultimo_post_{platform}")
    agora = datetime.datetime.utcnow()
    if ultimo_post:
        ultima_data = datetime.datetime.fromisoformat(ultimo_post)
        delta_horas = (agora - ultima_data).total_seconds() / 3600
        if delta_horas < MIN_HOURS_BETWEEN_POSTS:
            proximo = ultima_data + datetime.timedelta(hours=MIN_HOURS_BETWEEN_POSTS)
            escolha_h = proximo.hour

    return escolha_h

# =======================
# 🔹 Gerar gráfico
# =======================
def gerar_grafico(resultados):
    nomes = [r["gancho"] for r in resultados]
    scores = [r["score"] for r in resultados]
    plt.bar(nomes, scores)
    plt.title("Desempenho dos Ganchos (Score Total)")
    plt.xlabel("Gancho")
    plt.ylabel("Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "grafico_ganchos.png"))
    plt.close()

# =======================
# 🔹 Execução principal
# =======================
def main():
    metrics = load_json(METRICS_PATH)
    metadata = load_json(METADATA_PATH)
    ganchos = load_json(GANCHO_PATH)
    state = load_json(STATE_PATH)

    resultados, yt_horarios, ig_horarios = analisar_desempenho(metrics, metadata, ganchos)
    resultados.sort(key=lambda x: x["score"], reverse=True)

    gerar_grafico(resultados)
    save_json(resultados, RESULT_PATH)

    # Escolher para YouTube
    proximo_gancho_yt = escolher_proximo_gancho(metadata, "youtube", ganchos)
    proximo_horario_yt = escolher_horario(metadata, "youtube", state, yt_horarios)

    # Escolher para Instagram
    proximo_gancho_ig = escolher_proximo_gancho(metadata, "instagram", ganchos)
    proximo_horario_ig = escolher_horario(metadata, "instagram", state, ig_horarios)

    # Atualizar state
    state["proximo_gancho_yt"] = proximo_gancho_yt
    state["proximo_horario_yt"] = proximo_horario_yt
    state["proximo_gancho_ig"] = proximo_gancho_ig
    state["proximo_horario_ig"] = proximo_horario_ig
    save_json(state, STATE_PATH)

    print("✅ Análise concluída!")
    print(f"🏆 Próximo gancho YT: {proximo_gancho_yt}, Horário: {proximo_horario_yt}:00")
    print(f"🏆 Próximo gancho IG: {proximo_gancho_ig}, Horário: {proximo_horario_ig}:00")

    # Commit automático
    try:
        subprocess.run(["git", "add", METADATA_PATH, RESULT_PATH, STATE_PATH], check=True)
        subprocess.run(["git", "commit", "-m", "📈 Atualiza análise, pontos e recomendações"], check=False)
        subprocess.run(["git", "push"], check=False)
    except Exception as e:
        print("⚠️ Erro ao fazer commit automático:", e)

if __name__ == "__main__":
    main()