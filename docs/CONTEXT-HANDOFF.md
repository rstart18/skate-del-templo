# Contexto del proyecto — SKATE DEL TEMPLO + game-assets-mcp

Handoff para continuar en otra sesión. Copia esto al iniciar.

## Qué es el proyecto

Dos partes que trabajan juntas:

1. **`game-assets-mcp/`** — servidor MCP (Python/FastMCP) que genera assets 3D con un
   pipeline encadenable: **Gemini (imagen) → Tripo (image-to-3D) → optimize → manifest**,
   más `merge_animations` para el personaje. Ya conectado a Claude Desktop y **funcionando**.
2. **`game-assets-mcp/game/skate.html`** — juego web **Three.js r128** (estilo Tony Hawk),
   ambientado en el Templo Histórico de Villa del Rosario. Todo procedural (cajas/cilindros)
   + assets de IA cargados por `GLTFLoader`. El original del usuario está en
   `C:\Users\MSI\Downloads\skate-templo-historico-v2.html` (intacto).

Cliente orquestador recomendado: **Opus 4.8** (la orquestación es tool-chaining; el gasto
real son créditos de Gemini/Tripo). Fable 5 solo para razonamiento difícil.

## Estado actual (lo que YA funciona)

- **Pipeline validado end-to-end.** Claves en `game-assets-mcp/.env` (GEMINI_API_KEY, TRIPO_API_KEY).
- **Prop de ejemplo:** `banca_plaza` (banca colonial) generada, texturizada, integrada al
  juego vía `game/assets_manifest.json` + tabla `PLACEMENT` en el HTML. Se ve bien.
- **Skater (personaje):** ¡animado y texturizado en el juego!
  - Imagen T-pose generada → `assets/models/9a0d0d90909a7330.glb` (base sin rig).
  - Usuario lo pasó por **Mixamo** (Blender 5.0 convierte glb↔fbx). Trajo la 1ª animación:
    `assets/animations/9a0d0d90909a7330_skateboarding@skateboarding.glb`.
  - `merge_animations([...], "skater")` → `assets/models_final/skater.glb` con clip `skateboarding`.
  - El juego lo carga con `AnimationMixer` (bloque "Skater RIGGEADO" en skate.html).

## Cómo correr / ver el juego

Local server obligatorio (los `.glb` se cargan por fetch; `file://` da CORS):
```
cd game-assets-mcp
python -m http.server 8000
# http://localhost:8000/game/skate.html  (Ctrl+Shift+R para saltar caché)
```
Controles: **W** rueda, A/D gira, Espacio ollie.

## Detalles técnicos clave (gotchas ya resueltos)

- **Escala del skater = por HUESOS, no geometría.** El `.glb` de Mixamo trae un desajuste
  de unidades: geometría ~1.7 pero esqueleto ~168. Como es `SkinnedMesh`, lo renderizado
  sigue al esqueleto. El loader mide `skeleton.bones` (no `setFromObject`). Escala final ~1.736,
  estatura 1.7 m, pies a Y=0.28 (sobre la tabla). Constantes: `SKATER_TARGET_H`, `SKATER_FOOT_Y`.
- **Textura del skater inyectada por código.** Mixamo pierde la textura; las UVs sobreviven,
  así que se re-inyectó el color al `skater.glb` con pygltflib (imagen extraída a
  `assets/textures/skater_0_Color_*.jpg`). Ya NO hay que rehacer Blender por textura.
- **`optimize_mesh` NO decima mallas con textura ni con rig** (trimesh perdería UVs/rig).
  El poly-budget de props se controla con el `face_limit` de Tripo en `image_to_3d`.
- **`merge_animations` nombra clips por ARCHIVO** (Mixamo pone "mixamo.com"). `skater@X.glb` → clip `X`.
- **Timeout del cliente MCP** en `image_to_3d`: si expira (~60s vs ~120s de Tripo), vuelve a
  llamarlo — la caché por hash devuelve el resultado al instante.
- **El capturador de screenshots del entorno se cuelga** con la escena cargada (rAF pausado
  en pestaña de fondo). Verificar por medición vía consola / que el usuario mande captura.

## Rumbo Android (decidido: Capacitor)
El juego se publicará en Android empaquetado con **Capacitor** (WebView, sin reescribir).
Ya hecho en `game/skate.html`:
- **Controles táctiles** (`#touchui`): botones que disparan `KeyboardEvent` sintéticos
  (reutilizan la lógica de teclado tal cual). Auto-detección por `pointer: coarse`;
  en desktop ocultos; `?touch=1` los fuerza para debug. Multi-touch verificado.
- **Viewport móvil** + botón fullscreen/landscape + bloqueo de scroll/zoom.
- **Three.js r128 y GLTFLoader locales** en `game/lib/` (ya no CDN — requisito
  Capacitor/offline).
