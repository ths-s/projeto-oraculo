import http.server
import socketserver
import os

PORT = 8000
VIDEO_DIR = "/tmp"

os.chdir(VIDEO_DIR)

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🌍 Servindo vídeos em http://localhost:{PORT}")
    httpd.serve_forever()
