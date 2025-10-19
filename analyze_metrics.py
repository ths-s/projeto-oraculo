import json
import datetime
import random
from statistics import mean
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
WEIGHTS = {
    "views": 1,
    "likes": 5,
    "comments": 10
}

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
    analise = {}

    # YouTube
    for v in metrics["youtube"]["videos"]:
        for file, meta in metadata.items():
            if meta["youtube_id"] == v["video_id"]:
                g = meta["gancho"]
                analise.setdefault(g, {"views": [], "likes": [], "comments": [], "horarios": []})
                analise[g]["views"].append(v["views"])
                analise[g]["likes"].append(v["likes"])
                analise[g]["comments"].append(v["comments"])
                hora = datetime.datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00")).hour
                analise[g]["horarios"].append(hora)

    # Instagram
    for p in metrics["instagram"]["posts"]:
        for file, meta in metadata.items():
            if meta["instagram_id"] == p["id"]:
                g = meta["gancho"]
                analise.setdefault(g, {"views": [], "likes": [], "comments": [], "horarios": []})
                analise[g]["likes"].append(p["likes"])
                analise[g]["comments"].append(p["comments"])
                hora = datetime.datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00")).hour
                analise[g]["horarios"].append(hora)

    # Calcular médias
    resultados = []
    for g, d in analise.items():
        avg_views = mean(d["views"]) if d["views"] else 0
        avg_likes = mean(d["likes"]) if d["likes"] else 0
        avg_comments = mean(d["comments"]) if d["comments"] else 0
        score = avg_views * WEIGHTS["views"] + avg_likes * WEIGHTS["likes"] + avg_comments * WEIGHTS["comments"]
        hora_media = mean(d["horarios"]) if d["horarios"] else None

        resultados.append({
            "gancho": g,
            "titulo": ganchos[g]["title"],
            "views_medio": round(avg_views),
            "likes_medio": round(avg_likes),
            "comentarios_medio": round(avg_comments),
            "score": round(score),
            "melhor_horario": round(hora_media) if hora_media is not None else None
        })

    return resultados

# =======================
# 🔹 Escolha inteligente
# =======================
def escolher_proximo_gancho(resultados, state):
    # Histórico de pontuação
    gancho_scores = {r["gancho"]: r["score"] for r in resultados}
    total = sum(gancho_scores.values()) or 1

    # Distribuição probabilística proporcional ao desempenho
    pesos = {g: (score / total) for g, score in gancho_scores.items()}

    escolha = random.choices(list(pesos.keys()), weights=list(pesos.values()), k=1)[0]

    state["ultimo_gancho"] = escolha
    return escolha, pesos

def escolher_horario(resultados, state):
    ultimo_post = state.get("ultimo_post")
    agora = datetime.datetime.utcnow()

    # Garante espaçamento de 12h
    if ultimo_post:
        ultima_data = datetime.datetime.fromisoformat(ultimo_post)
        delta_horas = (agora - ultima_data).total_seconds() / 3600
        if delta_horas < MIN_HOURS_BETWEEN_POSTS:
            proximo = ultima_data + datetime.timedelta(hours=MIN_HOURS_BETWEEN_POSTS)
            return proximo.hour

    # Busca horário mais comum entre os top ganchos
    top3 = sorted(resultados, key=lambda x: x["score"], reverse=True)[:3]
    horas = [r["melhor_horario"] for r in top3 if r["melhor_horario"]]
    if horas:
        return round(mean(horas))
    else:
        return random.choice(POST_HOURS)

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

    resultados = analisar_desempenho(metrics, metadata, ganchos)
    resultados.sort(key=lambda x: x["score"], reverse=True)

    gerar_grafico(resultados)
    save_json(resultados, RESULT_PATH)

    proximo_gancho, pesos = escolher_proximo_gancho(resultados, state)
    proximo_horario = escolher_horario(resultados, state)

    # Atualiza histórico
    state["ultimo_post"] = datetime.datetime.utcnow().isoformat()
    state["pesos_ganchos"] = pesos
    state["proximo_gancho"] = proximo_gancho
    state["proximo_horario"] = proximo_horario
    save_json(state, STATE_PATH)

    print("✅ Análise concluída!")
    print(f"🏆 Próximo gancho sugerido: {proximo_gancho} — {ganchos[proximo_gancho]['title']}")
    print(f"🕐 Melhor horário estimado: {proximo_horario}:00")
    print(f"📊 Resultados salvos em {RESULT_PATH}")
    print(f"📁 Estado salvo em {STATE_PATH}")

    # 🔹 Commit automático (para manter o histórico de análises)
    try:
        subprocess.run(["git", "add", "data/analise_ganchos.json", "data/state.json"], check=True)
        subprocess.run(["git", "commit", "-m", "📈 Atualiza análise e próxima recomendação"], check=False)
        subprocess.run(["git", "push"], check=False)
    except Exception as e:
        print("⚠️ Erro ao fazer commit automático:", e)


if __name__ == "__main__":
    main()
