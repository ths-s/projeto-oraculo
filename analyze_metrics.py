#!/usr/bin/env python3
# analyze_metrics.py
import os
import json
import random
import subprocess
from datetime import datetime
from statistics import mean
from collections import defaultdict, Counter

# ======================
# 📂 Caminhos
# ======================
DATA_DIR = "data"
METRICS_PATH = os.path.join(DATA_DIR, "metrics.json")
GANCHOS_PATH = "gancho_data.json"

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

# Agora o nome do arquivo contém a data e hora da geração
RECOMENDACOES_PATH = os.path.join(DATA_DIR, f"recomendacoes - {timestamp()}.json")
RESUMO_PATH = os.path.join(DATA_DIR, f"analise_gancho - {timestamp()}.json")
HORARIO_PATH = os.path.join(DATA_DIR, "melhor_horario.txt")

# ======================
# 🔧 Utilitários
# ======================
def load_json(path):
    if not os.path.exists(path):
        print(f"⚠️ Arquivo não encontrado: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
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

# ======================
# 📊 Análises
# ======================
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

# ======================
# 🧠 Geração das recomendações
# ======================
def gerar_recomendacoes(metrics):
    recomendacoes = {}
    print("📊 Iniciando análise...")

    yt_videos = metrics.get("youtube", {}).get("videos", [])
    ig_posts = metrics.get("instagram", {}).get("posts", [])

    yt_horas, yt_titulos = calcular_scores_youtube(yt_videos)
    ig_horas, ig_captions = calcular_scores_instagram(ig_posts)

    recomendacoes["youtube"] = {
        "melhores_horarios": melhores_horarios(yt_horas),
        "melhores_ganchos": analisar_ganchos(yt_titulos)
    }
    recomendacoes["instagram"] = {
        "melhores_horarios": melhores_horarios(ig_horas),
        "melhores_ganchos": analisar_ganchos(ig_captions)
    }

    return recomendacoes

# ======================
# 🎯 Escolher ganchos reais
# ======================
def escolher_ganchos(recomendacoes, ganchos_data):
    ganchos_disponiveis = list(ganchos_data.keys())
    if not ganchos_disponiveis:
        raise ValueError("Nenhum gancho encontrado em gancho_data.json")

    yt_gancho = random.choice(ganchos_disponiveis)
    ig_gancho = random.choice(ganchos_disponiveis)

    horarios = (
        recomendacoes.get("youtube", {}).get("melhores_horarios", [])
        + recomendacoes.get("instagram", {}).get("melhores_horarios", [])
    )
    melhor_horario = max(horarios) if horarios else random.choice([11, 14, 17, 19, 21])

    return {
        "gancho_youtube": ganchos_data[yt_gancho],
        "gancho_instagram": ganchos_data[ig_gancho],
        "melhor_horario_postagem": f"{melhor_horario:02d}:00",
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
#!/usr/bin/env python3
# analyze_metrics.py
import os
import json
import random
import subprocess
from datetime import datetime
from statistics import mean
from collections import defaultdict, Counter

# ======================
# 📂 Caminhos
# ======================
DATA_DIR = "data"
METRICS_PATH = os.path.join(DATA_DIR, "metrics.json")
GANCHOS_PATH = "gancho_data.json"

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

# Agora o nome do arquivo contém a data e hora da geração
RECOMENDACOES_PATH = os.path.join(DATA_DIR, f"recomendacoes - {timestamp()}.json")
RESUMO_PATH = os.path.join(DATA_DIR, f"analise_gancho - {timestamp()}.json")
HORARIO_PATH = os.path.join(DATA_DIR, "melhor_horario.txt")

# ======================
# 🔧 Utilitários
# ======================
def load_json(path):
    if not os.path.exists(path):
        print(f"⚠️ Arquivo não encontrado: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
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

# ======================
# 📊 Análises
# ======================
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

# ======================
# 🧠 Geração das recomendações
# ======================
def gerar_recomendacoes(metrics):
    recomendacoes = {}
    print("📊 Iniciando análise...")

    yt_videos = metrics.get("youtube", {}).get("videos", [])
    ig_posts = metrics.get("instagram", {}).get("posts", [])

    yt_horas, yt_titulos = calcular_scores_youtube(yt_videos)
    ig_horas, ig_captions = calcular_scores_instagram(ig_posts)

    recomendacoes["youtube"] = {
        "melhores_horarios": melhores_horarios(yt_horas),
        "melhores_ganchos": analisar_ganchos(yt_titulos)
    }
    recomendacoes["instagram"] = {
        "melhores_horarios": melhores_horarios(ig_horas),
        "melhores_ganchos": analisar_ganchos(ig_captions)
    }

    return recomendacoes

# ======================
# 🎯 Escolher ganchos reais
# ======================
def escolher_ganchos(recomendacoes, ganchos_data):
    ganchos_disponiveis = list(ganchos_data.keys())
    if not ganchos_disponiveis:
        raise ValueError("Nenhum gancho encontrado em gancho_data.json")

    yt_gancho = random.choice(ganchos_disponiveis)
    ig_gancho = random.choice(ganchos_disponiveis)

    horarios = (
        recomendacoes.get("youtube", {}).get("melhores_horarios", [])
        + recomendacoes.get("instagram", {}).get("melhores_horarios", [])
    )
    melhor_horario = max(horarios) if horarios else random.choice([11, 14, 17, 19, 21])

    return {
        "gancho_youtube": ganchos_data[yt_gancho],
        "gancho_instagram": ganchos_data[ig_gancho],
        "melhor_horario_postagem": f"{melhor_horario:02d}:00",
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ======================
# 💾 Execução e salvamento
# ======================
def main():
    metrics = load_json(METRICS_PATH)
    ganchos_data = load_json(GANCHOS_PATH)

    # Gera recomendações completas e escolhe os melhores ganchos
    recomendacoes = gerar_recomendacoes(metrics)
    resumo = escolher_ganchos(recomendacoes, ganchos_data)

    os.makedirs(DATA_DIR, exist_ok=True)

    # Gera dois horários (exemplo: 20:00 e 12:00)
    horario_youtube = resumo.get("melhor_horario_postagem", "20:00")
    horario_instagram = "12:00" if horario_youtube != "12:00" else "20:00"

    # Garante formato de data/hora legível
    data_geracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Monta o dicionário final que será salvo em recomendacoes.json
    recomendacoes_completas = {
        "gancho_youtube": resumo.get("gancho_youtube", {}),
        "gancho_instagram": resumo.get("gancho_instagram", {}),
        "melhor_horario_youtube": horario_youtube,
        "melhor_horario_instagram": horario_instagram,
        "data_geracao": data_geracao
    }

    # Caminhos para salvar
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    RECOMENDACOES_FINAL_PATH = os.path.join(DATA_DIR, f"recomendacoes - {timestamp}.json")
    RECOMENDACOES_FIXO_PATH = os.path.join(DATA_DIR, "recomendacoes.json")

    # Salva todos os arquivos normalmente
    with open(RECOMENDACOES_PATH, "w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, ensure_ascii=False, indent=2)
    with open(RESUMO_PATH, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    with open(HORARIO_PATH, "w", encoding="utf-8") as f:
        f.write(horario_youtube)

    # 🔹 Novo: salva recomendacoes.json e a versão com timestamp
    with open(RECOMENDACOES_FINAL_PATH, "w", encoding="utf-8") as f:
        json.dump(recomendacoes_completas, f, ensure_ascii=False, indent=2)
    with open(RECOMENDACOES_FIXO_PATH, "w", encoding="utf-8") as f:
        json.dump(recomendacoes_completas, f, ensure_ascii=False, indent=2)

    print("✅ Análise concluída!")
    print(json.dumps(recomendacoes_completas, ensure_ascii=False, indent=2))

    # ✅ Chama update_cron.py e passa os dois horários (YouTube e Instagram)
    subprocess.run(["python3", "update_cron.py", horario_youtube, horario_instagram], check=False)


if __name__ == "__main__":
    main()
