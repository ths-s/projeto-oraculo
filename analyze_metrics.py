#!/usr/bin/env python3
# generate_results.py

import os
import json
from datetime import datetime
import random

# ======================
# 📂 Caminhos e Configuração
# ======================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Função auxiliar para gerar horário formatado
def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# ======================
# 🔍 Simulação de Análise
# ======================
def executar_analise():
    # Simula uma análise de métricas com valores aleatórios
    metricas = {
        "engajamento": random.randint(40, 100),
        "alcance": random.randint(1000, 5000),
        "cliques": random.randint(20, 300),
        "conversoes": random.randint(1, 15),
    }

    # Gera recomendações baseadas nesses números
    recomendacoes = []
    if metricas["engajamento"] < 60:
        recomendacoes.append("Use ganchos mais fortes no início do post.")
    if metricas["cliques"] < 100:
        recomendacoes.append("Adicione uma chamada para ação (CTA) mais clara.")
    if metricas["alcance"] > 3000:
        recomendacoes.append("Republique o conteúdo em outros horários.")
    if not recomendacoes:
        recomendacoes.append("Continue com essa linha de conteúdo!")

    return {
        "timestamp": datetime.now().isoformat(),
        "metricas": metricas,
        "recomendacoes": recomendacoes
    }

# ======================
# 💾 Execução principal
# ======================
def main():
    resultados = []

    # Executa duas análises (duas postagens no dia)
    for i in range(2):
        analise = executar_analise()
        resultados.append(analise)

    # Monta o resultado final
    resultado_final = {
        "gerado_em": datetime.now().isoformat(),
        "quantidade_posts": 2,
        "dados": resultados
    }

    # Nomeia o arquivo com data e hora
    file_name = f"result_{timestamp()}.json"
    file_path = os.path.join(DATA_DIR, file_name)

    # Salva o arquivo
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, ensure_ascii=False, indent=4)

    # Exibe o resultado no console (para GitHub Actions capturar)
    print(json.dumps(resultado_final, ensure_ascii=False, indent=4))

    print(f"\n✅ Resultado salvo em: {file_path}")

# ======================
# ▶ Execução
# ======================
if __name__ == "__main__":
    main()
