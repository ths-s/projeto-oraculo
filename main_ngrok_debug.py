import subprocess
import time
import os

print("🌐 Iniciando servidor HTTP")
server = subprocess.Popen(
    ["python", "serve_video.py"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(3)

print("🌐 Iniciando ngrok (modo stdout)")
ngrok_proc = subprocess.Popen(
    ["python", "ngrok_runner.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

public_url = None

for line in ngrok_proc.stdout:
    print(line.strip())
    if line.startswith("🌍 NGROK_URL="):
        public_url = line.split("=", 1)[1].strip()
        break

if not public_url:
    raise RuntimeError("❌ NGROK_URL não obtida")

video_name = os.listdir("/tmp")[0]
video_url = f"{public_url}/{video_name}"

print("🎬 VIDEO_URL:", video_url)

print("🧪 Testando URL final")
subprocess.run(["python", "http_probe.py", video_url], check=True)

print("✅ Infraestrutura OK")

server.terminate()
ngrok_proc.terminate()
