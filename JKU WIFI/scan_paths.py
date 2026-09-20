import urllib.request
import urllib.error

base = "http://chals.tisc26.ctf.sg:21515"
paths = [
    "/",
    "/robots.txt",
    "/.well-known/jwks.json",
    "/.well-known/openid-configuration",
    "/jwks.json",
    "/keys",
    "/keys.json",
    "/api",
    "/api/v2",
    "/api/v2/admin",
    "/api/v2/admin/login",
    "/api/v2/admin/status",
    "/api/v2/admin/config",
    "/api/v2/admin/backup",
    "/api/v2/admin/firmware",
    "/api/v2/keys",
    "/api/v2/jwks.json",
    "/api/v2/.well-known/jwks.json",
    "/firmware",
    "/backup",
    "/config",
    "/console",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/swagger.json",
    "/metrics",
    "/health",
    "/status",
    "/info",
    "/static",
    "/static/js/main.js",
    "/static/style.css"
]

for p in paths:
    url = base + p
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"[{resp.status}] {p} (len={len(resp.read())})")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[{e.code}] {p} -> {e.read()[:100]}")
        else:
            # 404
            pass
    except Exception as e:
        print(f"[ERR] {p} -> {e}")
