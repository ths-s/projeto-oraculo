import os
import json
import random
from datetime import datetime, timedelta

# ========================================
# 📁 Diretórios e nomes de arquivo
# ========================================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

SCHEDULE_PATH = os.path.join(DATA_DIR, "schedule.json")
GANCHOS_PATH = os.path.join(DATA_DIR, "gancho_ranking.json")

# ========================================
# ⚙️ Funções auxiliares
# ========================================
def gerar_horarios():
    """Gera dois horários com no mínimo 12h de diferença."""
    h1 = random.randint(6, 10)  # primeiro horário entre 6h e 10h
    h2 = h1 + 12
    if h2 >= 24:
        h2 -= 24
    return [f"{h1:02d}:00", f"{h2:02d}:00"]

def escolher_ganchos(gancho_data, qtd=2):
    """Escolhe ganchos diferentes aleatoriamente."""
    ganchos = list(gancho_data.values())
    return random.sample(ganchos, min(qtd, len(ganchos)))

def carregar_ganchos():
    """Carrega o arquivo de ranking de ganchos."""
    if not os.path.exists(GANCHOS_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {GANCHOS_PATH}")
    with open(GANCHOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_schedule(schedule):
    """Salva o cronograma gerado em JSON."""
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

# ========================================
# 🚀 Execução principal
# ========================================
def main():
    print("📊 Gerando novos horários e ganchos...")
    ganchos_data = carregar_ganchos()

    schedule = {
        "youtube": {
            "horarios": gerar_horarios(),
            "ganchos": escolher_ganchos(ganchos_data)
        },
        "instagram": {
            "horarios": gerar_horarios(),
            "ganchos": escolher_ganchos(ganchos_data)
        },
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    salvar_schedule(schedule)
    print(json.dumps(schedule, ensure_ascii=False, indent=2))
    print("✅ Arquivo salvo em:", SCHEDULE_PATH)

if __name__ == "__main__":
    main()
