# Task image_to_model de Tripo: moto Suzuki GN125 desde la referencia generada.
# (La tool MCP image_to_3d hace esto mismo pero su request se queda sin timeout;
#  este script corre en background y hace el polling con calma.)
import httpx, time, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
for line in open('.env'):
    if line.startswith('TRIPO_API_KEY='):
        KEY = line.strip().split('=', 1)[1]
H = {'Authorization': f'Bearer {KEY}'}

def upload(path):
    with open(path, 'rb') as f:
        r = httpx.post('https://api.tripo3d.ai/v2/openapi/upload/sts',
                       headers=H, files={'file': (os.path.basename(path), f, 'image/png')}, timeout=180)
    r.raise_for_status()
    return r.json()['data']['image_token']

print('subiendo referencia...', flush=True)
tok = upload(r'assets/images/2e83cb196f05f056.png')

task = {
    'type': 'image_to_model',
    'file': {'type': 'png', 'file_token': tok},
    'pbr': True,
    'face_limit': 18000,
}
r = httpx.post('https://api.tripo3d.ai/v2/openapi/task', headers=H, json=task, timeout=60)
print('crear task:', r.status_code, r.text[:200], flush=True)
tid = r.json()['data']['task_id']
print('task_id:', tid, flush=True)

t0 = time.time()
while True:
    time.sleep(6)
    d = httpx.get(f'https://api.tripo3d.ai/v2/openapi/task/{tid}', headers=H, timeout=60).json()['data']
    st = d.get('status')
    print(f'  {int(time.time()-t0)}s status={st} progreso={d.get("progress")}', flush=True)
    if st == 'success':
        out = d.get('output', {})
        url = out.get('pbr_model') or out.get('model') or (d.get('result', {}) or {}).get('pbr_model', {})
        if isinstance(url, dict): url = url.get('url')
        print('descargando', str(url)[:90], flush=True)
        glb = httpx.get(url, timeout=300, follow_redirects=True).content
        dest = r'assets/models/moto_gn125.glb'
        open(dest, 'wb').write(glb)
        print('GUARDADO', dest, len(glb), 'bytes', flush=True)
        break
    if st in ('failed', 'cancelled', 'banned', 'expired'):
        print('FALLO:', json.dumps(d)[:400], flush=True)
        sys.exit(1)
    if time.time() - t0 > 900:
        print('TIMEOUT esperando task', tid, flush=True)
        sys.exit(2)
