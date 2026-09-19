"""Save one public web page for passive challenge research."""
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

url, filename = sys.argv[1:3]
headers = {'User-Agent': 'Mozilla/5.0'}
if '--html' in sys.argv[3:]:
    headers['X-Return-Format'] = 'html'
response = requests.get(url, timeout=40, headers=headers)
print(response.status_code, response.url, response.headers.get('content-type'), len(response.content))
path = Path(filename).resolve()
root = Path(__file__).resolve().parent
if root not in path.parents:
    raise ValueError('Output must stay inside the challenge workspace')
path.write_bytes(response.content)
if response.headers.get('content-type', '').startswith('image/') or response.content.startswith((b'\xff\xd8\xff', b'\x89PNG')):
    pass
elif 'json' in response.headers.get('content-type', ''):
    print(response.text[:16000])
else:
    soup = BeautifulSoup(response.content, 'html.parser')
    for tag in soup(['script','style','nav','footer']): tag.decompose()
    print(soup.get_text(' ',strip=True)[:2500])
