#!/usr/bin/env python3
import json
import os
from openai import OpenAI

# ======================
# ⚙️ Configurações
# ======================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

METRICS_PATH = "data/metrics.json"
GANCHOS_PATH = "gancho_data.json"
OUTPUT_PATH = os.path.join(DATA_DIR, "analise_gancho.json")

# 🧠 Configurar cliente DeepSeek
client = OpenAI(
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

# ======================
# 📖 Ler dados
# ======================
def load_json(path):
    if not os.path.exists(path):
        print(f"⚠️ Arquivo não encontrado: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

metrics = load_json(METRICS_PATH)
ganchos = load_json(GANCHOS_PATH)

# ======================
# 🧩 Construir prompt
# ======================
prompt = f"""
Você é um analista de conteúdo para redes sociais.

Com base nas métricas abaixo, escolha **qual gancho** (entre os disponíveis) deve ser usado no próximo vídeo.

Regras:
- Analise engajamento e retenção de público.
- Escolha o gancho mais provável de gerar melhores resultados.
- Retorne a resposta em JSON com os campos: "gancho_escolhido", "motivo", "pontuacao_prevista".

📊 Métricas:
{json.dumps(metrics, ensure_ascii=False, indent=2)}

🎯 Ganchos disponíveis:
{json.dumps(ganchos, ensure_ascii=False, indent=2)}
"""

# ======================
# 🤖 Chamada à API DeepSeek
# ======================
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "Você é um assistente especialista em análise de performance digital."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.4,
)

# ======================
# 💾 Salvar resultado
# ======================
resultado = response.choices[0].message.content

try:
    data = json.loads(resultado)
except json.JSONDecodeError:
    print("⚠️ Resposta não estava em JSON puro. Salvando como texto bruto.")
    data = {"raw_output": resultado}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Análise concluída e salva em:", OUTPUT_PATH)
