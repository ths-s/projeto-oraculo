#!/usr/bin/env python3
# analyze_metrics.py
import os
import json
from datetime import datetime
from statistics import mean
from collections import defaultdict, Counter

DATA_DIR = "data"
METRICS_PATH = os.path.join(DATA_DIR, "metrics.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "recomendacoes.json")
TXT_PATH = os.path.join(DATA_DIR, "recomendacoes.txt")

def load_metrics():
    if not os.path.exists(METRICS_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {METRICS_PATH}")
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def extrair_hora(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.hour
    except Exception:
        return None

def normalizar(valores):
    if not valores:
        return []
    min_v, max_v = min(valores), max(valores)
    if min_v == max_v:
        return [1.0 for _ in valores]
    return [(v - min_v) / (max_v - min_v) for v in valores]

def calcular_scores_youtube(videos):
    horas = defaultdict(list)
    titulos = []
    views = [v["views"] for v in videos]
    likes = [v["likes"] for v in videos]
    comments = [v["comments"] for v in videos]
    nv, nl, nc = normalizar(views), normalizar(likes), normalizar(comments)
    
    for v, sv, sl, sc in zip(videos, nv, nl, nc):
        hora = extrair_hora(v["publishedAt"])
        if hora is not None:
            score = (sv * 0.5 + sl * 0.3 + sc * 0.2)
            horas[hora].append(score)
            titulos.append((v["title"], score))
    return horas, titulos

def calcular_scores_instagram(posts):
    horas = defaultdict(list)
    captions = []
    likes = [p["likes"] for p in posts]
    comments = [p["comments"] for p in posts]
    nl, nc = normalizar(likes), normalizar(comments)

    for p, sl, sc in zip(posts, nl, nc):
        hora = extrair_hora(p["timestamp"])
        if hora is not None:
            score = (sl * 0.7 + sc * 0.3)
            horas[hora].append(score)
            if p.get("caption"):
                captions.append((p["caption"], score))
    return horas, captions

def melhores_horarios(horas_dict):
    medias = {h: mean(scores) for h, scores in horas_dict.items() if scores}
    top_horas = sorted(medias.items(), key=lambda x: x[1], reverse=True)
    if not top_horas:
        return []
    melhores = [top_horas[0][0]]
    for h, _ in top_horas[1:]:
        if abs(h - melhores[0]) >= 12:
            melhores.append(h)
            break
    if len(melhores) < 2 and len(top_horas) > 1:
        melhores.append(top_horas[1][0])
    return sorted(melhores)

def analisar_ganchos(textos):
    palavras = Counter()
    for t, s in textos:
        for w in t.lower().split():
            if len(w) > 3 and not w.startswith("#"):
                palavras[w] += s
    melhores = [p for p, _ in palavras.most_common(10)]
    return melhores

def gerar_recomendacoes(metrics):
    recomendacoes = {}
    print("📊 Iniciando análise local...")

    # YouTube
    yt_videos = metrics.get("youtube", {}).get("videos", [])
    yt_horas, yt_titulos = calcular_scores_youtube(yt_videos)
    yt_melhores_horarios = melhores_horarios(yt_horas)
    yt_ganchos = analisar_ganchos(yt_titulos)

    # Instagram
    ig_posts = metrics.get("instagram", {}).get("posts", [])
    ig_horas, ig_captions = calcular_scores_instagram(ig_posts)
    ig_melhores_horarios = melhores_horarios(ig_horas)
    ig_ganchos = analisar_ganchos(ig_captions)

    recomendacoes["youtube"] = {
        "melhores_horarios": yt_melhores_horarios,
        "melhores_ganchos": yt_ganchos[:5],
        "ganchos_para_testar": yt_ganchos[5:]
    }

    recomendacoes["instagram"] = {
        "melhores_horarios": ig_melhores_horarios,
        "melhores_ganchos": ig_ganchos[:5],
        "ganchos_para_testar": ig_ganchos[5:]
    }

    return recomendacoes

def salvar_recomendacoes(recomendacoes):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, indent=4, ensure_ascii=False)
    
    with open(TXT_PATH, "w", encoding="utf-8") as f:
        f.write("📅 RECOMENDAÇÕES DE POSTAGEM\n\n")
        for plataforma, dados in recomendacoes.items():
            f.write(f"=== {plataforma.upper()} ===\n")
            f.write(f"Melhores horários (2x/dia, 12h+): {', '.join(map(str, dados['melhores_horarios']))}h\n")
            f.write(f"Melhores ganchos:\n- " + "\n- ".join(dados["melhores_ganchos"]) + "\n")
            f.write(f"Ganchos para testar:\n- " + "\n- ".join(dados["ganchos_para_testar"]) + "\n\n")
    print(f"✅ Recomendação salva em {OUTPUT_PATH} e {TXT_PATH}")

def main():
    metrics = load_metrics()
    recomendacoes = gerar_recomendacoes(metrics)
    salvar_recomendacoes(recomendacoes)

if __name__ == "__main__":
    main()
