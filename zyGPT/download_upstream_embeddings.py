import concurrent.futures
import pathlib
import time
import requests

URL='https://huggingface.co/Qwen/Qwen3-1.7B/resolve/main/model-00001-of-00002.safetensors'
OUT=pathlib.Path('upstream_embeddings.bin')
SIZE=622365512
CHUNK=16*1024*1024
start_time=time.monotonic()
with OUT.open('wb') as f:
    f.truncate(SIZE)
def part(start):
    end=min(start+CHUNK,SIZE)
    r=requests.get(URL+f'?download=true&range_start={start}',headers={'Range':f'bytes={start}-{end-1}'},timeout=90)
    r.raise_for_status()
    assert r.status_code==206,(r.status_code,len(r.content))
    assert len(r.content)==end-start,(r.headers.get('Content-Range'),len(r.content),end-start)
    with OUT.open('r+b') as f:
        f.seek(start)
        f.write(r.content)
    return end-start
total=0
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for f in concurrent.futures.as_completed([pool.submit(part,i) for i in range(0,SIZE,CHUNK)]):
        total+=f.result()
        print(f'{total/1e6:.0f}/{SIZE/1e6:.0f} MB upstream embeddings',flush=True)
print('Done',round(time.monotonic()-start_time,1),flush=True)