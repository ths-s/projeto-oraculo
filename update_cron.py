import os
import json
import re

DATA_DIR = "data"
SCHEDULE_PATH = os.path.join(DATA_DIR, "schedule.json")

WORKFLOWS_DIR = ".github/workflows"
YOUTUBE_YML = os.path.join(WORKFLOWS_DIR, "post_Y.yml")
INSTAGRAM_YML = os.path.join(WORKFLOWS_DIR, "post_I.yml")

def carregar_schedule():
    if not os.path.exists(SCHEDULE_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {SCHEDULE_PATH}")
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def gerar_cron(horarios):
    """Gera expressões cron para os horários informados."""
    return [f"0 {int(h.split(':')[0])} * * *" for h in horarios]

def atualizar_yaml(path, horarios):
    """Substitui a seção de agendamento do YAML pelos novos horários."""
    with open(path, "r", encoding="utf-8") as f:
        conteudo = f.read()

    blocos_cron = "\n".join([f"    - cron: \"{c}\"" for c in gerar_cron(horarios)])
    novo_schedule = f"  schedule:\n{blocos_cron}\n  workflow_dispatch:"

    conteudo_novo = re.sub(r"on:\n\s*schedule:.*?workflow_dispatch:", f"on:\n{novo_schedule}", conteudo, flags=re.S)

    with open(path, "w", encoding="utf-8") as f:
        f.write(conteudo_novo)

    print(f"🕒 Atualizado: {path} -> {horarios}")

def main():
    schedule = carregar_schedule()

    atualizar_yaml(YOUTUBE_YML, schedule["youtube"]["horarios"])
    atualizar_yaml(INSTAGRAM_YML, schedule["instagram"]["horarios"])

    print("✅ Cron atualizado com sucesso.")

if __name__ == "__main__":
    main()
