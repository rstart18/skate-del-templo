// Construye dist/ (el paquete web del juego) desde game/ y assets/.
// Es la MISMA carpeta que se publica en surge y la que Capacitor empaqueta
// en las apps de Android/iOS (webDir en capacitor.config.json).
import { cpSync, mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');

// carpetas completas
const dirs = ['game'];
// assets individuales que el juego carga (mantener en sync con assets_manifest.json
// y con las rutas dentro de skate.html)
const files = [
  'assets/models/53914247a877a402.glb',        // tabla SNAIKYY
  'assets/models/7423743c79d9034c.glb',        // estatua de Santander
  'assets/models/templo_multiview.glb',        // templo hero (Tripo multiview v2)
  'assets/models_final/skater.glb',            // skater riggeado (4 clips)
  'assets/models_optimized/7c695f3c94f30352_opt.glb', // banca colonial
  'assets/textures/deck_snaikyy.png',
  'assets/textures/tex_piedra_colonial.jpg',
  'assets/textures/tex_yeso_cupula.jpg',
];

for (const d of dirs) cpSync(join(root, d), join(dist, d), { recursive: true });
for (const f of files) {
  mkdirSync(dirname(join(dist, f)), { recursive: true });
  cpSync(join(root, f), join(dist, f));
}

// index.html: redirige al juego (raiz del sitio y pantalla de arranque de la app)
const index = join(dist, 'index.html');
writeFileSync(index, `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=game/skate.html">
<script>location.replace('game/skate.html');</script>
<title>SKATE DEL TEMPLO</title>
</head>
<body style="background:#0b0d14;color:#fff;font-family:sans-serif;text-align:center;padding-top:20vh">
<p>Cargando SKATE DEL TEMPLO…</p>
<p><a href="game/skate.html" style="color:#ffd257">Entrar al juego</a></p>
</body>
</html>
`);

console.log('dist/ actualizado', existsSync(join(dist,'game/skate.html')) ? '(ok)' : '(FALTA skate.html!)');
