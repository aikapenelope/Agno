---
name: market-intelligence
description: Strategies for researching market data, competitor analysis, pricing intelligence, and industry trends. Covers data source hierarchy, metric extraction, and competitive positioning.
metadata:
  version: "1.0.0"
  tags: [market, competitors, pricing, trends, data, intelligence]
---

# Market Intelligence

You are researching market data, competitors, or industry trends.
This skill teaches you how to find reliable numbers and competitive insights.

## Data Source Hierarchy (trust in this order)

1. **Company filings**: SEC 10-K/10-Q, annual reports (most reliable)
2. **Research firms**: Statista, Gartner, McKinsey, a16z (reliable but may be paywalled)
3. **Crunchbase/PitchBook**: funding, valuations, team size (reliable for startups)
4. **Industry reports**: World Bank, WHO, CEPAL, IDB (reliable for macro data)
5. **News articles**: TechCrunch, Bloomberg, Reuters (reliable for events, less for numbers)
6. **Blog posts**: company blogs, Medium (verify independently)
7. **Social media**: Twitter threads, Reddit (anecdotal, not authoritative)

## Query Patterns for Market Data

### Market size and growth
- `"[industry] market size 2025 2026" site:statista.com OR site:grandviewresearch.com`
- `"[industry] CAGR growth rate forecast"`
- `"[industry] TAM SAM SOM"`

### Competitor analysis
- `"[competitor] funding round 2025 2026" site:crunchbase.com`
- `"[competitor] vs [competitor] comparison review"`
- `"[competitor] pricing plans" site:[competitor].com`
- `"[competitor] customers case study"`

### Pricing intelligence
- `"[product category] pricing comparison 2026"`
- `"[competitor] pricing page" site:[competitor].com/pricing`
- `"[product] free tier vs paid"`

### Latam-specific data
- `"[industry] Latin America" site:iadb.org OR site:cepal.org`
- `"[industry] mercado latinoamerica estadisticas"`
- `"transformacion digital [country]" site:worldbank.org`

## What to Extract

For every number, capture:
- **The metric**: what exactly is being measured
- **The value**: specific number with units
- **The source**: who published it and when
- **The date**: when was this data collected (not published)
- **The scope**: geographic, industry, company-specific

## Output Format

MARKET_DATA:
- **[Metric: value]** ([Source](URL), [date]) — [What this means]

COMPETITIVE_LANDSCAPE:
| Company | Product | Pricing | Key Differentiator |
|---------|---------|---------|-------------------|
| [name]  | [product] | [price] | [what makes them different] |

TRENDS:
- [Trend 1 with supporting data]
- [Trend 2 with supporting data]

GAPS: [What data was unavailable or unreliable]
CONFIDENCE: [high/medium/low based on source quality]
