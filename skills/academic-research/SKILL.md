---
name: academic-research
description: Strategies for finding and evaluating academic papers, preprints, and scientific literature. Covers arXiv, Google Scholar, PubMed, citation analysis, and distinguishing peer-reviewed from preprints.
metadata:
  version: "1.0.0"
  tags: [academic, papers, arxiv, scholar, research, citations]
---

# Academic Research

You are researching academic and scientific literature. This skill teaches you
how to find papers, evaluate their credibility, and extract key findings.

## Where to Search

| Source | Best For | Query Pattern |
|--------|----------|---------------|
| arXiv | AI/ML, CS, physics preprints | `"topic" site:arxiv.org` |
| Google Scholar | Cross-discipline, citation counts | `"topic" site:scholar.google.com` |
| PubMed | Medical, biomedical, health | `"topic" site:pubmed.ncbi.nlm.nih.gov` |
| Semantic Scholar | AI-powered paper discovery | `"topic" site:semanticscholar.org` |
| IEEE/ACM | Engineering, computing | `"topic" site:ieeexplore.ieee.org` |

## Evaluating Paper Credibility

| Signal | High Credibility | Low Credibility |
|--------|-----------------|-----------------|
| Venue | NeurIPS, ICML, Nature, JAMA | No venue, self-published |
| Citations | 50+ in 2 years | 0 citations after 1 year |
| Authors | Known researchers, university affiliation | Anonymous, no affiliation |
| Peer review | Published in journal/conference | arXiv-only preprint |
| Reproducibility | Code available, clear methodology | No code, vague methods |

**Rule: arXiv preprints are NOT peer-reviewed. Always note "preprint" when citing.**

## What to Extract from a Paper

1. **Key claim**: what does the paper argue? (1 sentence)
2. **Method**: how did they test it? (1 sentence)
3. **Result**: what numbers support the claim? (specific metrics)
4. **Limitation**: what did the authors acknowledge as limitations?
5. **Citation**: full reference with URL

## Output Format

PAPERS:
- **[Title]** ([Authors, Year](URL)) — [Key finding in 1 sentence]
  - Method: [brief]
  - Result: [specific metric]
  - Status: [peer-reviewed / preprint]
  - Citations: [count if available]

SYNTHESIS: [What the literature collectively says about this topic]

GAPS: [What hasn't been studied or is contradictory]
