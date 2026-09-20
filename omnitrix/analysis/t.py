import socket, struct, subprocess, os, time
BIN=os.path.expanduser('~/omni/omnitrix')
env={**os.environ,'OMNITRIX_BIND':'127.0.0.1:19393','RUST_LOG':'info'}
env.pop('OMNITRIX_MASTER_KEY',None)
srv=subprocess.Popen([BIN],env=env,stdout=open('/tmp/t_srv.log','wb'),stderr=subprocess.STDOUT)
time.sleep(1.5)
try:
    s=socket.socket(); s.connect(('127.0.0.1',19393)); s.settimeout(0.6)
    s.send(b'OMNI'+bytes([1,0])+struct.pack('>H',0x51)+struct.pack('>Q',0)+struct.pack('>H',0))
    time.sleep(0.3)
    try: r=s.recv(4096)
    except: r=b'(timeout)'
    open('/tmp/t.out','w').write('resp='+repr(r)+'\n')
except Exception as e:
    open('/tmp/t.out','w').write('EXC='+repr(e)+'\n')
srv.terminate()
print('OK')
