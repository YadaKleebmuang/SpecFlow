import subprocess, re, time, urllib.request, json
import http.server, socketserver, threading

# Dummy server
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

httpd = socketserver.TCPServer(("127.0.0.1", 5005), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

cf = subprocess.Popen(["/Users/ploy/.local/bin/cloudflared", "tunnel", "--url", "http://127.0.0.1:5005"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
url = None
while True:
    line = cf.stdout.readline()
    if not line: break
    m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
    if m:
        url = m.group(0)
        break

if url:
    print("Found URL:", url)
    time.sleep(5)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SpecFlow-HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            print("Status:", resp.status)
            print("Body:", resp.read().decode())
    except Exception as e:
        print("Error:", e)
        if hasattr(e, "read"):
            print("Error body:", e.read().decode())
cf.kill()
httpd.shutdown()
