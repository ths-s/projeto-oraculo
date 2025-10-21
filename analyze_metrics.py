#!/usr/bin/env python3
# analyze_metrics_v3.py
import os
import json
import datetime
from statistics import mean
from collections import defaultdict
from openai import OpenAI

# ======================
# ⚙️ Configurações
# ======================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

METRICS_PATH = os.path.join(DATA_DIR, "metrics.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "recomendacoes.json")
TXT_PATH = os.path.join(DATA_DIR, "recomendacoes.txt")

client = OpenAI(api_key=os.getenv("NEW_OPEN_AI_KEY"))

# ======================
# 🔍 Funções utilitárias
# ======================
def carregar_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def salvar_txt(texto, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(texto)

# ======================
# 📊 Análise de métricas
# ======================
def analisar_metricas(metrics):
    plataformas = defaultdict(list)

    for item in metrics.get("posts", []):
        plataforma = item.get("platform", "desconhecida")
        horario = item.get("time", "00:00")
        desempenho = item.get("engagement", 0)
        titulo = item.get("title", "")
        plataformas[plataforma].append({
            "horario": horario,
            "desempenho": desempenho,
            "titulo": titulo
        })
    return plataformas

# ======================
# 🤖 Geração via IA
# ======================
def gerar_recomendacoes(plataformas):
    prompt = f"""
Analise os dados de desempenho abaixo e gere recomendações para postagem:

{json.dumps(plataformas, indent=2, ensure_ascii=False)}

Para cada plataforma (YouTube e Instagram), gere:
1. Dois melhores horários para postar (com pelo menos 12h de diferença).
2. Os 3 melhores ganchos baseados em desempenho (curtidas, engajamento, retenção etc).
3. O formato ideal de postagem (curto, médio, longo, reels, shorts, etc).

Retorne o resultado em JSON estruturado assim:
{{
  "instagram": {{
    "melhores_horarios": ["HH:MM", "HH:MM"],
    "melhores_ganchos": ["texto 1", "texto 2", "texto 3"]
  }},
  "youtube": {{
    "melhores_horarios": ["HH:MM", "HH:MM"],
    "melhores_ganchos": ["texto 1", "texto 2", "texto 3"]
  }}
}}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # ou o modelo da sua escolha
        messages=[
            {"role": "system", "content": "Você é um analista de dados e marketing digital."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    texto = response.choices[0].message.content.strip()

    try:
        return json.loads(texto)
    except:
        return {"erro": "Falha ao interpretar resposta da IA", "resposta_bruta": texto}

# ======================
# 🧩 Execução principal
# ======================
def main():
    print("📊 Iniciando análise de métricas...")

    metrics = carregar_json(METRICS_PATH)
    if not metrics:
        print(f"⚠️ Nenhum dado encontrado em {METRICS_PATH}")
        return

    plataformas = analisar_metricas(metrics)
    recomendacoes = gerar_recomendacoes(plataformas)

    salvar_json(recomendacoes, OUTPUT_PATH)

    texto = f"""
📅 RECOMENDAÇÕES DE POSTAGEM ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})

📸 Instagram:
  🕒 Melhores horários: {', '.join(recomendacoes.get('instagram', {}).get('melhores_horarios', []))}
  🎯 Melhores ganchos:
    - {chr(10).join(recomendacoes.get('instagram', {}).get('melhores_ganchos', []))}

🎥 YouTube:
  🕒 Melhores horários: {', '.join(recomendacoes.get('youtube', {}).get('melhores_horarios', []))}
  🎯 Melhores ganchos:
    - {chr(10).join(recomendacoes.get('youtube', {}).get('melhores_ganchos', []))}
    """

    salvar_txt(texto, TXT_PATH)
    print("✅ Análise concluída!")
    print(f"📁 Arquivos salvos em:\n - {OUTPUT_PATH}\n - {TXT_PATH}")

if __name__ == "__main__":
    main()
