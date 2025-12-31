import http.server
import socketserver
import os

PORT = 8000
# Muda o diretório de trabalho para onde o vídeo foi baixado
os.chdir("/tmp")

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Servindo na porta {PORT}")
    httpd.serve_forever()