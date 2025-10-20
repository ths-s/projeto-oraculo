#!/usr/bin/env python3
# move_posted_video.py
import os
import shutil
import json
import re
import time
from pathlib import Path

# --- CONFIG ---
BASE_DIR = Path(__file__).resolve().parent
PENDING_DIR = (BASE_DIR / "videos" / "pending")
POSTED_DIR = (BASE_DIR / "videos" / "posted")
STATE_PATH = (BASE_DIR / "data" / "state.json")
LOG_PATH = (BASE_DIR / "data" / "move_log.txt")

VIDEO_EXTS = ('.mp4', '.mov', '.avi', '.mkv', '.webm')

# --- HELPERS ---
def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_state():
    if not STATE_PATH.exists():
        return {"posted_videos": []}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Erro ao ler state.json: {e}")
        return {"posted_videos": []}

def save_state(state):
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=4, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log(f"Erro ao salvar state.json: {e}")

def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

def make_dst_unique(dst_path: Path):
    """Se já existir, cria um sufixo _1, _2 ..."""
    if not dst_path.exists():
        return dst_path
    stem = dst_path.stem
    suffix = dst_path.suffix
    parent = dst_path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def file_info(p: Path):
    try:
        st = p.stat()
        perms = oct(st.st_mode)[-3:]
        return f"{p} | size={st.st_size} | perms={perms}"
    except Exception as e:
        return f"{p} | erro obtendo stat: {e}"

# --- MOVE LOGIC ---
def move_first_unposted_video():
    log(f"Base dir: {BASE_DIR}")
    log(f"Pending dir: {PENDING_DIR.resolve()}")
    log(f"Posted dir: {POSTED_DIR.resolve()}")
    log(f"State path: {STATE_PATH.resolve()}")

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    POSTED_DIR.mkdir(parents=True, exist_ok=True)

    state = load_state()
    posted = set(state.get("posted_videos", []))

    # debug: listar arquivos antes
    all_pending = [f for f in PENDING_DIR.iterdir() if f.is_file()]
    log(f"Arquivos em pending (total {len(all_pending)}):")
    for p in sorted(all_pending, key=lambda x: natural_sort_key(x.name)):
        log("  - " + file_info(p))

    # filtrar vídeos válidos e não postados
    pending = [
        f.name for f in all_pending
        if f.suffix.lower() in VIDEO_EXTS and f.name not in posted
    ]
    pending = sorted(pending, key=natural_sort_key)

    if not pending:
        log("⚠️ Nenhum novo vídeo para mover (todos já postados ou não há vídeos).")
        return

    video = pending[0]
    src = PENDING_DIR / video
    dst = POSTED_DIR / video

    log(f"Selecionado para mover: {src} -> {dst}")

    if not src.exists():
        log(f"❌ Arquivo não encontrado em src: {src}")
        return

    # verificar permissões de escrita/leitura
    try:
        readable = os.access(src, os.R_OK)
        writable_dest = os.access(POSTED_DIR, os.W_OK)
        log(f"Permissões: src_readable={readable}, posted_dir_writable={writable_dest}")
    except Exception as e:
        log(f"Erro ao checar permissões: {e}")

    # garantir que destino seja único para evitar sobrescrever
    final_dst = make_dst_unique(dst)

    # tentativas de mover: rename -> shutil.move -> copy2 + remove
    moved = False
    errors = []

    try:
        # tentativa 1: rename (rápido em mesma partição)
        try:
            src.rename(final_dst)
            moved = True
            log("move via Path.rename() bem-sucedido.")
        except Exception as e:
            errors.append(f"rename falhou: {e}")
            # tentativa 2: shutil.move
            try:
                shutil.move(str(src), str(final_dst))
                moved = True
                log("move via shutil.move() bem-sucedido.")
            except Exception as e2:
                errors.append(f"shutil.move falhou: {e2}")
                # tentativa 3: copy + remove
                try:
                    shutil.copy2(str(src), str(final_dst))
                    # verificação antes de remover
                    if final_dst.exists():
                        src.unlink()
                        moved = True
                        log("copy2 + unlink bem-sucedido.")
                    else:
                        errors.append("copy2 criou o arquivo mas final_dst não existe após copy.")
                except Exception as e3:
                    errors.append(f"copy2/unlink falhou: {e3}")
    except Exception as e_outer:
        errors.append(f"Erro inesperado no bloco de movimento: {e_outer}")

    # relatório final
    if moved and final_dst.exists() and not src.exists():
        log(f"✅ Vídeo movido com sucesso: {final_dst.name}")
        posted.add(final_dst.name)
        state["posted_videos"] = sorted(list(posted))
        save_state(state)
    else:
        log(f"❌ Falha ao mover o vídeo: {video}")
        for e in errors:
            log("   erro: " + str(e))
        # listar destino e origem para diagnóstico
        log("Estado final (após tentativas):")
        log("  src exists: " + str(src.exists()))
        log("  dst exists: " + str(final_dst.exists()))
        if src.exists():
            log("  src info: " + file_info(src))
        if final_dst.exists():
            log("  dst info: " + file_info(final_dst))
        log("Sugestões: verifique se o arquivo não está aberto, se o antivírus não está bloqueando e se você tem permissão de escrita na pasta 'posted'.")

if __name__ == "__main__":
    move_first_unposted_video()
