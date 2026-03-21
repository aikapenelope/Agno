---
name: github-research
description: Strategies for researching GitHub repositories, organizations, PRs, issues, and code. Covers repo analysis, contributor patterns, release tracking, and OSS health assessment.
metadata:
  version: "1.0.0"
  tags: [github, oss, code, repositories, research]
---

# GitHub Research

You are researching software projects on GitHub. This skill teaches you how
to extract maximum insight from GitHub searches.

## Query Patterns

### Finding repositories
- `"project-name" site:github.com` — find the main repo
- `org:langchain-ai "deep agents"` — search within an organization
- `"project-name" stars:>1000` — filter by popularity
- `"project-name" pushed:>2025-01-01` — filter by recent activity

### Finding PRs and issues
- `"feature-name" site:github.com/org/repo/pulls` — search PRs
- `"bug" site:github.com/org/repo/issues` — search issues
- `is:pr is:merged label:feature` — merged feature PRs

### Finding code
- `"function_name" language:python site:github.com/org` — find implementations
- `filename:requirements.txt "package-name"` — find who uses a package

## What to Extract from a Repository

When analyzing a repo, extract these in order:

1. **README**: project description, architecture, getting started
2. **Stars/Forks/Issues**: health indicators
3. **Recent PRs**: what's being actively developed (last 30 days)
4. **Release notes**: what shipped recently
5. **Open issues with most reactions**: what the community wants
6. **Contributors**: who's building it (company vs community)

## Health Assessment

| Signal | Healthy | Warning | Dead |
|--------|---------|---------|------|
| Last commit | < 7 days | 7-90 days | > 90 days |
| Open issues response | < 48h | 48h-2w | > 2 weeks |
| PR merge time | < 1 week | 1-4 weeks | > 1 month |
| Stars trend | Growing | Flat | Declining |
| Bus factor | 3+ active contributors | 2 | 1 |

## Output Format

REPOSITORY: [name] ([URL])
STARS: [count] | FORKS: [count] | OPEN_ISSUES: [count]
LAST_COMMIT: [date]
HEALTH: [healthy/warning/stale]

KEY_FINDINGS:
- [finding with URL to specific PR/issue/release]

ARCHITECTURE: [brief description of how it's built]

RECENT_ACTIVITY: [what's being worked on in last 30 days]

COMMUNITY: [who's building it, company vs community driven]
