# Fuentes del sitio real (Parque Gran Colombiano / Templo Histórico)

Registro de las fuentes recolectadas para ampliar el mapa del juego con el
sitio real. Coordenadas del templo (Nominatim): **7.8293274, -72.4626194**.

## Satélite (Esri World Imagery, zoom 19, 0.2958 m/px)

- `tools/sat_grande.jpg` — mosaico 5×5 tiles (378 m de lado), templo en px (681, 528)
- `tools/sat_zonas_anotado.jpg` — 10 zonas identificadas con medidas
- `tools/real_vs_juego.jpg` — comparación con el mapa actual del juego
- Conversión px→m: `metros = px * 0.2958`; el juego usa 1 unidad = 1 m

## Panoramas de Street View (thumbnails vía navegador, w=1024)

El endpoint `streetviewpixels-pa.googleapis.com/v1/thumbnail` funciona SOLO
desde el contexto de una página google.com (fetch en el navegador) — con curl
da 403. El `yaw` es rumbo absoluto (0=N, 90=E, 180=S, 270=O).

| Panoid | Coordenadas | Ubicación |
|---|---|---|
| 3QaZnwAQKS-IhpxStoaVOw | 7.8292873, -72.4624648 | vía este FRENTE AL TEMPLO |
| U3MaGLT68wA9pxXNTD9fZw | 7.8276888, -72.4623671 | Calle 11 (borde sur) |
| 9MRubQTHHfmLRgQ_hek3lQ | 7.8296599, -72.4631832 | vía oeste (frente al palmar) |
| Ng9p5zHS-Wcn5iYiGfrVsQ | 7.8304762, -72.46241  | vía este tramo norte |
| t5LutGhZS_Z1GRs07oUNRA | 7.8276829, -72.46227  | Calle 11 este |
| oPmXjrbhFY9jfxmgU9clYA | 7.8276963, -72.4624747 | Calle 11 (esquina SE) |
| ruBZbL7Vxlp8-3rtgPi_5Q | 7.8284479, -72.4634215 | vía oeste con Calle 10 |
| df27nUNmAtdbX-gQI7j4qA | 7.8278614, -72.4618338 | Cra 1 Este (club piscina) |
| Xuht239qbyK79OnX3GjR4g | 7.8307531, -72.4624024 | vía este entrada norte |
| CIHM0ogKEICAgIDqg9u8_AE | 7.8297054, -72.4626316 | FOTOESFERA dentro del palmar (no descargable por API; verla en navegador) |

Capturas guardadas: `tools/sv_*.jpg` (ronda 1) y `tools/sv2_*.jpg` (ronda 2).
Paneles: `tools/sv_hallazgos.jpg`, `tools/sv_hallazgos2.jpg`.

## Hallazgos clave (para construir)

1. **Bajo el "bosque" sur hay suelo abierto transitable**: troncos de palma,
   senderos de tierra, gente caminando. Construir como palmar caminable.
2. **Cerca perimetral con DOS estilos**: frente al templo hierro negro con
   base de mampostería de piedra; tramo norte/este pilares BLANCOS con rejas.
3. **Muro del templo**: piedra tostada + arcos de LADRILLO rojo; escalinata
   de entrada desde el andén este; piso de losas alrededor (ya existe ✓).
4. **Torre oeste del templo con portal en arco** — visible desde la vía oeste.
5. **Tamarindo histórico**: árbol enorme de copa ancha, esquina NE del parque.
6. **Vía este tramo norte**: colonnata de palmas reales (troncos blancos).
7. **"Piscina pública" SE = Club Villa Campestre** (privado): valla de entrada
   "Restaurante / Piscina / Juegos / Salones", portón verde, muros blancos.
8. **CORRECCIÓN**: la "plazoleta del monumento" marcada en el satélite
   (7.82749, -72.46215) es en realidad un TANQUE DE AGUA elevado de una casa.
   El monumento/obelisco real del juego debe validarse aparte (está dentro
   del parque, no visible desde la calle).
9. **Vía oeste con Calle 10**: cruce con kiosco de comida y motos parqueadas;
   cerca verde metálica en ese tramo del parque.
10. Texturas de referencia capturadas: pared colonial con calados + teja,
    tapia pisada, muros blancos con teja.
11. **PLACA ELEVADA con escalinata** (señalada por el usuario, confirmada en
    SV): plataforma plana elevada con escaleras para subir, dentro del parque
    en la zona sur-central bajo el dosel. Posición triangulada:
    **≈ 7.82818, -72.46296 (±15 m)** — en coords del juego ≈ (x −37, z +82
    relativo a la cúpula), FUERA del límite actual del mapa (zona de
    ampliación sur). Vista en `tools/sv3_placa_desde_norte_c.jpg` (pano
    ZDfmF5rXtHwoIEEBx_3a9Q yaw 220) y en captura del usuario (pano "70",
    may 2022, mirando O-NO). En la captura del usuario se ve ademas un posible
    tablero de baloncesto cerca → podria ser placa polideportiva o tarima de
    eventos. Confirmar tamaño exacto con foto del usuario o fotoesfera.
    Paneles: `tools/placa_confirmada.jpg`.
