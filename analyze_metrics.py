import os
import json
import random
from datetime import datetime
import subprocess
import matplotlib.pyplot as plt

# ========================================
# 📁 Diretórios e nomes de arquivo
# ========================================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

RESULT_PATH = os.path.join(DATA_DIR, f"analise_ganchos - {timestamp()}.json")
STATE_PATH = os.path.join(DATA_DIR, f"state - {timestamp()}.json")
GRAPH_PATH = os.path.join(DATA_DIR, f"grafico_ganchos - {timestamp()}.png")

# ========================================
# 🔧 Funções utilitárias
# ========================================
def latest_metrics_file():
    """Pega o arquivo de métricas mais recente dentro da pasta data/"""
    files = [f for f in os.listdir(DATA_DIR) if f.startswith("metrics") and f.endswith(".json")]
    if not files:
        raise FileNotFoundError("Nenhum arquivo de métricas encontrado em /data.")
    files.sort(reverse=True)
    return os.path.join(DATA_DIR, files[0])

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========================================
# 📊 Análise de desempenho
# ========================================
def analisar_desempenho(metrics):
    print("📈 Analisando desempenho dos ganchos...")
    resultados = {}
    videos = metrics.get("youtube", {}).get("videos", [])
    posts = metrics.get("instagram", {}).get("posts", [])

    for item in videos + posts:
        gancho = item.get("gancho", "desconhecido")
        score = item.get("views", 0) + item.get("likes", 0) * 2 + item.get("comments", 0) * 3
        resultados.setdefault(gancho, []).append(score)

    analise_final = []
    for gancho, scores in resultados.items():
        media = sum(scores) / len(scores)
        analise_final.append({
            "gancho": gancho,
            "pontuacao_media": round(media, 2),
            "quantidade_posts": len(scores),
            "melhor_horario_estimado": random.choice(["12:00", "15:00", "18:00"])
        })

    analise_final.sort(key=lambda x: x["pontuacao_media"], reverse=True)
    return analise_final

def gerar_grafico(resultados):
    nomes = [r["gancho"] for r in resultados]
    scores = [r["pontuacao_media"] for r in resultados]

    plt.bar(nomes, scores, color="skyblue")
    plt.title("Desempenho Médio por Gancho")
    plt.xlabel("Gancho")
    plt.ylabel("Pontuação Média")
    plt.tight_layout()
    plt.savefig(GRAPH_PATH)
    plt.close()
    print(f"📊 Gráfico salvo em {GRAPH_PATH}")

# ========================================
# 🚀 Execução principal
# ========================================
def main():
    metrics_path = latest_metrics_file()
    metrics = load_json(metrics_path)

    resultados = analisar_desempenho(metrics)
    save_json(resultados, RESULT_PATH)

    state = {
        "executado_em": datetime.utcnow().isoformat(),
        "melhor_gancho": resultados[0]["gancho"],
        "melhor_horario": resultados[0]["melhor_horario_estimado"]
    }
    save_json(state, STATE_PATH)

    gerar_grafico(resultados)

    print("✅ Análise concluída!")
    print(f"🏆 Próximo gancho sugerido: {state['melhor_gancho']}")
    print(f"🕐 Melhor horário estimado: {state['melhor_horario']}")
    print(f"📊 Resultados salvos em {RESULT_PATH}")
    print(f"📁 Estado salvo em {STATE_PATH}")

    # Commit automático
    try:
        subprocess.run(["git", "add", RESULT_PATH, STATE_PATH, GRAPH_PATH], check=True)
        subprocess.run(["git", "commit", "-m", "📈 Atualiza análise e próxima recomendação"], check=False)
        subprocess.run(["git", "push"], check=False)
    except Exception as e:
        print("⚠️ Erro ao fazer commit automático:", e)

if __name__ == "__main__":
    main()
