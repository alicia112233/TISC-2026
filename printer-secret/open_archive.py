"""Download the challenge archive and read its entries without executing them."""
from pathlib import Path
import zipfile
import requests

URL = 'https://printer-secret.chals.tisc26.ctf.sg/Fn8u92fhuiWAfeAfGu23dy.zip'
PASSWORD = b'sut0roberi1-fure!b4a_*=^'
archive = Path(__file__).resolve().parent / 'secret-archive.zip'
if not archive.exists():
    response = requests.get(URL, timeout=30)
    print('HTTP:', response.status_code, 'Bytes:', len(response.content), flush=True)
    response.raise_for_status()
    archive.write_bytes(response.content)

with zipfile.ZipFile(archive) as z:
    for entry in z.infolist():
        print('Entry:', entry.filename, 'Size:', entry.file_size,
              'Encryption:', bool(entry.flag_bits & 1), 'Method:', entry.compress_type)
        try:
            data = z.read(entry, pwd=PASSWORD)
            print(repr(data[:16000]))
        except (RuntimeError, NotImplementedError) as exc:
            print(type(exc).__name__ + ':', exc)
