import subprocess
import time
import re
import sys

def start_ngrok(port=8000, timeout=15):
    proc = subprocess.Popen(
        ["ngrok", "http", str(port), "--log=stdout"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start = time.time()
    public_url = None

    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if not line:
            continue

        print("📡 ngrok:", line.strip())

        match = re.search(r"https://[a-z0-9\-]+\.ngrok(-free)?\.app", line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        proc.terminate()
        raise RuntimeError("❌ Não foi possível capturar URL pública do ngrok via stdout")

    return proc, public_url


if __name__ == "__main__":
    p, url = start_ngrok()
    print("🌍 NGROK_URL=", url)
    time.sleep(30)
    p.terminate()
