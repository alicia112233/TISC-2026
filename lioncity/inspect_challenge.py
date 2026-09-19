import json
from pathlib import Path
from collections import deque
import requests

BASE = 'http://chals.tisc26.ctf.sg:57161'

def route(grid):
    stamps = {(x,y): 1 << i for i,(x,y) in enumerate((x,y) for y,row in enumerate(grid) for x,c in enumerate(row) if c in 'ABC')}
    start = next((x,y,0) for y,row in enumerate(grid) for x,c in enumerate(row) if c == 'S')
    todo = deque([(start, '')])
    seen = {start}
    while todo:
        (x,y,mask), path = todo.popleft()
        if grid[y][x] == 'E' and mask == (1 << len(stamps)) - 1:
            return path
        for d,dx,dy in [('U',0,-1),('D',0,1),('L',-1,0),('R',1,0)]:
            nx,ny = x+dx,y+dy
            if not (0 <= ny < len(grid) and 0 <= nx < len(grid[ny])) or grid[ny][nx] == '#':
                continue
            state = (nx,ny,mask | stamps.get((nx,ny),0))
            if state not in seen:
                seen.add(state)
                todo.append((state,path+d))
    raise ValueError('No route')

if __name__ == '__main__':
    start = json.loads(Path('start.json').read_text())
    traces = [route(level['grid']) for level in start['levels']]
    for level, trace in zip(start['levels'], traces):
        print(level['name'], len(trace), trace)
    response = requests.post(BASE+'/api/harbour/stamp',json={'session': start['session'], 'traces':traces},timeout=30)
    Path('stamp.json').write_text(response.text)
    print('STAMP:',response.status_code,response.text)
    targets = {
        'tide-format.json': '/api/harbour/tide?format=wasm',
        'singa_legacy.wasm': '/engine/singa_legacy.wasm',
        'supertree.png': start['levels'][1]['assets']['C'],
        'chicken-rice.png': start['levels'][0]['assets']['C'],
        'purple-orchid.png': start['levels'][2]['assets']['C'],
    }
    for name,url in targets.items():
        response = requests.get(BASE+url,timeout=30)
        Path(name).write_bytes(response.content)
        print(name,response.status_code,len(response.content))
        if name.endswith('.json'): print(response.text)
