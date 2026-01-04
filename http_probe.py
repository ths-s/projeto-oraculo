import requests
import sys

url = sys.argv[1]

print("🧪 Testando acesso HTTP:", url)

r = requests.get(url, stream=True, timeout=10)

print("Status:", r.status_code)
print("Content-Type:", r.headers.get("Content-Type"))
print("Content-Length:", r.headers.get("Content-Length"))

if r.status_code != 200:
    raise RuntimeError("❌ URL inacessível")

if "video" not in (r.headers.get("Content-Type") or ""):
    raise RuntimeError("❌ Não é vídeo")

print("✅ URL válida para Instagram")
