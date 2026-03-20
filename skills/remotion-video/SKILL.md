---
name: remotion-video
description: Programmatic video production using Remotion templates. Generates JSON content for pre-designed motion graphics templates — no AI images needed.
metadata:
  tags: remotion, video, react, animation, rendering, production, templates
---

# Remotion Video Production

You produce JSON content for Remotion motion graphics templates. You do NOT
generate image descriptions — the templates handle all visuals with React
animations.

## Available Templates

| Template | ID | Input Fields |
|---|---|---|
| **PromoProduct** | `promo-product` | brand, hook, features[], stat, cta |
| **DataStory** | `data-story` | hook, data_points[], insight, cta |
| **Explainer** | `explainer` | hook, steps[], conclusion, cta |
| **TikTok Captions** | `tiktok` | video_url, language |

## How to Generate Content

For each video, produce a JSON with:
1. `template` — which template to use (from table above)
2. `brand` — which product (docflow, whabi, aurora)
3. Content fields specific to the template

### PromoProduct JSON
```json
{
  "template": "promo-product",
  "brand": "docflow",
  "hook": "Tu clinica aun usa papel?",
  "features": [
    {"text": "Digitaliza historias clinicas", "icon": "📱"},
    {"text": "Cumple regulaciones de salud", "icon": "🛡️"},
    {"text": "Conecta toda la clinica", "icon": "🔗"}
  ],
  "stat": {"number": "70%", "label": "menos papeleo"},
  "cta": "Prueba Docflow gratis"
}
```

## Rules

- NEVER include a `visual` field — templates handle visuals
- NEVER describe images — there are no AI-generated images
- Keep text SHORT: max 10 words per feature, max 8 words per hook
- Each variant should have a DIFFERENT hook and angle
- Save JSON files to: public/content/<slug>.json
- Brand colors are automatic based on the `brand` field

## Brand Reference

| Brand | Accent Color | Tagline |
|---|---|---|
| docflow | #e94560 | Tu clinica, sin papel |
| whabi | #25D366 | WhatsApp Business CRM |
| aurora | #8B5CF6 | Voice-first para negocios |
