# Auditoría de fidelidad: juego vs sitio real

Objetivo (usuario): **que el mapa se parezca al real lo más fiel posible.**
Método: loop construir → entrar al juego → validar contra satélite/fotos →
corregir → siguiente. Este doc es el estado zona por zona; se actualiza en
cada loop. Fuentes en `fuentes-mapa-real.md`.

Estados: ✅ fiel · 🔶 parcial (difiere en detalles) · ❌ falta/incorrecto ·
❓ falta información real

## Zona por zona

| # | Zona | Estado | Detalle / pendiente |
|---|------|--------|---------------------|
| 1 | Templo (mesh Tripo, no tocar) | ✅ | cúpula + torre; escala aprobada por el usuario |
| 2 | Nave en ruinas (45m, muros dentados, pilares cuadrados) | 🔶 | fiel en planta; REVISAR: alturas de muros vs fotos, arcos laterales de ladrillo (SV frente-este) |
| 3 | ~~Santuario de 3 arcos~~ | ✅ | **ELIMINADO** — el usuario confirma que ese arco NO existe. La estatua de Santander con su pedestal sí queda (esa sí es real) |
| 4 | Placa elevada (20×15, 1.5m, escalinata) | ✅ | detrás del templo; el usuario indica que su posición exacta "no tiene mucha relevancia" — se da por buena |
| 5 | Explanada de arena (70×84 real) | ✅ | posición y proporción razonables (satélite) |
| 6 | Piscina (lado este del templo) | ✅ | rediseño del usuario con sus fotos; existe aunque el satélite no la muestre |
| 7 | Parque de palmeras NORTE (64×97) | ✅ | sembrado + senderos de tierra internos (loop 4) |
| 8 | Palmar/bosque SUR caminable + sendero | ✅ | sembrado + cruce de senderos (loop 4) |
| 9 | Vías este y oeste | 🔶 | extendidas + berma de arena oeste + andenes de baldosa (loop 4); falta: parqueo diagonal, cruces laterales |
| 10 | Cercas del parque | ✅ | 3 estilos reales: piedra+hierro frente al templo, pilares blancos norte/este/sur, verde metálica oeste-sur (loop 4) |
| 11 | Escalinata de entrada este del templo | ✅ | vano en la cerca de piedra + 2 peldaños (loop 4) |
| 12 | Andenes de baldosa de ladrillo | ✅ | textura de baldosa aplicada a ambos andenes (loop 4) |
| 13 | Tamarindo histórico (NE, copa enorme) | 🔶 | hay tamarindos; validar el GRANDE de la esquina NE con SV |
| 14 | Colonnata de palmas reales vía este norte | ✅ | 6 palmas reales altas en fila (loop 4) |
| 15 | ~~Monumento/obelisco~~ | ✅ | **ELIMINADO** (con sus barandales) — el usuario confirma que no existe en el parque real |
| 16 | Club Villa Campestre | ✅ | predio amurallado blanco, portón verde, valla, piscina, salón de teja, palmas (loop 4) |
| 17 | Kiosco esquina oeste (Cl 10) | ✅ | construido (loop 1) validado en cenital |
| 18 | Casas coloniales del borde | 🔶 | volumetría ok; texturas reales (calados, tapia) capturadas en SV sin aplicar |
| 19 | Cancha este | ✅ | cancha verde con líneas y arcos/tableros, cruzando la vía (loop 4, escala reducida por espacio) |
| 20 | Polideportivo oeste (techo azul) | ✅ | bodega crema de techo azul con portón (loop 4) |

## Preguntas abiertas para el usuario

(Resueltas 2026-08-02: placa sin relevancia exacta ✓; el arco no existe →
eliminado ✓; el obelisco no existe → eliminado ✓. Sin preguntas abiertas.)

## Reglas del loop (acordadas)

- No pasar a la siguiente estructura sin validar la actual en cenital + física.
- Texturas del pipeline (Gemini) o extraídas de fotos > colores planos.
- El mesh del templo NO se toca. La piscina existe. El usuario (local) manda
  sobre cualquier triangulación mía.
