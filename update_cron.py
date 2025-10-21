#!/usr/bin/env python3
import re
import os
import datetime

DATA_DIR = "data"
HORARIO_PATH = os.path.join(DATA_DIR, "melhor_horario.txt")

# Caminhos dos workflows
WORKFLOWS = {
    "YouTube": ".github/workflows/upload_youtube.yml",
    "Instagram": ".github/workflows/upload_instagram.yml"
}

def load_horario():
    if not os.path.exists(HORARIO_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {HORARIO_PATH}")
    with open(HORARIO_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def horario_para_cron(horario):
    """Converte '20:00' para formato cron: '0 23 * * *' (ajustando fuso UTC)"""
    hora, minuto = map(int, horario.split(":"))

    # GitHub Actions usa UTC, então ajustar (ex: Brasil = UTC-3)
    hora_utc = (hora + 3) % 24
    return f"{minuto} {hora_utc} * * *"

def atualizar_cron(path, cron_novo):
    with open(path, "r", encoding="utf-8") as f:
        conteudo = f.read()

    conteudo_novo = re.sub(
        r"cron:\s*['\"]?([^\n'\"]+)['\"]?",
        f"cron: '{cron_novo}'",
        conteudo
    )

    if conteudo != conteudo_novo:
        with open(path, "w", encoding="utf-8") as f:
            f.write(conteudo_novo)
        print(f"✅ Atualizado cron em {path} → {cron_novo}")
    else:
        print(f"ℹ️ Nenhuma alteração necessária em {path}")

def main():
    print("🕒 Atualizando horários de postagem...")
    horario = load_horario()
    cron = horario_para_cron(horario)
    for nome, path in WORKFLOWS.items():
        atualizar_cron(path, cron)
    print("✅ Atualização concluída!")

if __name__ == "__main__":
    main()
