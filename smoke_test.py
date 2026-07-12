"""
smoke_test.py — Revalida el servidor game-assets-mcp sin conectarlo a un cliente.

Uso:
    python smoke_test.py            # pruebas locales (NO gasta créditos):
                                    #   imports, .env, manifest, optimize_mesh
    python smoke_test.py --full     # además genera imagen (Gemini) y modelo
                                    #   (Tripo). ¡ESTO SÍ CONSUME CRÉDITOS!

Pensado para correrse tras cambios en server.py o al montar el proyecto en
otra máquina. Limpia sus propios artefactos al terminar.
"""

from __future__ import annotations

import os
import sys
import time

import server  # importa y carga .env automáticamente

FULL = "--full" in sys.argv
PROMPT = "a wooden skateboard quarter pipe ramp, low poly game prop"

ok = 0
fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global ok, fail
    mark = "OK " if cond else "XX "
    if cond:
        ok += 1
    else:
        fail += 1
    print(f"  [{mark}] {name}" + (f" -> {detail}" if detail else ""))


print("== game-assets-mcp :: smoke test ==\n")

# --- 1) Entorno y tools -----------------------------------------------------
print("1) Entorno y tools")
import asyncio

tools = sorted(t.name for t in asyncio.run(server.mcp.list_tools()))
expected = {
    "generate_image", "image_to_3d", "auto_rig", "optimize_mesh",
    "merge_animations", "update_manifest", "read_manifest",
}
check("7 tools registradas", set(tools) == expected, ", ".join(tools))
check("GEMINI_API_KEY presente", bool(os.environ.get("GEMINI_API_KEY")))
check("TRIPO_API_KEY presente", bool(os.environ.get("TRIPO_API_KEY")))

# --- 2) Manifest ------------------------------------------------------------
print("\n2) Manifest (no gasta créditos)")
res = server.update_manifest("_smoke_probe", "assets/models_optimized/_probe.glb")
check("update_manifest escribe", "_smoke_probe" in server.read_manifest(), res)
# Restaura el manifest a vacío
import json
server.MANIFEST_PATH.write_text(
    json.dumps({"objects": {}}, indent=2), encoding="utf-8"
)
check("manifest restaurado a {}", server.read_manifest().count("_smoke_probe") == 0)

# --- 3) optimize_mesh (malla sintética, no gasta créditos) ------------------
print("\n3) optimize_mesh (malla sintética)")
try:
    import trimesh

    sphere = trimesh.creation.icosphere(subdivisions=5)  # ~20k caras
    src = server.MODELS_DIR / "_smoke_sphere.glb"
    sphere.export(str(src))
    out = server.optimize_mesh("assets/models/_smoke_sphere.glb", target_faces=1500)
    opt = server.OPTIMIZED_DIR / "_smoke_sphere_opt.glb"
    reduced = opt.exists() and len(trimesh.load(str(opt), force="mesh").faces) <= 1500
    check("decima >20k -> <=1500 caras", reduced, out)
    src.unlink(missing_ok=True)
    opt.unlink(missing_ok=True)
except Exception as exc:
    check("decima", False, f"EXC {exc}")

# --- 4) Pipeline con API (solo con --full; GASTA CRÉDITOS) ------------------
if FULL:
    print("\n4) Pipeline real Gemini + Tripo (--full, GASTA CRÉDITOS)")
    img = server.generate_image(PROMPT)
    check("generate_image -> .png", img.endswith(".png"), img)
    if img.endswith(".png"):
        t0 = time.time()
        glb = server.image_to_3d(img, face_limit=3000)
        check(
            f"image_to_3d -> .glb ({time.time() - t0:.0f}s)",
            glb.endswith(".glb"),
            glb,
        )
        if glb.endswith(".glb"):
            opt = server.optimize_mesh(glb, target_faces=2500)
            check("optimize_mesh sobre malla real", ".glb" in opt, opt)
        # Nota: no borramos estos artefactos; sirven de caché para no re-gastar.
else:
    print("\n4) Pipeline real Gemini + Tripo  (omitido; usa --full para probarlo)")

# --- Resumen ----------------------------------------------------------------
print(f"\n== Resultado: {ok} OK, {fail} fallos ==")
sys.exit(1 if fail else 0)
