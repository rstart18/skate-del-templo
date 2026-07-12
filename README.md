# game-assets-mcp

Servidor **MCP (FastMCP)** que expone un pipeline encadenable para generar assets 3D
de un juego web **Three.js estilo Tony Hawk's Pro Skater**. El cliente **Fable 5**
orquesta la cadena; este servidor solo ejecuta cada eslabón y devuelve **rutas**
(nunca binarios ni base64).

```
generate_image ──▶ image_to_3d ──▶ optimize_mesh ──▶ update_manifest
                            └────▶ auto_rig (fallback de rigging)

merge_animations   ◀── .glb exportados MANUALMENTE desde Mixamo
```

---

## Instalación

```bash
cd game-assets-mcp
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Credenciales (solo por variables de entorno)

Copia `.env.example` a `.env` y rellena tus claves **reales**:

```
GEMINI_API_KEY=...
TRIPO_API_KEY=...
```

> `.env` está en `.gitignore`. **Nunca** se hardcodean claves en el código.
> Al ejecutar el servidor asegúrate de que esas variables estén en el entorno
> (Claude Desktop las inyecta desde el bloque `env`, ver abajo).

---

## Conectar a un cliente MCP (Claude Desktop / Fable 5)

Añade esto a la config MCP del cliente (o copia `claude_desktop_config.json`).
El `command` apunta al **Python del venv** (donde están las dependencias); las
claves las carga el propio servidor desde `.env`, así que no hace falta bloque `env`:

```json
{
  "mcpServers": {
    "game-assets-mcp": {
      "command": "C:\\Users\\MSI\\Documents\\projects\\game-assets-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\MSI\\Documents\\projects\\game-assets-mcp\\server.py"]
    }
  }
}
```

> Si prefieres no depender de `.env`, puedes añadir un bloque `"env": { "GEMINI_API_KEY": "...", "TRIPO_API_KEY": "..." }` — las variables del cliente tienen prioridad sobre `.env`.

### ¿Qué modelo orquesta la cadena?

El MCP server es **agnóstico al modelo** — funciona idéntico con cualquier cliente. El modelo (Fable 5, Opus 4.8, etc.) se elige en el cliente, no en el server.

**Recomendado: Opus 4.8** ($5/$25 por MTok). La orquestación del pipeline es tool-chaining mecánico (pasar rutas entre tools); no requiere un modelo frontera. El costo dominante son los **créditos de Gemini/Tripo**, no los tokens del orquestador — así que el sobreprecio de Fable 5 ($10/$50, ~2× más) no se justifica aquí.

Reserva **Fable 5** solo para razonamiento genuinamente difícil (diseñar props de un nivel completo, presupuestos de polígonos por escena, depurar esqueletos que no encajan en `merge_animations`).

## Ver el juego (integración de assets)

El juego Three.js vive en [`game/skate.html`](game/skate.html). Como carga los `.glb`
por `fetch`, **no funciona con doble-clic** (`file://` bloquea el fetch por CORS).
Sírvelo por HTTP local:

```bash
cd game-assets-mcp
python -m http.server 8000
# abre http://localhost:8000/game/skate.html
```

El juego lee `game/assets_manifest.json` y coloca cada `.glb` según la tabla
`PLACEMENT` del HTML (`pos`, `rot`, `scale`; el loader **auto-aterriza** cada
modelo en el suelo). Para añadir un prop nuevo: genéralo con el pipeline →
`update_manifest` con un `object_id` → añade ese `object_id` a `PLACEMENT` con su
posición. La geometría procedural del juego sigue intacta; los assets de IA se
**añaden** encima.

> **Poly-budget de props texturizados:** contrólalo con el `face_limit` de Tripo en
> `image_to_3d` (produce low-poly CON textura en un paso). `optimize_mesh` NO decima
> mallas con textura (trimesh perdería las UVs y quedarían negras): las preserva.

## ⚠️ Timeout del cliente MCP en tareas largas

`image_to_3d` (y a veces `optimize_mesh`) pueden tardar más que el timeout por
defecto del cliente MCP (~60s), mientras Tripo genera el modelo (~hasta 120s). El
cliente reporta "Request timed out" **pero el servidor termina el trabajo y guarda
el `.glb`**. Gracias a la caché por hash, la solución es simple: **vuelve a llamar
`image_to_3d` con la misma imagen** — la segunda vez devuelve la ruta cacheada al
instante, sin re-gastar créditos.

## Smoke test

Para revalidar tras cualquier cambio o al montar el proyecto en otra máquina:

```bash
python smoke_test.py          # local, NO gasta créditos (env, manifest, optimize_mesh)
python smoke_test.py --full   # además Gemini + Tripo reales (SÍ gasta créditos)
```

---

## Tools MCP

