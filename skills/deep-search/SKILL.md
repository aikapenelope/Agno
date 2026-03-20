---
name: deep-search
description: Advanced web search strategies for maximizing information quality with minimal tool calls. Covers query engineering, source prioritization, snippet extraction, and gap identification.
metadata:
  tags: search, research, web, queries, sources, extraction
---

# Deep Search

You are a research agent performing web searches. This skill teaches you how
to extract maximum value from each search call.

## Query Engineering

Bad queries waste tool calls. Good queries find answers in 1-2 searches.

### Compound Queries (search more, call less)
Instead of multiple simple searches, use compound queries:

- Bad: `"EHR market"` (too vague, millions of results)
- Bad: `"EHR"` then `"EHR Latin America"` then `"EHR market size"` (3 calls for 1 topic)
- Good: `"EHR electronic health records market size Latin America 2025 2026 growth"`
- Good: `"digital health adoption hospitals Latin America statistics site:mckinsey.com OR site:statista.com"`

### Site-Targeted Queries
Use `site:` to go directly to high-quality sources:

| Data type | Target sites |
|---|---|
| Market data | `site:statista.com`, `site:grandviewresearch.com`, `site:mckinsey.com` |
| Tech news | `site:techcrunch.com`, `site:theverge.com`, `site:wired.com` |
| Company info | `site:crunchbase.com`, `site:linkedin.com/company` |
| Latam specific | `site:xataka.com`, `site:hipertextual.com`, `site:iadb.org` |
| Research | `site:arxiv.org`, `site:scholar.google.com`, `site:nature.com` |
| Government | `site:who.int`, `site:worldbank.org`, `site:cepal.org` |

### Language Strategy
- Global topics: search in English (more results, better sources)
- Latam-specific: search in Spanish AND English
- Combine: `"salud digital clinicas Latinoamerica" OR "digital health clinics Latin America"`

## Snippet Extraction

Search results include titles, URLs, and text snippets. Extract:

- **Numbers**: funding amounts, user counts, percentages, dates, growth rates
- **Names**: companies, people, products, technologies
- **Quotes**: any direct quotes in snippets are high-value
- **URLs**: save EVERY relevant URL as a source

Do NOT try to fetch or read full articles. Snippets from good queries contain
80% of the information you need. The other 20% is not worth the context cost.

## Source Quality Hierarchy

When multiple sources say different things, trust in this order:

1. **Primary sources**: company blogs, official announcements, press releases
2. **Data providers**: Statista, World Bank, WHO, government reports
3. **Tier 1 journalism**: TechCrunch, Reuters, Bloomberg, The Verge
4. **Industry analysis**: McKinsey, a16z, Sequoia, Gartner
5. **General journalism**: news aggregators, blogs, opinion pieces

If you only have sources from level 5, note low confidence in your output.

## Gap Identification

After each search, explicitly state what you DID NOT find:

```
FINDINGS:
- [fact 1 with source]
- [fact 2 with source]

GAPS:
- Could not find market size data for 2026
- No primary source for the 70% adoption claim
- Missing competitor pricing information
```

Gaps are as valuable as findings. They tell the next agent (or the reflector)
what to look for, and they tell the synthesizer what to flag as uncertain.

## Anti-Patterns (never do these)

- Searching the same topic with slightly different wording
- Fetching full articles when snippets have the answer
- Doing more than 2 searches without producing output
- Ignoring search results that contradict your hypothesis
- Reporting findings without source URLs
