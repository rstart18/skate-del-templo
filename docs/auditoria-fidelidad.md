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
| 3 | Santuario de Santander (muro 3 arcos + estatua) | 🔶 | existe en el sitio (video usuario) ✅ pero **validar su posición exacta** — el usuario señala que el arco no está donde el juego lo pone respecto a la placa ❓ |
| 4 | Placa elevada (20×15, 1.5m, escalinata) | 🔶 | movida detrás del templo (corrección usuario); **posición exacta y orientación de la escalinata** ❓ — pedir foto/pin del usuario; hoy queda alineada al eje del santuario y el usuario indica que así no es |
| 5 | Explanada de arena (70×84 real) | ✅ | posición y proporción razonables (satélite) |
| 6 | Piscina (lado este del templo) | ✅ | rediseño del usuario con sus fotos; existe aunque el satélite no la muestre |
| 7 | Parque de palmeras NORTE (64×97) | 🔶 | sembrado (loop 2); faltan los senderos de tierra internos del satélite |
| 8 | Palmar/bosque SUR caminable + sendero | 🔶 | sembrado (loop 1); densidad real es mayor; falta el cruce de senderos |
| 9 | Vías este y oeste | 🔶 | extendidas a todo el mundo (loop 2); falta: berma de arena oeste (SV), parqueo diagonal oeste (satélite), cruces de calles laterales |
| 10 | Cercas del parque | 🔶 | pilares blancos + rejas ✅ (SV norte/este); falta el tramo de **piedra + hierro frente al templo** (SV) y la **cerca verde metálica** del tramo oeste-sur (SV) |
| 11 | Escalinata de entrada este del templo (desde el andén) | ❌ | SV la muestra clara; no existe en el juego |
| 12 | Andenes de baldosa de ladrillo (SV) | 🔶 | hay andén de concreto; el real es baldosa de arcilla |
| 13 | Tamarindo histórico (NE, copa enorme) | 🔶 | hay tamarindos; validar el GRANDE de la esquina NE con SV |
| 14 | Colonnata de palmas reales vía este norte (SV) | ❌ | pendiente |
| 15 | Monumento/obelisco del juego | ❓ | el "monumento" del satélite era un tanque de agua; el obelisco real del parque no está confirmado en posición — fuente pendiente (foto usuario / fotos turísticas) |
| 16 | Club Villa Campestre (esquina SE: valla, portón verde, muros blancos, piscina) | ❌ | pendiente |
| 17 | Kiosco esquina oeste (Cl 10) | ✅ | construido (loop 1) validado en cenital |
| 18 | Casas coloniales del borde | 🔶 | volumetría ok; texturas reales (calados, tapia) capturadas en SV sin aplicar |
| 19 | Cancha este (37×28, cruzando la vía) | ❌ | pendiente |
| 20 | Polideportivo oeste (techo azul) | ❌ | pendiente |

## Preguntas abiertas para el usuario (bloquean fidelidad exacta)

1. **Placa elevada**: ¿hacia dónde mira la escalinata y qué tan lejos está del
   santuario/nave? (una foto o un pin en el mapa resuelve)
2. **Santuario/arco**: ¿el muro de 3 arcos está pegado al fondo de la nave o
   separado? ¿la placa queda a un costado y no en su eje?
3. **Obelisco del juego**: ¿existe en el parque real y dónde?

## Reglas del loop (acordadas)

- No pasar a la siguiente estructura sin validar la actual en cenital + física.
- Texturas del pipeline (Gemini) o extraídas de fotos > colores planos.
- El mesh del templo NO se toca. La piscina existe. El usuario (local) manda
  sobre cualquier triangulación mía.