| Tool | Qué hace | Devuelve |
|------|----------|----------|
| `generate_image(prompt)` | Gemini con salida de imagen. Fuerza **fondo neutro + sujeto centrado** (mejora el image-to-3D). Cachea por hash del prompt. | ruta del `.png` |
| `image_to_3d(image_path, face_limit=5000)` | Tripo `image_to_model` (upload → task → polling). Texturizado + PBR. Cachea por hash de la imagen. `face_limit` ∈ [48, 20000]. | ruta del `.glb` |
| `auto_rig(glb_path)` | Auto Rigging de Tripo (**fallback**; el rigging real se hace en Mixamo). | ruta del `.glb` riggeado |
| `optimize_mesh(glb_path, target_faces=3000)` | Decima con trimesh (`simplify_quadric_decimation`). **Si el modelo trae rig/animaciones, NO decima** para no romper skin weights ni clips. | ruta del `.glb` optimizado |
| `merge_animations(glb_paths, output_id)` | Fusiona varios `.glb` de Mixamo en **uno solo**: malla una vez + todos los clips. Listo para `AnimationMixer`. | ruta del `.glb` final |
| `update_manifest(object_id, model_path)` | Escribe `game/assets_manifest.json`. | confirmación corta |
| `read_manifest()` | Devuelve el manifest actual. | JSON del manifest |

---

## Flujo de trabajo completo

### A) Objetos del escenario (rampas, obstáculos, props)

1. **`generate_image`** — describe el objeto → PNG con fondo neutro.
2. **`image_to_3d`** — PNG → `.glb` texturizado (`assets/models/`).
3. **`optimize_mesh`** — decima a ~3000 caras (`assets/models_optimized/`). Crítico para que Three.js corra fluido: las mallas de IA vienen high-poly.
4. **`update_manifest`** — registra el objeto para que el juego lo cargue.

### B) El personaje (skater) — incluye paso MANUAL de Mixamo

1. **`generate_image`** — genera el skater en pose T/A, fondo neutro.
2. **`image_to_3d`** — `.glb` del skater.
3. **`optimize_mesh`** — **decima el skater ANTES de riggear** (la optimización sobre un modelo ya riggeado se salta la decimación para no romper el rig).
4. **🔴 PASO MANUAL EN MIXAMO** (lo hace la persona, fuera del MCP):
   - Mixamo (Adobe) **no tiene API pública**. Subes el `.glb`/`.fbx` del skater a [mixamo.com](https://www.mixamo.com).
   - Mixamo lo auto-riggea.
   - Descargas cada animación como `.glb` separado: `idle`, `skateboarding`, `jumping`, etc.
   - Dejas esos `.glb` en una carpeta acordada.
   - > ⚠️ Este paso es manual. El servidor **no inventa ni asume** estos archivos. Si el asistente necesita saber cuántas/cuáles animaciones traes, sus nombres exactos, la carpeta o el formato de export, **debe detenerse y preguntar** antes de continuar.
5. **`merge_animations`** — pasa la lista de `.glb` de Mixamo → un único `.glb` con la malla una sola vez + todos los clips empaquetados (`assets/models_final/`).
6. **`update_manifest`** — registra el personaje final.

> **`auto_rig`** existe como *fallback* por si en algún momento no se puede usar Mixamo, pero el rigging principal del personaje es Mixamo.

---

## Estructura de carpetas

```
game-assets-mcp/
├── server.py
├── requirements.txt
├── .gitignore
├── .env.example
├── claude_desktop_config.json
├── README.md
├── assets/
│   ├── images/            # PNGs de Gemini            (nombre = hash del prompt)
│   ├── models/            # .glb crudos de Tripo      (image_to_3d)
│   ├── models_rigged/     # .glb riggeados            (auto_rig, fallback)
│   ├── models_optimized/  # .glb decimados            (optimize_mesh)
│   └── models_final/      # .glb malla+animaciones    (merge_animations)
└── game/
    └── assets_manifest.json   # {"objects": {"<id>": {"model": "<path>"}}}
```

---

## Idempotencia y caché

Cada etapa usa **hashes como clave de caché** para no regenerar ni quemar créditos:

- `generate_image`: hash del prompt enriquecido → si el PNG existe, no llama a Gemini.
- `image_to_3d`: hash del archivo de imagen → si el `.glb` existe, no llama a Tripo.
- `auto_rig`: hash del `.glb` de entrada.

Para forzar una regeneración, borra el archivo cacheado correspondiente.

---

## Cargar el resultado en Three.js

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const manifest = await (await fetch('/game/assets_manifest.json')).json();
const loader = new GLTFLoader();
const gltf = await loader.loadAsync(manifest.objects['skater'].model);

const mixer = new THREE.AnimationMixer(gltf.scene);
const clips = Object.fromEntries(gltf.animations.map(c => [c.name, c]));
mixer.clipAction(clips['idle']).play();   // idle / skateboarding / jumping ...
```

---

## Notas

- `face_limit` en Tripo va de **48 a 20000** (el servidor hace clamp).
- Los errores de red/API (`failed`, `banned`, timeout) se devuelven como **mensaje legible**, no como excepción cruda.
- Los binarios generados están en `.gitignore` (se regeneran desde el pipeline).
