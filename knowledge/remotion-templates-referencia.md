# Remotion Templates y Capacidades

Referencia de templates y patrones disponibles en Remotion para produccion
de video programatico. Usado por el Scriptwriter y el Content Factory.

---

## Templates Disponibles en ~/nexus-videos

### PromoProduct (custom, ya instalado)
Video promocional para Whabi, Docflow, o Aurora.
- 6 escenas: hook → 3 features → stat → CTA
- Spring physics, texto kinetico, numeros animados
- Brand system con colores por producto
- Input: `{brand, hook, features[], stat, cta}`

### TikTok Captions
Captions animadas word-by-word sobre video existente.
- Whisper.cpp para transcripcion automatica
- Estilos de caption personalizables
- Instalar: `npx create-video@latest --tiktok`

### Prompt to Motion Graphics
Genera motion graphics desde descripcion en texto.
- LLM genera codigo React en tiempo real
- Skills: charts, typography, transitions, spring-physics, social-media
- Instalar: `npx create-video@latest --prompt-to-motion-graphics`

### Audiogram
Convierte audio/podcast en video con waveform.
- Visualizacion de audio
- Subtitulos sincronizados
- Instalar: `npx create-video@latest --audiogram`

### Code Hike
Animaciones de codigo para tutoriales tech.
- Transiciones suaves entre snippets
- Syntax highlighting multi-lenguaje
- Instalar: `npx create-video@latest --code-hike`

---

## Tipos de Video y Que Template Usar

| Tipo de Video | Template | Cuando Usar |
|---|---|---|
| Promo de producto | PromoProduct | Promocionar Whabi/Docflow/Aurora |
| Datos/estadisticas | Prompt to Motion Graphics | Presentar numeros con graficos animados |
| Tutorial de codigo | Code Hike | Contenido tech para el blog |
| Podcast/audio clip | Audiogram | Convertir audio en video social |
| Video con captions | TikTok | Agregar subtitulos a cualquier video |
| Explainer generico | Prompt to Motion Graphics | Explicar conceptos con animaciones |

---

## Componentes de Remotion Disponibles

### Animacion
- `spring()` — movimiento organico con fisica
- `interpolate()` — mapear rangos de valores
- `useCurrentFrame()` — frame actual para animaciones
- `@remotion/animation-utils` — scale, translateY, rotate

### Transiciones
- `@remotion/transitions` — fade, slide, wipe, flip, clock-wipe
- `TransitionSeries` — transiciones entre escenas
- `linearTiming`, `springTiming` — control de velocidad

### Texto
- `@remotion/google-fonts` — 1500+ fuentes
- `@remotion/layout-utils` — fitText para texto responsive
- `@remotion/rounded-text-box` — text box estilo TikTok
- `@remotion/captions` — subtitulos profesionales

### Efectos
- `@remotion/motion-blur` — motion blur cinematico
- `@remotion/noise` — texturas de ruido/grain
- `@remotion/light-leaks` — efecto light leak
- `@remotion/starburst` — efecto starburst/rays
- `@remotion/shapes` — SVG shapes animados

### Audio
- `@remotion/sfx` — libreria de efectos de sonido
- `@remotion/media` — tags de audio/video
- Audio con volume, loop, startFrom

### Otros
- `@remotion/lottie` — animaciones After Effects
- `@remotion/animated-emoji` — emojis animados Google
- `@remotion/paths` — SVG path animations

---

## Flujo de Produccion

```
1. Scriptwriter genera JSON con template_id + contenido
2. CLI selecciona el template correcto
3. Remotion renderiza con los datos
4. Output: MP4 listo para publicar
```

Para motion graphics (sin imagenes AI):
```
1. Scriptwriter genera JSON con template="promo-product"
2. No se llama a MiniMax Image-01
3. Remotion usa componentes React animados
4. Resultado: video profesional sin costo de imagenes
```

---

## Edicion de Templates

### Con OpenCode (recomendado)
```bash
cd ~/nexus-videos
npm run dev          # Remotion Studio en browser
opencode             # en otra terminal
> "Mejora el HookScene con efecto glitch"
```
OpenCode tiene el skill `remotion-dev/skills` con 37 reglas.

### Con Remotion Studio
Abrir `npm run dev`, cambiar props en el panel derecho, ver resultado en tiempo real.

### Renderizar
```bash
npx remotion render promo-docflow ~/Downloads/docflow-promo.mp4
```
