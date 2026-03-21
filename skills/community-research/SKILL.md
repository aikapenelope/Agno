---
name: community-research
description: Strategies for researching community sentiment on Reddit, HackerNews, Twitter/X, and forums. Covers opinion mining, sentiment analysis, and signal extraction.
metadata:
  version: "1.0.0"
  tags: [reddit, hackernews, twitter, community, sentiment, forums]
---

# Community Research

You are researching what communities think about a topic, product, or technology.
This skill teaches you how to find real opinions, not marketing.

## Platform-Specific Query Patterns

### Reddit
- `"topic" site:reddit.com` — general search
- `"topic" site:reddit.com/r/programming` — specific subreddit
- `"topic" site:reddit.com inurl:comments` — find discussion threads (not just posts)
- Key subreddits by domain:
  - AI/ML: r/MachineLearning, r/LocalLLaMA, r/artificial
  - Dev tools: r/programming, r/webdev, r/devops
  - Startups: r/startups, r/SaaS, r/Entrepreneur
  - Latam tech: r/programacion, r/devBrasil

### HackerNews
- `"topic" site:news.ycombinator.com` — find HN discussions
- Look for: Show HN posts (launches), Ask HN (questions), comment threads
- HN comments are high-signal: technical, opinionated, experienced developers

### Twitter/X
- `"topic" site:x.com` or `"topic" site:twitter.com`
- Look for: threads from developers, launch announcements, complaint threads
- High-signal accounts: framework maintainers, DevRel, VCs, indie hackers

### Forums & Discord
- `"topic" site:discord.com` — Discord server discussions
- `"topic" site:community.xyz.com` — official community forums
- `"topic" site:stackoverflow.com` — technical Q&A

## What to Extract

### Sentiment Signals
| Signal | Positive | Negative | Neutral |
|--------|----------|----------|---------|
| Language | "love", "game-changer", "finally" | "broken", "unusable", "switched to" | "tried", "comparing", "looking at" |
| Actions | "deployed in production", "migrated to" | "migrated away from", "gave up" | "evaluating", "POC" |
| Engagement | High upvotes + supportive comments | High upvotes + complaint comments | Low engagement |

### What matters most
1. **Production usage stories** > opinions (someone actually using it > someone who read about it)
2. **Complaints with specifics** > vague praise (specific bugs = real usage)
3. **Comparisons** > standalone reviews (X vs Y reveals real tradeoffs)
4. **Recent posts** > old posts (communities change fast)

## Output Format

COMMUNITY_FINDINGS:
- **[Finding]** ([Platform](URL)) — [What this signals]

SENTIMENT: [positive/mixed/negative/too-early]
SAMPLE_SIZE: [how many discussions/posts found]
CONFIDENCE: [high if 10+ sources, medium if 3-9, low if 1-2]

KEY_QUOTES:
- "[exact quote]" — [username], [platform], [date]

GAPS: [what community data you couldn't find]
