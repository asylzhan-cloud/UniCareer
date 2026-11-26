"""UniCareer educational backend. Python standard library only.
Runs locally; not production-grade authentication or multi-user authorization.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, sqlite3, threading, os, time

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'unicareer.sqlite3'
HTML = ROOT / 'public' / 'index.html'
LOCK = threading.RLock()
MAX_BODY = 2_000_000

def connection():
    c = sqlite3.connect(DB, timeout=10)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, updated_at INTEGER NOT NULL)')
    return c

class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, mime='application/json; charset=utf-8'):
        data = body if isinstance(body, bytes) else body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            return self.send(200, HTML.read_bytes(), 'text/html; charset=utf-8')
        if self.path == '/api/health':
            return self.send(200, json.dumps({'ok': True, 'database': 'sqlite3'}))
        if self.path == '/api/state':
            with LOCK, connection() as c:
                row = c.execute('SELECT payload FROM app_state WHERE id=1').fetchone()
            return self.send(200, row[0] if row else '{}')
        return self.send(404, '{"error":"Not found"}')

    def do_PUT(self):
        if self.path != '/api/state':
            return self.send(404, '{"error":"Not found"}')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 2 <= size <= MAX_BODY:
                return self.send(413, '{"error":"Invalid payload size"}')
            value = json.loads(self.rfile.read(size))
            if not isinstance(value, dict) or not all(isinstance(value.get(k), t) for k, t in [('users',list),('jobs',list),('applications',list),('employment',list),('resume',dict)]):
                return self.send(400, '{"error":"Invalid application state"}')
            value['current'] = None  # Current browser user is never shared as global session
            value.pop('selectedJob', None)
            value.pop('selectedCandidate', None)
            with LOCK, connection() as c:
                c.execute('INSERT INTO app_state (id,payload,updated_at) VALUES (1,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at', (json.dumps(value,ensure_ascii=False), int(time.time())))
            return self.send(200, '{"ok":true}')
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return self.send(400, '{"error":"Invalid JSON"}')
        except Exception as e:
            print('Database error:', e)
            return self.send(500, '{"error":"Database error"}')

    def log_message(self, fmt, *args):
        print('[UniCareer]', fmt % args)

if __name__ == '__main__':
    host = os.environ.get('UNICAREER_HOST', '127.0.0.1')
    port = int(os.environ.get('UNICAREER_PORT', '8000'))
    with connection(): pass
    server = ThreadingHTTPServer((host, port), Handler)
    print(f'UniCareer server: http://{host}:{port}')
    print('Stop with Ctrl+C')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
