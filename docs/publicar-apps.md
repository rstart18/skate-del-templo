# Publicar SKATE DEL TEMPLO — web, Android e iOS

Un solo repo, un solo código (el juego web). Las "apps" son el mismo HTML
empaquetado con **Capacitor** (WebView nativo). Ya está TODO configurado.

## El flujo de siempre (memorízate estos 3 comandos)

```
npm run web        # publica la web en https://snaikyy-skate.surge.sh
npm run android    # reconstruye dist, sincroniza y abre Android Studio
npm run ios        # igual pero para Xcode (solo en Mac)
```

Cualquier feature nueva se hace en `game/skate.html` como siempre. Los tres
comandos arriba parten de ahí — no hay código duplicado por plataforma.

## Cómo está armado

- `scripts/build-dist.mjs` — arma `dist/` (juego + assets). Si el juego empieza
  a cargar un asset nuevo, AGREGARLO a la lista `files` de ese script.
- `capacitor.config.json` — appId `com.snaikyy.skatedeltemplo`, webDir `dist`.
- `android/` — proyecto Android nativo (SE COMMITEA al repo).
- `ios/` — proyecto iOS nativo (SE COMMITEA al repo).
- `npx cap sync` copia `dist/` dentro de ambos proyectos nativos.

## Android — primera vez (una sola vez)

1. Instala **Android Studio**: https://developer.android.com/studio
   (trae el SDK y Java; no hay que instalar nada más).
2. `npm run android` → abre el proyecto en Android Studio.
3. Para PROBAR: conecta el celular con "Depuración USB" activada y dale ▶.
4. Para PUBLICAR:
   - Menú **Build ▸ Generate Signed Bundle/APK ▸ Android App Bundle**.
   - Crea un **keystore** nuevo (GUÁRDALO + su contraseña: sin él NO puedes
     actualizar la app nunca más; hacer backup fuera del repo, NUNCA commitearlo).
   - Cuenta de **Google Play Console**: única vez USD $25 → https://play.google.com/console
   - Crea la app, sube el `.aab`, llena la ficha (capturas, descripción) y a revisión.
5. ACTUALIZACIONES futuras: sube `versionCode` (+1) y `versionName` en
   `android/app/build.gradle`, repite Build ▸ Generate Signed Bundle con el
   MISMO keystore, sube el nuevo `.aab`.

## iOS — la realidad desde Windows

Compilar iOS exige **Xcode, que solo corre en macOS**. La carpeta `ios/` ya
está creada y sincronizada; opciones para compilarla:

- **Codemagic** (recomendada, tiene plan gratis): CI en la nube que compila
  Capacitor iOS desde tu repo de GitHub y hasta sube a App Store Connect.
  https://codemagic.io — se configura con un `codemagic.yaml` en el repo.
- Un Mac prestado o **MacinCloud** (Mac por horas): `npm run ios` y publicar
  con Xcode como en cualquier tutorial de Capacitor.
- En ambos casos necesitas el **Apple Developer Program**: USD $99/año.

Sugerencia práctica: lanza primero Android (barato y desde tu PC); iOS cuando
el juego tenga tracción, vía Codemagic.

## GitHub — un solo repo (como querías)

Ya está todo listo para el primer push. El `.gitignore` protege `.env` (¡API
keys!) e ignora lo regenerable, PERO incluye los 5 modelos finales del juego
(sin ellos un clon no funciona). Primer push:

```
git add -A
git commit -m "SKATE DEL TEMPLO: juego web + Capacitor (Android/iOS)"
# crea el repo vacío en github.com y luego:
git remote add origin https://github.com/TU_USUARIO/skate-del-templo.git
git push -u origin master
```

ANTES del primer push, verifica que el .env NO va incluido:
`git status --ignored | grep .env` debe mostrarlo como ignorado.

## Trampas conocidas (aprendidas a golpes)

- El juego carga assets por `fetch` — en la app funcionan porque Capacitor
  sirve `dist/` por HTTP interno. No usar rutas absolutas `/assets/...`;
  siempre relativas `../assets/...` como están.
- Si agregas un asset nuevo y en la app no aparece: te faltó agregarlo a
  `scripts/build-dist.mjs` (la web por surge tiene el mismo requisito).
- El manifest usa cache-buster `?v=N` — al regenerar un glb, sube la N.
- El fullscreen/landscape del juego ya funciona dentro del WebView de la app.
