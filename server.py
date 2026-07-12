"""
game-assets-mcp
===============
Servidor MCP (FastMCP) que expone un pipeline encadenable de generación de
assets para un juego web Three.js estilo Tony Hawk's Pro Skater:

    generate_image  ->  image_to_3d  ->  optimize_mesh  ->  update_manifest
                                    \\-> auto_rig (fallback de rigging)

    merge_animations  (fusiona los .glb que exporto manualmente desde Mixamo)

Diseño:
- Auth SOLO por variables de entorno (GEMINI_API_KEY, TRIPO_API_KEY).
- Idempotencia: hashes como clave de caché en cada etapa (no quema créditos).
- Las tools devuelven SOLO rutas locales o confirmaciones cortas.
  NUNCA base64 ni binarios en el retorno.
- Errores de red/API se devuelven como mensaje legible, no como excepción cruda.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Rutas base (relativas a este archivo, para que funcione sin importar el CWD)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv() -> None:
    """Carga BASE_DIR/.env en os.environ (sin pisar variables ya definidas).

    Usa python-dotenv si está disponible; si no, hace un parseo mínimo.
    Así el archivo de secretos surte efecto tanto al correr `python server.py`
    como al lanzarlo desde Claude Desktop.
    """
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
        return
    except ImportError:
        pass
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()
IMAGES_DIR = BASE_DIR / "assets" / "images"
MODELS_DIR = BASE_DIR / "assets" / "models"
RIGGED_DIR = BASE_DIR / "assets" / "models_rigged"
OPTIMIZED_DIR = BASE_DIR / "assets" / "models_optimized"
FINAL_DIR = BASE_DIR / "assets" / "models_final"
GAME_DIR = BASE_DIR / "game"
MANIFEST_PATH = GAME_DIR / "assets_manifest.json"

for _d in (IMAGES_DIR, MODELS_DIR, RIGGED_DIR, OPTIMIZED_DIR, FINAL_DIR, GAME_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_IMAGE_MODEL}:generateContent"
)

TRIPO_HOST = "https://api.tripo3d.ai/v2/openapi"
TRIPO_UPLOAD_URL = f"{TRIPO_HOST}/upload/sts"
TRIPO_TASK_URL = f"{TRIPO_HOST}/task"

# Rango válido de face_limit según la doc de Tripo.
FACE_LIMIT_MIN = 48
FACE_LIMIT_MAX = 20000

# Parámetros de polling de Tripo.
POLL_INTERVAL_S = 2.0
POLL_TIMEOUT_S = 120.0

mcp = FastMCP("game-assets-mcp")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _rel(path: Path) -> str:
    """Ruta relativa al proyecto (más corta y estable para el manifest)."""
    try:
        return str(path.relative_to(BASE_DIR)).replace("\\", "/")
    except ValueError:
        return str(path)


def _env(key: str) -> str | None:
    val = os.environ.get(key)
    return val.strip() if val else None


# ---------------------------------------------------------------------------
# 1) generate_image
# ---------------------------------------------------------------------------
@mcp.tool()
def generate_image(prompt: str) -> str:
    """Genera un PNG con Gemini (fondo neutro, sujeto centrado) y devuelve la ruta local; cachea por hash del prompt."""
    api_key = _env("GEMINI_API_KEY")
    if not api_key:
        return "Error: falta GEMINI_API_KEY en el entorno."

    # El fondo blanco/neutro y el sujeto centrado mejoran mucho el image-to-3D.
    enriched = (
        f"{prompt}. Single subject, centered in frame, full object visible, "
        "isolated on a plain solid white neutral background, even studio lighting, "
        "no shadows on background, no text, no watermark, product shot style."
    )

    prompt_hash = _hash_text(enriched)
    out_path = IMAGES_DIR / f"{prompt_hash}.png"
    if out_path.exists():  # caché
        return _rel(out_path)

    payload = {
        "contents": [{"parts": [{"text": enriched}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                GEMINI_ENDPOINT,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
            )
    except httpx.HTTPError as exc:
        return f"Error de red llamando a Gemini: {exc}"

    if resp.status_code != 200:
        return f"Error de Gemini ({resp.status_code}): {resp.text[:300]}"

    try:
        data = resp.json()
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        return f"Error: respuesta inesperada de Gemini ({exc})."

    import base64

    image_b64 = None
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            image_b64 = inline["data"]
            break

    if not image_b64:
        return "Error: Gemini no devolvió imagen (posible bloqueo de safety o prompt sin salida de imagen)."

    try:
        out_path.write_bytes(base64.b64decode(image_b64))
    except (ValueError, OSError) as exc:
        return f"Error guardando la imagen: {exc}"

    return _rel(out_path)


# ---------------------------------------------------------------------------
# Tripo: helpers de upload / task / polling
# ---------------------------------------------------------------------------
def _tripo_upload(client: httpx.Client, api_key: str, image_path: Path) -> tuple[str | None, str | None]:
    """Sube la imagen a Tripo. Devuelve (file_token, error_msg)."""
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path.name, f, "image/png")}
            resp = client.post(
                TRIPO_UPLOAD_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
            )
    except httpx.HTTPError as exc:
        return None, f"Error de red subiendo a Tripo: {exc}"

    if resp.status_code != 200:
        return None, f"Error subiendo a Tripo ({resp.status_code}): {resp.text[:300]}"

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return None, "Error: respuesta de upload de Tripo no es JSON."

    if data.get("code") not in (0, None):
        return None, f"Error de Tripo en upload: {data.get('message', data)}"

    token = (data.get("data") or {}).get("image_token") or (data.get("data") or {}).get("file_token")
    if not token:
        return None, f"Error: Tripo no devolvió file_token en upload ({data})."
    return token, None


def _tripo_create_task(client: httpx.Client, api_key: str, body: dict) -> tuple[str | None, str | None]:
    """Crea un task en Tripo. Devuelve (task_id, error_msg)."""
    try:
        resp = client.post(
            TRIPO_TASK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
    except httpx.HTTPError as exc:
        return None, f"Error de red creando task en Tripo: {exc}"

    if resp.status_code != 200:
        return None, f"Error creando task en Tripo ({resp.status_code}): {resp.text[:300]}"

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return None, "Error: respuesta de task de Tripo no es JSON."

    if data.get("code") not in (0, None):
        return None, f"Error de Tripo al crear task: {data.get('message', data)}"

    task_id = (data.get("data") or {}).get("task_id")
    if not task_id:
        return None, f"Error: Tripo no devolvió task_id ({data})."
    return task_id, None


def _tripo_poll(client: httpx.Client, api_key: str, task_id: str) -> tuple[dict | None, str | None]:
    """Hace polling con backoff hasta success/failed/timeout. Devuelve (task_data, error_msg)."""
    deadline = time.monotonic() + POLL_TIMEOUT_S
    url = f"{TRIPO_TASK_URL}/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    while True:
        try:
            resp = client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            return None, f"Error de red consultando estado en Tripo: {exc}"

        if resp.status_code != 200:
            return None, f"Error consultando task en Tripo ({resp.status_code}): {resp.text[:200]}"

        try:
            data = resp.json().get("data", {})
        except json.JSONDecodeError:
            return None, "Error: estado de Tripo no es JSON."

        status = data.get("status")
        if status == "success":
            return data, None
        if status in ("failed", "banned", "cancelled", "expired", "unknown"):
            return None, f"Tripo devolvió estado '{status}' para el task {task_id}."

        if time.monotonic() >= deadline:
            return None, f"Timeout (~{int(POLL_TIMEOUT_S)}s) esperando el task {task_id} de Tripo (último estado: {status})."

        time.sleep(POLL_INTERVAL_S)


def _tripo_model_url(task_data: dict) -> str | None:
    """Extrae la URL del .glb resultante de un task de Tripo."""
    output = task_data.get("output") or {}
    result = task_data.get("result") or {}
    # Tripo ha usado distintas claves según versión: pbr_model / model / base_model.
    for container in (output, result):
        for key in ("pbr_model", "model", "base_model", "rigged_model"):
            val = container.get(key)
            if isinstance(val, str) and val:
                return val
            if isinstance(val, dict) and val.get("url"):
                return val["url"]
    return None


def _download(client: httpx.Client, url: str, dest: Path) -> str | None:
    """Descarga un archivo a dest. Devuelve error_msg o None."""
    try:
        with client.stream("GET", url) as resp:
            if resp.status_code != 200:
                return f"Error descargando el modelo ({resp.status_code})."
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)
    except httpx.HTTPError as exc:
        return f"Error de red descargando el modelo: {exc}"
    return None


# ---------------------------------------------------------------------------
# 2) image_to_3d
# ---------------------------------------------------------------------------
@mcp.tool()
def image_to_3d(image_path: str, face_limit: int = 5000) -> str:
    """Convierte una imagen en un .glb texturizado vía Tripo (async + polling) y devuelve la ruta; cachea por hash de la imagen."""
    api_key = _env("TRIPO_API_KEY")
    if not api_key:
        return "Error: falta TRIPO_API_KEY en el entorno."

    img = Path(image_path)
    if not img.is_absolute():
        img = BASE_DIR / image_path
    if not img.exists():
        return f"Error: no existe la imagen {image_path}."

    face_limit = max(FACE_LIMIT_MIN, min(FACE_LIMIT_MAX, int(face_limit)))

    img_hash = _hash_file(img)
    out_path = MODELS_DIR / f"{img_hash}.glb"
    if out_path.exists():  # caché por hash de la imagen
        return _rel(out_path)

    with httpx.Client(timeout=60.0) as client:
        file_token, err = _tripo_upload(client, api_key, img)
        if err:
            return err

        body = {
            "type": "image_to_model",
            "file": {"type": "png", "file_token": file_token},
            "face_limit": face_limit,
            "texture": True,
            "pbr": True,
        }
        task_id, err = _tripo_create_task(client, api_key, body)
        if err:
            return err

        task_data, err = _tripo_poll(client, api_key, task_id)
        if err:
            return err

        model_url = _tripo_model_url(task_data)
        if not model_url:
            return f"Error: el task {task_id} terminó pero no expuso URL de modelo."

        err = _download(client, model_url, out_path)
        if err:
            return err

    return _rel(out_path)


# ---------------------------------------------------------------------------
# 3) auto_rig  (fallback; el rigging principal se hace en Mixamo)
# ---------------------------------------------------------------------------
@mcp.tool()
def auto_rig(glb_path: str) -> str:
    """Riggea un .glb generado por Tripo vía Auto Rigging (async) y devuelve la ruta del .glb riggeado; fallback de Mixamo."""
    api_key = _env("TRIPO_API_KEY")
    if not api_key:
        return "Error: falta TRIPO_API_KEY en el entorno."

    src = Path(glb_path)
    if not src.is_absolute():
        src = BASE_DIR / glb_path
    if not src.exists():
        return f"Error: no existe el modelo {glb_path}."

    src_hash = _hash_file(src)
    out_path = RIGGED_DIR / f"{src_hash}_rigged.glb"
    if out_path.exists():  # caché
        return _rel(out_path)

    with httpx.Client(timeout=60.0) as client:
        # 1) Subimos el .glb para obtener un token de modelo reutilizable.
        try:
            with open(src, "rb") as f:
                files = {"file": (src.name, f, "model/gltf-binary")}
                up = client.post(
                    TRIPO_UPLOAD_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files,
                )
        except httpx.HTTPError as exc:
            return f"Error de red subiendo el modelo a Tripo: {exc}"

        if up.status_code != 200:
            return f"Error subiendo el modelo a Tripo ({up.status_code}): {up.text[:200]}"

        try:
            up_data = up.json().get("data", {})
        except json.JSONDecodeError:
            return "Error: respuesta de upload de Tripo no es JSON."

        model_token = up_data.get("file_token") or up_data.get("image_token") or up_data.get("model_token")
        if not model_token:
            return f"Error: Tripo no devolvió token del modelo subido ({up_data})."

        # 2) Task de rigging.
        body = {
            "type": "animate_rig",
            "original_model_task_id": None,
            "file": {"type": "glb", "file_token": model_token},
            "out_format": "glb",
        }
        task_id, err = _tripo_create_task(client, api_key, body)
        if err:
            return (
                f"{err}\nNota: el Auto Rigging de Tripo suele requerir enlazar el "
                "task original de generación. Si falla, usa el flujo manual de Mixamo."
            )

        task_data, err = _tripo_poll(client, api_key, task_id)
        if err:
            return err

        model_url = _tripo_model_url(task_data)
        if not model_url:
            return f"Error: el task de rigging {task_id} no expuso URL de modelo."

        err = _download(client, model_url, out_path)
        if err:
            return err

    return _rel(out_path)


# ---------------------------------------------------------------------------
# 4) optimize_mesh
# ---------------------------------------------------------------------------
def _glb_has_rig_or_anim(path: Path) -> bool:
    """True si el .glb contiene skins (esqueleto) o animaciones."""
    try:
        from pygltflib import GLTF2

        gltf = GLTF2().load(str(path))
        return bool(getattr(gltf, "animations", None)) or bool(getattr(gltf, "skins", None))
    except Exception:
        return False


def _glb_has_texture(path: Path) -> bool:
    """True si el .glb trae texturas/imágenes o materiales (visual que trimesh perdería al decimar)."""
    try:
        from pygltflib import GLTF2

        gltf = GLTF2().load(str(path))
        return bool(getattr(gltf, "textures", None)) or bool(getattr(gltf, "images", None)) or bool(getattr(gltf, "materials", None))
    except Exception:
        return False


@mcp.tool()
def optimize_mesh(glb_path: str, target_faces: int = 3000) -> str:
    """Decima un .glb estático SIN textura a target_faces con trimesh; si trae textura, rig o animaciones NO decima (los preservaría se perderían). Devuelve la ruta."""
    src = Path(glb_path)
    if not src.is_absolute():
        src = BASE_DIR / glb_path
    if not src.exists():
        return f"Error: no existe el modelo {glb_path}."

    out_path = OPTIMIZED_DIR / f"{src.stem}_opt.glb"

    # CRÍTICO: si hay rig o animaciones, la decimación con trimesh rompería
    # skin weights y clips (trimesh no los preserva). En ese caso copiamos el
    # modelo tal cual para no destruir el rig, y avisamos.
    if _glb_has_rig_or_anim(src):
        import shutil

        shutil.copyfile(src, out_path)
        return (
            f"{_rel(out_path)} (copiado sin decimar: el .glb contiene rig/animaciones "
            "y se preservaron skin weights y clips; decima la malla ANTES de riggear/animar)."
        )

    # IGUAL DE CRÍTICO: si trae textura, la decimación con trimesh rompe las UVs
    # y la malla queda sin material (negra). Preservamos la textura y avisamos:
    # el poly-budget de assets texturizados se controla con el face_limit de Tripo
    # en image_to_3d (produce low-poly CON textura en un solo paso).
    if _glb_has_texture(src):
        import shutil

        shutil.copyfile(src, out_path)
        return (
            f"{_rel(out_path)} (copiado sin decimar: el .glb tiene textura y trimesh "
            "la perdería al decimar; controla los polígonos con el face_limit de Tripo "
            "en image_to_3d)."
        )

    try:
        import trimesh

        mesh = trimesh.load(str(src), force="mesh")
    except Exception as exc:
        return f"Error cargando el modelo con trimesh: {exc}"

    if not hasattr(mesh, "faces"):
        return "Error: el archivo no contiene una malla triangular decimable."

    target_faces = max(1, int(target_faces))
    try:
        if len(mesh.faces) > target_faces:
            simplified = mesh.simplify_quadric_decimation(face_count=target_faces)
        else:
            simplified = mesh  # ya está por debajo del objetivo
    except Exception as exc:
        return f"Error decimando la malla: {exc}"

    try:
        simplified.export(str(out_path))
    except Exception as exc:
        return f"Error exportando el .glb optimizado: {exc}"

    return f"{_rel(out_path)} ({len(mesh.faces)} -> {len(simplified.faces)} caras)"


# ---------------------------------------------------------------------------
# 5) merge_animations
# ---------------------------------------------------------------------------
@mcp.tool()
def merge_animations(glb_paths: list[str], output_id: str) -> str:
    """Fusiona varios .glb de Mixamo (idle, skateboarding, jumping...) en un ÚNICO .glb con la malla una vez + todos los clips, listo para AnimationMixer."""
    if not glb_paths:
        return "Error: no se pasaron .glb para fusionar."

    resolved: list[Path] = []
    for p in glb_paths:
        path = Path(p)
        if not path.is_absolute():
            path = BASE_DIR / p
        if not path.exists():
            return f"Error: no existe el .glb {p}."
        resolved.append(path)

    try:
        from pygltflib import GLTF2
    except ImportError:
        return "Error: falta pygltflib (pip install pygltflib)."

    # Base = primer .glb (aporta la malla, esqueleto y su primer clip).
    try:
        base = GLTF2().load(str(resolved[0]))
    except Exception as exc:
        return f"Error cargando el .glb base: {exc}"

    # Mapa nombre_de_nodo -> índice en la base, para remapear los canales.
    base_node_by_name = {
        n.name: i for i, n in enumerate(base.nodes) if n.name is not None
    }

    def _clip_name(gltf, anim, src_path: Path, idx: int) -> str:
        # Mixamo nombra TODAS sus animaciones "mixamo.com", así que ese nombre es
        # inútil para el AnimationMixer. Derivamos el nombre del ARCHIVO:
        # "skater@skateboarding.glb" -> "skateboarding". Si un .glb trae varios
        # clips, se desambigua con el índice.
        stem = src_path.stem
        base_name = stem.split("@")[-1] if "@" in stem else stem
        n_clips = len(getattr(gltf, "animations", []) or [])
        return base_name if n_clips <= 1 else f"{base_name}_{idx}"

    base_bin = bytearray(base.binary_blob() or b"")

    def _append_bin(blob: bytes) -> int:
        """Alinea a 4 bytes y anexa blob al buffer base; devuelve el offset."""
        while len(base_bin) % 4 != 0:
            base_bin.append(0)
        offset = len(base_bin)
        base_bin.extend(blob)
        return offset

    def _import_accessor(src_gltf, src_bin: bytes, acc_idx: int) -> int:
        """Copia un accessor (con su bufferView y bytes) desde src a la base. Devuelve el nuevo índice."""
        acc = src_gltf.accessors[acc_idx]
        bv = src_gltf.bufferViews[acc.bufferView]
        start = (bv.byteOffset or 0)
        length = bv.byteLength
        raw = src_bin[start:start + length]

        new_offset = _append_bin(raw)

        from pygltflib import BufferView, Accessor

        new_bv = BufferView(
            buffer=0,
            byteOffset=new_offset,
            byteLength=length,
            byteStride=bv.byteStride,
            target=bv.target,
        )
        base.bufferViews.append(new_bv)
        new_bv_idx = len(base.bufferViews) - 1

        new_acc = Accessor(
            bufferView=new_bv_idx,
            byteOffset=acc.byteOffset,
            componentType=acc.componentType,
            normalized=acc.normalized,
            count=acc.count,
            type=acc.type,
            max=acc.max,
            min=acc.min,
        )
        base.accessors.append(new_acc)
        return len(base.accessors) - 1

    imported = 0
    skipped: list[str] = []

    # El primer .glb ya trae su clip en la base; añadimos los clips del resto.
    for src_idx, src_path in enumerate(resolved):
        if src_idx == 0:
            # Forzamos el nombre del clip base desde el archivo (Mixamo pone
            # "mixamo.com", que no sirve para el AnimationMixer).
            for i, anim in enumerate(base.animations):
                anim.name = _clip_name(base, anim, src_path, i)
                imported += 1
            continue

        try:
            src = GLTF2().load(str(src_path))
        except Exception as exc:
            skipped.append(f"{src_path.name} (no se pudo cargar: {exc})")
            continue

        src_bin = src.binary_blob() or b""
        src_node_name = {i: n.name for i, n in enumerate(src.nodes)}

        from pygltflib import Animation, AnimationChannel, AnimationChannelTarget, AnimationSampler

        for a_idx, anim in enumerate(src.animations):
            new_samplers = []
            sampler_remap: dict[int, int] = {}
            ok = True

            for s_i, sampler in enumerate(anim.samplers):
                in_acc = _import_accessor(src, src_bin, sampler.input)
                out_acc = _import_accessor(src, src_bin, sampler.output)
                sampler_remap[s_i] = len(new_samplers)
                new_samplers.append(
                    AnimationSampler(
                        input=in_acc,
                        output=out_acc,
                        interpolation=sampler.interpolation,
                    )
                )

            new_channels = []
            for ch in anim.channels:
                target_node_idx = ch.target.node
                node_name = src_node_name.get(target_node_idx)
                # Remapeamos por NOMBRE de hueso (Mixamo usa mixamorig:*).
                mapped = base_node_by_name.get(node_name)
                if mapped is None:
                    ok = False
                    break
                new_channels.append(
                    AnimationChannel(
                        sampler=sampler_remap[ch.sampler],
                        target=AnimationChannelTarget(node=mapped, path=ch.target.path),
                    )
                )

            if not ok or not new_channels:
                skipped.append(
                    f"{src_path.name}:{_clip_name(src, anim, src_path, a_idx)} "
                    "(los huesos no coinciden con el esqueleto base)"
                )
                continue

            base.animations.append(
                Animation(
                    name=_clip_name(src, anim, src_path, a_idx),
                    samplers=new_samplers,
                    channels=new_channels,
                )
            )
            imported += 1

    # Reescribimos el buffer combinado y su longitud.
    base.set_binary_blob(bytes(base_bin))
    if base.buffers:
        base.buffers[0].byteLength = len(base_bin)
        base.buffers[0].uri = None  # GLB: buffer embebido

    out_path = FINAL_DIR / (output_id if output_id.endswith(".glb") else f"{output_id}.glb")
    try:
        base.save(str(out_path))
    except Exception as exc:
        return f"Error guardando el .glb final: {exc}"

    msg = f"{_rel(out_path)} ({imported} animaciones empaquetadas)"
    if skipped:
        msg += ". Omitidas: " + "; ".join(skipped)
    return msg


# ---------------------------------------------------------------------------
# 6) update_manifest  /  7) read_manifest
# ---------------------------------------------------------------------------
def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    if "objects" not in data or not isinstance(data.get("objects"), dict):
        data["objects"] = {}
    return data


@mcp.tool()
def update_manifest(object_id: str, model_path: str) -> str:
    """Actualiza game/assets_manifest.json con {object_id: {model: model_path}} y devuelve confirmación corta."""
    data = _load_manifest()

    p = Path(model_path)
    stored = _rel(p if p.is_absolute() else BASE_DIR / model_path)

    data["objects"][object_id] = {"model": stored}
    try:
        MANIFEST_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        return f"Error escribiendo el manifest: {exc}"

    return f"OK: '{object_id}' -> {stored} ({len(data['objects'])} objetos en total)."


@mcp.tool()
def read_manifest() -> str:
    """Devuelve el contenido actual de game/assets_manifest.json (para consultar estado cuando se necesite)."""
    data = _load_manifest()
    return json.dumps(data, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
