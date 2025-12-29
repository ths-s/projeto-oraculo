from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

PORT = 8000

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="videos/pending", **kwargs)

with TCPServer(("", PORT), Handler) as httpd:
    print(f"🌐 Servindo vídeos em http://localhost:{PORT}")
    httpd.serve_forever()
