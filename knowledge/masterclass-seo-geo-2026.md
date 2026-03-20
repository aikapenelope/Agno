# Masterclass SEO + GEO 2026

Guia completa para posicionar contenido en Google y en motores de busqueda
AI (ChatGPT, Perplexity, Gemini, Google AI Overviews). Basada en datos de
Q1 2026.

---

## Parte 1: El Nuevo Panorama de Busqueda

### Los numeros que importan

- 40% de busquedas ahora pasan por AI (ChatGPT, Perplexity, Claude, Gemini)
- 50%+ de busquedas en Google muestran AI Overviews en Q1 2026
- 65% de busquedas en Google terminan sin click (zero-click)
- CTR organico cae 61% en queries con AI Overview
- PERO: si tu marca es citada en el AI Overview, CTR organico sube 35%
- AI-referred sessions crecieron 527% year-over-year en 2025
- Reddit recibio 600%+ mas trafico desde 2023 — AI favorece UGC

### Las 3 disciplinas de visibilidad

| Disciplina | Objetivo | Donde |
|---|---|---|
| **SEO** | Rankear en resultados de Google | Blue links, Featured Snippets |
| **AEO** | Ser la respuesta directa | Knowledge Panels, Voice Search |
| **GEO** | Ser citado por AI | ChatGPT, Perplexity, AI Overviews |

Las tres se complementan. Un articulo bien hecho puede rankear en Google,
aparecer como Featured Snippet, Y ser citado por ChatGPT.

---

## Parte 2: GEO — Generative Engine Optimization

### Como los AI eligen que citar

Cuando un usuario pregunta algo a ChatGPT o Perplexity:

1. **Retrieval**: El AI busca en la web (o en su indice) fuentes relevantes
2. **Evaluacion**: Evalua autoridad, relevancia, frescura, y precision
3. **Sintesis**: Combina informacion de multiples fuentes
4. **Citacion**: Cita las fuentes que mas contribuyeron a la respuesta

### Que contenido citan los AI (datos reales)

De un analisis de 129,000+ citaciones de ChatGPT:

- **74.2%** de citaciones AI vienen de contenido en formato listicle ("Top N", "Best X")
- **0%** de citaciones vienen de paginas de servicio o landing pages
- **0%** de citaciones vienen de case studies standalone
- **44.2%** de citaciones vienen del primer 30% del texto (la intro)
- Contenido de 2,900+ palabras recibe 5.1 citaciones promedio vs 3.2 para contenido corto
- Secciones de 120-180 palabras por heading son el sweet spot

### Fuentes mas citadas por plataforma

| Plataforma | Fuente #1 | Fuente #2 |
|---|---|---|
| ChatGPT | Wikipedia (47.9%) | News sites |
| Perplexity | Reddit (46.7%) | News sites |
| Google AI Overviews | Sitios con schema markup | Reddit, forums |

### Lo que NO funciona para GEO

- Paginas de producto/servicio (0 citaciones)
- Contenido promocional ("premier", "best-in-class", "revolutionary")
- Contenido sin fuentes verificables
- Contenido viejo (efecto "citation cliff" a los 3 meses)
- Informacion contradictoria entre tu sitio y otras fuentes

---

## Parte 3: Las 12 Tacticas GEO Validadas

### Tactica 1: Formato Listicle Obligatorio

100% de las paginas citadas por AI en datos de GenOptima usaban formato
"Top N" o "Best X". No hay excepcion.

Requisitos:
- Entradas numeradas con posicion explicita
- Estructura consistente por entrada: nombre, diferenciador, evidencia
- Minimo 7 entradas para señal de cobertura
- Tabla comparativa resumiendo todas las entradas
- Seccion de metodologia

### Tactica 2: Quick Answer + Deep Dive

Cada pagina debe tener dos capas:

**Capa 1 — Quick Answer (primeras 200 palabras)**:
- Lista numerada de top entries con descripcion de 1 linea
- Sin imagenes, links, ni formato que rompa la extraccion
- Heading claro: "Quick Answer: Top [N] [Categoria]"

**Capa 2 — Deep Dive (resto del articulo)**:
- Analisis detallado de cada entrada
- Evidencia con atribucion de fuentes
- Tablas comparativas
- Seccion FAQ

### Tactica 3: Densidad de Evidencia

AI filtra contenido promocional. Reemplazar lenguaje de marketing con datos
verificables.

Palabras que activan deteccion de publicidad (evitar):
- "Premier", "lider", "best-in-class", "revolucionario"
- "Soluciones innovadoras", "de clase mundial"
- Superlativos sin datos que los respalden

Reemplazar con:
- Numeros especificos con fuente
- Comparaciones directas con competidores
- Datos de terceros (Gartner, Statista, reportes de industria)

### Tactica 4: FAQ Alineadas con Prompts de AI

Las preguntas del FAQ deben coincidir con lo que los usuarios preguntan
a ChatGPT/Perplexity. No inventar preguntas — investigar queries reales.

Ejemplo para EHR:
- "Que es un EHR?" (query exacta en ChatGPT)
- "Cuanto cuesta implementar un EHR?" (query exacta)
- "Es obligatorio tener EHR en Mexico?" (query exacta)

### Tactica 5: Frescura (7-14 dias)

Ciclos de actualizacion de 7-14 dias son obligatorios. Incluir:
- Fecha de publicacion visible
- Fecha de ultima actualizacion
- "Verificado en marzo 2026" o similar
- Version history si es posible

### Tactica 6: Schema JSON-LD Triple

