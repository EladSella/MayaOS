import os
import http.server
import socketserver
import urllib.parse
from pathlib import Path

PORT = int(os.environ.get("PORT", 8000))
BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"
RECORDS_DIR = BASE_DIR / "memory" / "medical_records"

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/schedule'):
            import subprocess
            import json
            import sys
            
            integration_path = BASE_DIR / "integrations" / "icon_fitness" / "get_schedule.py"
            try:
                result = subprocess.run(
                    [sys.executable, str(integration_path), "--day", "Today"],
                    capture_output=True, text=True, check=True
                )
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(result.stdout.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return
            
        if self.path.startswith('/api/meditation'):
            import subprocess
            import json
            import sys
            
            integration_path = BASE_DIR / "integrations" / "youtube" / "get_meditation.py"
            try:
                result = subprocess.run(
                    [sys.executable, str(integration_path)],
                    capture_output=True, text=True, check=True
                )
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(result.stdout.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        return super().do_GET()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_POST(self):
        if self.path == '/upload':
            raw_file_name = self.headers.get('X-File-Name', 'uploaded_file.bin')
            file_name = urllib.parse.unquote(raw_file_name)
            file_name = os.path.basename(file_name)
            
            # Security: Whitelist allowed file extensions
            allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
            ext = os.path.splitext(file_name)[1].lower()
            if ext not in allowed_extensions:
                self.send_response(403) # Forbidden
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "File type not allowed"}')
                return
            
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length > 0:
                file_data = self.rfile.read(content_length)
                RECORDS_DIR.mkdir(parents=True, exist_ok=True)
                file_path = RECORDS_DIR / file_name
                
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"MayaOS UI Server running on http://localhost:{PORT}")
        httpd.serve_forever()
