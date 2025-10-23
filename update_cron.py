# update_cron.py
import os
import sys
import re

WORKFLOWS_DIR = ".github/workflows"
YOUTUBE_YML = os.path.join(WORKFLOWS_DIR, "post_Y.yml")
INSTAGRAM_YML = os.path.join(WORKFLOWS_DIR, "post_I.yml")

def gerar_cron(horario):
    """Gera expressão cron para o horário informado (formato HH:MM)."""
    hora = int(horario.split(":")[0])
    return f"0 {hora} * * *"

def atualizar_yaml(path, horario):
    """Substitui a seção de agendamento do YAML pelo novo horário."""
    with open(path, "r", encoding="utf-8") as f:
        conteudo = f.read()

    cron = gerar_cron(horario)
    novo_schedule = f"  schedule:\n    - cron: \"{cron}\"\n  workflow_dispatch:"

    conteudo_novo = re.sub(
        r"on:\n\s*schedule:.*?workflow_dispatch:",
        f"on:\n{novo_schedule}",
        conteudo,
        flags=re.S
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(conteudo_novo)

    print(f"🕒 Atualizado: {path} -> {horario}")

def main():
    if len(sys.argv) < 3:
        raise ValueError("Uso: python update_cron.py <horario_youtube> <horario_instagram>")
    
    horario_youtube = sys.argv[1]  # e.g., "20:00"
    horario_instagram = sys.argv[2]  # e.g., "14:00"

    atualizar_yaml(YOUTUBE_YML, horario_youtube)
    atualizar_yaml(INSTAGRAM_YML, horario_instagram)

    print("✅ Cron atualizado com sucesso.")

if __name__ == "__main__":
    main()