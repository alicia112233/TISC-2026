"""Submit a bot only when explicitly run; token stays in a local environment variable."""
from pathlib import Path
import argparse
import os
import sys
import urllib.error
import urllib.request

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a raw bot to the CtS API. Does not log the submission token.")
    parser.add_argument("program", type=Path)
    args = parser.parse_args()
    token = os.environ.get("CTS_SUBMISSION_TOKEN", "").strip()
    if not token:
        parser.error("Set CTS_SUBMISSION_TOKEN locally using the token from the challenge card.")
    payload = args.program.read_bytes()
    if args.program.suffix.lower() == ".hex":
        try:
            program = bytes.fromhex(payload.decode("ascii"))
        except (UnicodeError, ValueError):
            parser.error("Input is not valid hexadecimal text.")
        content_type = "text/plain"
    else:
        program = payload
        content_type = "application/octet-stream"
    if not 4 <= len(program) <= 8192:
        parser.error("Decoded program must be 4 to 8192 bytes.")
    request = urllib.request.Request("https://cts.chals.tisc26.ctf.sg/api/v1/submissions", data=payload,
                                     headers={"Authorization": "Bearer " + token, "Content-Type": content_type}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            print(response.read().decode("utf-8", errors="replace").replace(token, "[REDACTED]"))
    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8", errors="replace").replace(token, "[REDACTED]")
        print(f"HTTP {error.code}: {message}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as error:
        print(f"Submission failed: {str(error.reason).replace(token, '[REDACTED]')}", file=sys.stderr)
        sys.exit(1)
