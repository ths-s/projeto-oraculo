#!/usr/bin/env python3
# update_cron.py
import sys
import os
import re

# ======================
# 📂 Caminhos
# ======================
WORKFLOW_DIR = ".github/workflows"
FILES = {
    "youtube": os.path.join(WORKFLOW_DIR, "post_Y.yml"),
    "instagram": os.path.join(WORKFLOW_DIR, "post_I.yml"),
}
HORARIO_PATH = "data/melhor_horario.txt"

# ======================
# 🕒 Utilitários
# ======================
def load_horario():
    if len(sys.argv) > 1:
        return sys.argv[1]
    if not os.path.exists(HORARIO_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {HORARIO_PATH}")
    with open(HORARIO_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def atualizar_cron(path, horario):
    if not os.path.exists(path):
        print(f"⚠️ Arquivo não encontrado: {path} — criando novo.")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()

    with open(path, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Substitui a linha do cron
    novo_conteudo, n = re.subn(
        r'cron:\s*"[^"]+"',
        f'cron: "0 {int(horario.split(":")[0])} * * *"',
        conteudo,
    )

    if n == 0:
        # Se não existia linha de cron, adiciona
        novo_conteudo += f'\n  schedule:\n    - cron: "0 {int(horario.split(":")[0])} * * *"\n'

    with open(path, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)
    print(f"🕒 Atualizado: {path} → {horario}")

# ======================
# 🚀 Execução
# ======================
def main():
    print("🕒 Atualizando horários de postagem...")
    horario = load_horario()

    for nome, path in FILES.items():
        atualizar_cron(path, horario)

    print("✅ Horários atualizados com sucesso!")

if __name__ == "__main__":
    main()
