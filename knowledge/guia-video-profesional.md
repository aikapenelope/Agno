# Guia: Video Profesional con Remotion + Agno

## El Problema Actual

Tu pipeline genera: imagen AI + texto encima + transiciones basicas = slideshow con efectos.
Los videos profesionales de Reels/TikTok usan: motion graphics, texto kinetico, graficos
animados, transiciones cinematicas, branding consistente.

## La Solucion: 3 Capas

```
Capa 1: Templates (tu los diseñas una vez)
  → Componentes React con tu identidad visual
  → Colores, fuentes, animaciones, layout predefinidos
  → Se reutilizan para cada video

Capa 2: Contenido (Agno lo genera)
  → Texto, datos, hooks, CTAs
  → El Scriptwriter produce JSON con el contenido
  → No decide el diseño, solo el contenido

Capa 3: Rendering (Remotion lo ejecuta)
  → Template + Contenido = Video final
  → Motion graphics, no imagenes AI
```

---

## Herramientas Disponibles en 2026

### Opcion A: Prompt-to-Motion-Graphics (Remotion oficial)

**Que es**: Un template SaaS de Remotion que genera codigo React de motion graphics
desde un prompt de texto. Usa un LLM para escribir el componente React en tiempo real.

**Como funciona**:
```
Prompt → LLM detecta skills necesarias → genera codigo React → compila en browser → preview
```

**Skills incluidas** (8 guidance + 9 examples):
- `typography`: typewriter, word carousel, text highlight
- `charts`: bar charts, pie charts, histograms con animaciones staggered
- `transitions`: TransitionSeries con fade, slide, wipe, flip
- `spring-physics`: bounce, snap, organic motion
- `social-media`: safe zones, mobile text sizes, hook en frame 0, high contrast
- `sequencing`: staggered entrances, choreographed animations
- `messaging`: chat bubbles, WhatsApp/iMessage style
- `3d`: Three.js integration

**Pros**: Genera motion graphics reales, no imagenes AI. Cada video es unico.
**Contras**: Necesita OpenAI para generar el codigo React. Calidad variable.

**Instalar**:
```bash
npx create-video@latest --prompt-to-motion-graphics
```

### Opcion B: Templates Pre-diseñados (lo mas profesional)

**Que es**: Tu diseñas componentes React reutilizables con tu identidad visual.
El sistema solo inyecta contenido diferente cada vez.

**Asi funcionan**: GitHub Unwrapped, Spotify Wrapped, Typeframes, ClipPulse.

**Ejemplo de template**:
```tsx
// templates/PromoProduct.tsx
export const PromoProduct: React.FC<{
  hook: string;
  scenes: { text: string; stat?: string }[];
  cta: string;
  brandColor: string;
}> = ({ hook, scenes, cta, brandColor }) => {
  // Animaciones predefinidas, layout fijo, solo cambia el contenido
};
```

**Pros**: Calidad consistente, identidad de marca, rapido de renderizar.
**Contras**: Necesitas diseñar cada template (una vez).

### Opcion C: Remotion Bits + Componentes Open Source

**Que es**: Componentes pre-hechos que puedes combinar.

**Recursos**:
- remotionbits.com — bloques de animacion gratuitos
- @remotion/transitions — fade, slide, wipe, flip, clock-wipe
- @remotion/google-fonts — 1500+ fuentes
- @remotion/animation-utils — scale, translateY, rotate helpers
- @remotion/layout-utils — fitText para texto responsive
- Lottie animations via @remotion/lottie

---

## Recomendacion: Hibrido (B + A)

1. **Diseña 3-4 templates base** con tu identidad visual (Opcion B)
2. **Usa prompt-to-motion-graphics** para variaciones creativas (Opcion A)
3. **El Scriptwriter de Agno** genera el contenido, no el diseño

---

## Templates Sugeridos para Tus Productos