Pendiente Android: probar en celular vía `http://<ip-pc>:8000/game/skate.html`,
luego `npx cap init` + `cap add android` (usuario instalará Node + Android Studio).

## Templo fiel (hecho) + captura de frames
- `buildTemplo()` en skate.html reconstruido **fiel a las ruinas reales** (refs en
  `C:\Users\MSI\Pictures\templo*.jpg`): portada de 3 arcos transitables (ExtrudeGeometry
  con huecos), torre+campanario con pináculos, cúpula blanca+linterna+cruz, contrafuertes,
  NAVE EN RUINAS a cielo abierto (muros irregulares, piso de ladrillo), palmeras reales
  procedurales. Colisiones por machones → se patina A TRAVÉS del arco y dentro de la nave.
- **Estatua de Santander** (pipeline): `assets/models/7423743c79d9034c.glb`, en manifest
  como `estatua_santander`, PLACEMENT pos [0,2.9,-45.8] rot [0,-PI/2,0] scale 2.2
  (sobre pedestal procedural).
- **Captura de frames del preview** (el preview_screenshot se cuelga): correr
  `tools/receiver.py <out.jpg>` en background y desde preview_eval hacer
  renderer.render + canvas.toDataURL + fetch POST a http://127.0.0.1:8123/. Ver frames
  en tools/frame*.jpg (gitignored).
- El fetch del manifest lleva cache-buster (`?t=Date.now()`); el skater.glb usa `?v=N`
  (const SKATER_GLB_V — subir al regenerar).

## Templo HERO (Tripo) — flujo foto→render→3D que SÍ funcionó
- `assets/images/templo_render3d.png`: render limpio generado con Gemini image-to-image
  (script directo con la foto real `C:\Users\MSI\Pictures\templo4.jpg` como входные —
  la tool MCP generate_image es solo texto; para img2img llamar la API con inline_data).
- Tripo face_limit 18000 → `assets/models/255d623117535c9d.glb` (17.9k tris, PBR).
- En manifest como `templo_historico`; PLACEMENT pos [0,1.2,-46.5] rot [0,-PI/2,0] scale 29
  (¡la rotación correcta se halló probando: el frente del modelo mira -X!).
- El arco quedó ENREJADO como el templo real → no se atraviesa (fiel). Entrada a las
  ruinas: brecha baja saltable en el muro ESTE de la nave (h 0.7 walkTop, z tz-10.1..-7.2).
- La torre procedural fue eliminada de buildTemplo; quedan: plataforma, nave en ruinas,
  escombros, pedestal+estatua, palmas. Colisiones del hero: bloque frontal + alas.
- FLY CAM: tecla V (WASD+mouse+Espacio/Q, Shift turbo). window.snap(px,py,pz,tx,ty,tz)
  posiciona cámara, renderiza y hace POST del frame al receiver (tools/receiver.py).

## TAREA ACTUAL (lo que falta ahora)

1. **Colocar el skater sobre la tabla (profundidad).** El personaje quedó desalineado del
   monopatín. Perillas nuevas en skate.html: `SKATER_OFFSET_X`, `SKATER_OFFSET_Z`.
   Ajustar en vivo por consola (`skaterModel.position.z += 0.3`) y fijar los valores.
2. **Orientación del skater** (`SKATER_MODEL_YAW`): confirmar que mira/rueda bien.
3. **Faltan 3 animaciones de Mixamo:** `jumping`, `crouch` (agacharse), `fall` (caerse).
   El usuario las traerá como `assets/animations/skater@<anim>.glb` (o similar con `@`).
   Cuando estén: `merge_animations` con las 4 (skateboarding PRIMERO = base con malla) →
   luego cablear en el juego el **cambio de clip por estado** (rodar→skateboarding,
   aire→jumping, cargar ollie→crouch, bail→fall), con crossfade en el `AnimationMixer`.

### ⚠️ Mixamo es paso MANUAL del usuario
No inventar archivos de animación. Si se necesita saber cuántas/cuáles animaciones, nombres,
carpeta o formato — **detenerse y preguntar**. Guía completa en `docs/mixamo-workflow.md`.

## Estructura de archivos relevante
```
game-assets-mcp/
├── server.py                       # 7 tools MCP
├── game/skate.html                 # el juego (bloque "Skater RIGGEADO" + loader de props)
├── game/assets_manifest.json       # {objects:{banca_plaza:{model}}}
├── assets/models/9a0d..glb         # skater base T-pose
├── assets/animations/*.glb         # animaciones de Mixamo (1 de 4)
├── assets/models_final/skater.glb  # skater fusionado (malla + clips + textura)
├── assets/textures/skater_0_Color_*.jpg
└── docs/mixamo-workflow.md         # guía Blender/Mixamo
```
