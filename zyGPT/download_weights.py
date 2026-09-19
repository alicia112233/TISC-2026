import concurrent.futures
import pathlib
import time

import requests

URL = 'http://chals.tisc26.ctf.sg:14172/model/model.safetensors'
OUT = pathlib.Path('model/model.safetensors')
OUT.parent.mkdir(exist_ok=True)
SIZE = 3441185608
CHUNK = 16 * 1024 * 1024
started = time.monotonic()

def part(start):
    end = min(start + CHUNK, SIZE)
    for attempt in range(4):
        try:
            r = requests.get(URL, headers={'Range': f'bytes={start}-{end-1}'}, timeout=60)
            r.raise_for_status()
            assert r.status_code == 206
            assert len(r.content) == end-start, (len(r.content), end-start)
            with OUT.open('r+b') as f:
                f.seek(start)
                f.write(r.content)
            return end-start
        except Exception:
            if attempt == 3:
                raise
    return 0

with OUT.open('wb') as f:
    f.truncate(SIZE)
total = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(part, s) for s in range(0,SIZE,CHUNK)]
    for n,f in enumerate(concurrent.futures.as_completed(futures),1):
        total += f.result()
        if n % 8 == 0 or total == SIZE:
            print(f'{total/1e9:.2f}/{SIZE/1e9:.2f} GB ({total/(time.monotonic()-started)/1e6:.1f} MB/s)',flush=True)
print('Download complete',flush=True)