### Template 1: `promo-product`
Para: Promocionar Whabi, Docflow, Aurora
Estilo: Fondo oscuro (#1a1a2e), accent color por producto, logo animado
Estructura:
```
Scene 1: Hook (texto kinetico grande, spring bounce)
Scene 2-4: Features (icono + texto, staggered entrance)
Scene 5: Stat/dato impactante (numero grande animado)
Scene 6: CTA + logo (fade in con branding)
```

### Template 2: `data-story`
Para: Presentar estadisticas, tendencias, research
Estilo: Graficos animados, numeros grandes, transiciones limpias
Estructura:
```
Scene 1: Pregunta hook ("Sabias que...?")
Scene 2-3: Datos con bar charts/pie charts animados
Scene 4: Insight (texto kinetico)
Scene 5: CTA
```

### Template 3: `explainer`
Para: Explicar conceptos, tutoriales, how-to
Estilo: Paso a paso, iconos animados, texto progresivo
Estructura:
```
Scene 1: Problema (texto + icono)
Scene 2-4: Solucion paso a paso (typewriter + iconos)
Scene 5: Resultado + CTA
```

### Template 4: `testimonial`
Para: Testimonios de clientes, social proof
Estilo: Quote grande, foto/avatar, estrellas animadas
Estructura:
```
Scene 1: Quote animado (typewriter)
Scene 2: Nombre + empresa + foto
Scene 3: Resultado/metrica
Scene 4: CTA
```

---

## Como Encaja en el Pipeline de Agno

### Flujo Actual (lo que tienes):
```
Trend Scout → Scriptwriter → genera JSON → MiniMax genera imagenes → Remotion renderiza
```

### Flujo Nuevo (motion graphics):
```
Trend Scout → Scriptwriter → genera JSON con template_id → Remotion usa template + datos
```

### Cambio en el Scriptwriter:

El JSON del Scriptwriter cambia de:
```json
{
  "scenes": [
    {"text": "...", "visual": "descripcion para AI image", "duration_seconds": 5}
  ]
}
```

A:
```json
{
  "template": "promo-product",
  "brand": "docflow",
  "hook": "Tu clinica aun usa papel?",
  "scenes": [
    {"text": "70% de clinicas usan papel", "stat": "70%", "icon": "document"},
    {"text": "Docflow digitaliza todo", "stat": null, "icon": "digital"},
    {"text": "Seguro y regulado", "stat": "100%", "icon": "shield"}
  ],
  "cta": "Sigue para mas",
  "accent_color": "#e94560"
}
```

**No hay campo `visual`** porque el template define el diseño.
**No se generan imagenes AI** porque el template usa motion graphics.
**El costo baja** porque no llamas a MiniMax Image-01.

### Cambio en Remotion:

En vez de un solo componente `AIVideo` que muestra imagenes, tienes multiples
compositions registradas:

```tsx
// Root.tsx
<Composition id="promo-product" component={PromoProduct} ... />
<Composition id="data-story" component={DataStory} ... />
<Composition id="explainer" component={Explainer} ... />
<Composition id="testimonial" component={Testimonial} ... />
```

El CLI lee el `template` del JSON y renderiza la composition correcta.

---

## Paso a Paso para Implementar

### Fase 1: Diseñar templates (1-2 dias)
1. Definir paleta de colores por producto (Whabi, Docflow, Aurora)
2. Elegir fuentes (Inter para body, una display font para hooks)
3. Diseñar el layout de cada template en papel/Figma
4. Codificar en React con Remotion

### Fase 2: Actualizar el pipeline (medio dia)
1. Cambiar el schema del Scriptwriter para incluir `template` y quitar `visual`
2. Actualizar el CLI para seleccionar composition por template
3. Eliminar la generacion de imagenes AI (ya no se necesita)

### Fase 3: Conectar con Agno (medio dia)
1. Actualizar instrucciones del Scriptwriter para usar templates
2. Agregar skill con los templates disponibles y sus campos
3. El Creative Director evalua las variantes basado en el template elegido

### Fase 4: Iterar
1. Renderizar videos de prueba
2. Ajustar animaciones y timing
3. Agregar templates nuevos segun necesidad

---

## Recursos

- Remotion docs: remotion.dev/docs
- Remotion Bits (componentes gratuitos): remotionbits.com
- Template prompt-to-motion-graphics: github.com/remotion-dev/template-prompt-to-motion-graphics-saas
- Remotion Showcase (ejemplos reales): remotion.dev/showcase
- Spring physics playground: remotion.dev/docs/spring
- TransitionSeries docs: remotion.dev/docs/transitions