Cada pagina de ranking debe tener 3 schemas apilados:
- `Article` — identifica el contenido como articulo
- `ItemList` — estructura la lista de entradas
- `FAQPage` — estructura las preguntas frecuentes

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Article",
      "headline": "Top 7 EHR para Clinicas en Latam 2026",
      "datePublished": "2026-03-19",
      "dateModified": "2026-03-19",
      "author": {"@type": "Organization", "name": "Aika Labs"}
    },
    {
      "@type": "ItemList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Docflow"},
        {"@type": "ListItem", "position": 2, "name": "Nubimed"}
      ]
    },
    {
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "Que es un EHR?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Un EHR es un sistema digital para..."
          }
        }
      ]
    }
  ]
}
```

### Tactica 7: Consistencia Cross-Source

AI detecta inconsistencias entre fuentes y baja confianza. Asegurar que
la misma informacion aparezca igual en:
- Tu sitio web
- Reddit posts
- LinkedIn
- Crunchbase
- Google Business Profile

### Tactica 8: Distribucion en Canales de Alto Pickup

AI cita contenido que encuentra en multiples fuentes. Distribuir en:
- Reddit (r/healthIT, r/SaaS, r/whatsapp) — 46.7% de citaciones en Perplexity
- Quora — respuestas con datos y links
- Medium / Dev.to — articulos tecnicos
- LinkedIn — posts con datos de industria

### Tactica 9: Publicacion Consistente

1-2 listicles nuevos por semana. La velocidad de publicacion acumula
citaciones. No es un sprint — es un ritmo sostenido.

### Tactica 10: Monitoreo en 6 Plataformas

Monitorear citaciones en:
1. ChatGPT
2. Perplexity
3. Google AI Overviews
4. Google AI Mode
5. Microsoft Copilot
6. Gemini

53.6% de respuestas de ChatGPT no incluyen fuentes web — filtrar en analytics.

### Tactica 11: E-E-A-T (Experience, Expertise, Authority, Trust)

Señales que AI busca:
- Bio del autor con credenciales
- Fuentes autoritativas citadas
- Investigacion original y datos propios
- Cobertura tematica comprehensiva (topical authority)

### Tactica 12: Optimizar para Bottom Funnel

Dato contraintuitivo: el contenido bottom funnel (case studies, pricing,
comparativas) recibe MAS trafico de AI referral que el top funnel
(guias "que es", "como hacer"). Los usuarios que llegan desde AI ya
investigaron — quieren decidir, no aprender.

---

## Parte 4: SEO Clasico en 2026

### Lo que sigue funcionando

- **Contenido de calidad**: largo, profundo, con datos
- **Backlinks**: siguen siendo señal de autoridad
- **Technical SEO**: Core Web Vitals, mobile-first, HTTPS
- **Schema markup**: JSON-LD con @id graph model
- **Internal linking**: estructura de silos tematicos

### Lo que cambio

- **Zero-click es la norma**: optimizar para impresiones, no solo clicks
- **AI Overviews**: aparecer ahi es mas valioso que posicion #1
- **CTR organico cayo 61%** en queries con AI Overview
- **Reddit y UGC**: Google y AI favorecen contenido de comunidad
- **Frescura**: contenido viejo pierde posiciones mas rapido

### Estructura de URL recomendada

```
aikalabs.cc/                    → landing page con schema Organization
aikalabs.cc/docflow             → pagina de producto con schema SoftwareApplication
aikalabs.cc/whabi               → pagina de producto
aikalabs.cc/aurora              → pagina de producto
aikalabs.cc/blog/               → indice del blog
aikalabs.cc/blog/top-ehr-2026   → articulo listicle con schema Article+ItemList+FAQ
```

Subfolder, no subdomain. Toda la autoridad se acumula en un dominio.

---

## Parte 5: Medicion

### Metricas GEO

- **Citation frequency**: cuantas veces te citan los AI por semana
- **Citation position**: en que posicion apareces en la lista de fuentes
- **Prompt coverage**: de N queries monitoreadas, en cuantas apareces
- **AI referral traffic**: visitas desde ChatGPT, Perplexity (ver en GA4)

### Metricas SEO

- **Organic traffic**: visitas desde Google
- **Keyword rankings**: posiciones para keywords target
- **CTR**: click-through rate en Search Console
- **AI Overview presence**: apareces en AI Overviews?

### Herramientas

- Google Search Console (gratis)
- GA4 con filtro de AI referral (gratis)
- Ahrefs o SEMrush (keyword tracking)
- GenOptima o similar (GEO citation tracking)

---

## Parte 6: Plan de Accion Semanal

| Dia | Accion |
|---|---|
| Lunes | Publicar 1 articulo listicle nuevo |
| Martes | Distribuir en Reddit + LinkedIn |
| Miercoles | Actualizar 1 articulo existente (frescura) |
| Jueves | Publicar 1 articulo listicle nuevo |
| Viernes | Revisar metricas: citaciones AI, trafico, rankings |
| Sabado | Investigar keywords para proxima semana |

---

## Aplicacion a Aika Labs

### Temas prioritarios para GEO

| Producto | Articulo Listicle | Target Query en AI |
|---|---|---|
| Docflow | "Top N EHR para clinicas en Latam" | "mejores sistemas EHR latinoamerica" |
| Docflow | "Comparativa software historia clinica electronica" | "que EHR usar para mi clinica" |
| Whabi | "Mejores CRM para WhatsApp Business" | "mejor CRM whatsapp business" |
| Whabi | "Como automatizar WhatsApp para ventas" | "automatizar whatsapp ventas" |
| Aurora | "Apps voice-first para negocios" | "aplicaciones voz negocios" |
| General | "Software de IA para salud en Latam" | "inteligencia artificial salud latinoamerica" |

### Ventaja competitiva

La mayoria de estos temas NO tienen buenos articulos en español. La
competencia en GEO para contenido en español es baja comparada con ingles.
Publicar primero = capturar citaciones antes que la competencia.
