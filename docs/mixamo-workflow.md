# Flujo Mixamo — del skater base a las animaciones (Blender 5.0)

Mixamo **no acepta ni exporta `.glb`**: sube FBX/OBJ y descarga FBX/Collada. Por eso
Blender hace de puente en los dos extremos. Este es el flujo completo.

Malla base (T-pose, generada por el pipeline): `assets/models/9a0d0d90909a7330.glb`

Convención de nombres (IMPORTANTE — `merge_animations` saca el nombre del clip de
lo que va después de `@`):

| Archivo (en `assets/animations/`) | Clip resultante | Descarga Mixamo |
|---|---|---|
| `skater@skateboarding.glb` | `skateboarding` | **With Skin** (es la base, aporta la malla) |
| `skater@jumping.glb` | `jumping` | Without Skin |
| `skater@crouch.glb` | `crouch` | Without Skin |
| `skater@fall.glb` | `fall` | Without Skin |

---

## PARTE A — Convertir el skater base `.glb` → `.fbx` (para subir a Mixamo)

1. Blender 5.0 → **File ▸ Import ▸ glTF 2.0 (.glb/.gltf)** → elige
   `assets/models/9a0d0d90909a7330.glb`. Entra de pie (glTF es Y-up, Blender lo
   convierte a Z-up automáticamente).
2. Selecciona el mesh. **Object ▸ Apply ▸ All Transforms** (Ctrl+A → All Transforms)
   para dejar escala/rotación limpias.
3. **File ▸ Export ▸ FBX (.fbx)**:
   - **Path Mode: Copy** + activa el icono de **Embed Textures** (para que la textura viaje).
   - Deja **Forward: -Z**, **Up: Y** (por defecto — Mixamo lo espera así).
   - Guárdalo como `skater_base.fbx` (fuera de `assets/animations/`, es temporal).
4. [mixamo.com](https://www.mixamo.com) → **Upload Character** → `skater_base.fbx` →
   coloca los marcadores (barbilla, muñecas, codos, rodillas, entrepierna) → auto-rig.

---

## PARTE B — Aplicar y descargar las 4 animaciones en Mixamo

Con el personaje ya riggeado, busca y aplica cada animación. Sugerencias de búsqueda:

| La tuya | Buscar en Mixamo |
|---|---|
| skateboarding | `Skateboarding` |
| jumping | `Jump` / `Jumping` |
| agacharse | `Crouch` / `Crouching Idle` |
| caerse | `Falling Back Death` / `Stumble Backwards` |

Para **cada** animación, **Download** con:
- **Format: FBX Binary (.fbx)**
- **Skin:** la 1ª (skateboarding) = **With Skin**; las otras 3 = **Without Skin**.
- **Frames per Second: 30**, **Keyframe Reduction: none**.

Te quedan 4 archivos `.fbx`.

---

## PARTE C — Convertir cada `.fbx` de Mixamo → `.glb` (en Blender)

Repite esto para **cada** uno de los 4 FBX (hazlos todos igual para que los nombres
de huesos coincidan entre archivos — de eso depende `merge_animations`):

1. **File ▸ New ▸ General** (empezar limpio).
2. **File ▸ Import ▸ FBX (.fbx)** → el fbx de la animación.
3. **File ▸ Export ▸ glTF 2.0 (.glb)**:
   - **Format: glTF Binary (.glb)**.
   - Sección **Data ▸ Mesh**: deja lo default. Sección **Animation**: activada
     (exporta la acción importada).
   - Guárdalo en `assets/animations/` con el nombre EXACTO de la tabla de arriba
     (`skater@skateboarding.glb`, `skater@jumping.glb`, `skater@crouch.glb`, `skater@fall.glb`).

---

## PARTE D — Fusionar (lo hago yo con el MCP)

Cuando los 4 `.glb` estén en `assets/animations/`, corro:

```
merge_animations(
  glb_paths=[
    "assets/animations/skater@skateboarding.glb",   # PRIMERO = base con malla
    "assets/animations/skater@jumping.glb",
    "assets/animations/skater@crouch.glb",
    "assets/animations/skater@fall.glb",
  ],
  output_id="skater"
)
```

→ produce `assets/models_final/skater.glb`: la malla UNA vez + los 4 clips
(`skateboarding`, `jumping`, `crouch`, `fall`), listo para `AnimationMixer`.

Luego cableo el `AnimationMixer` en el juego y conecto los clips a los estados
(rodando / aire / cargar ollie / bail).

> Si `merge_animations` reporta clips "omitidos (huesos no coinciden)", casi seguro
> es porque algún `.glb` se convirtió distinto en Blender. Reconvierte los 4 igual.
