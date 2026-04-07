---
name: obsidian-vault
description: Guide for using the Obsidian vault MCP tools. Read, write, search, and organize notes. Available to all agents.
metadata:
  version: "1.0.0"
  tags: [obsidian, notes, knowledge, vault, mcp]
---

# Obsidian Vault — MCP Tools Reference

The Obsidian vault is your team's knowledge base. All agents have access to read, write, and search notes.

## MCP Tools

| Tool | What it does | When to use |
|------|-------------|-------------|
| `read_note` | Read a specific note by path | When you need the content of a known note |
| `write_note` | Create or update a note | Save meeting notes, decisions, documentation |
| `search_notes` | Full-text search across all notes | Find information on any topic |
| `list_directory` | List files in a folder | Browse vault structure |
| `get_frontmatter` | Read YAML frontmatter of a note | Check tags, dates, metadata |
| `manage_tags` | Add or remove tags from a note | Organize and categorize notes |

## When to Use Obsidian

| Situation | Action |
|-----------|--------|
| User asks "what do we know about X" | `search_notes` first |
| User says "save this" or "remember this" | `write_note` |
| User asks about a meeting, decision, or process | `search_notes` then `read_note` |
| User wants to organize notes | `manage_tags` or `list_directory` |
| Before answering a knowledge question | `search_notes` to check if we have internal info |

## Note Format

Notes are Markdown files with optional YAML frontmatter:

```markdown
---
tags: [meeting, whabi, q1-2026]
date: 2026-03-25
---

# Meeting: Whabi Q1 Review

## Attendees
- Angel, Maria, Pedro

## Decisions
- Launch pro plan in April
- Hire 2 support agents

## Action Items
- [ ] Pedro: prepare pricing page
- [ ] Maria: onboard new agents
```

## Folder Structure

```
vault/
├── meetings/          → Meeting notes
├── decisions/         → Key decisions and rationale
├── projects/          → Project documentation
│   ├── whabi/
│   ├── docflow/
│   └── aurora/
├── clients/           → Client-specific notes
├── processes/         → SOPs and workflows
├── learnings/         → Insights and patterns
└── daily/             → Daily notes and logs
```

## Search Patterns

### Find meeting notes
```
search_notes query="meeting whabi"
```

### Find decisions about pricing
```
search_notes query="pricing decision"
```

### Find client information
```
search_notes query="Pedro Gomez" 
```

### Find all notes with a tag
```
search_notes query="tag:whabi"
```

## Writing Notes

### Save a meeting summary
```
write_note path="meetings/2026-03-25-whabi-review.md" content="---\ntags: [meeting, whabi]\ndate: 2026-03-25\n---\n\n# Whabi Q1 Review\n\n..."
```

### Save a client interaction
```
write_note path="clients/pedro-gomez.md" content="# Pedro Gomez\n\nEmpresa: Nexus\nProducto: Whabi\n\n## Interacciones\n- 2026-03-25: Pregunto por plan pro..."
```

### Save a decision
```
write_note path="decisions/2026-03-pricing.md" content="# Pricing Update March 2026\n\nDecision: Increase pro plan to $59/month\nReason: Added AI features..."
```

## Important Rules

1. **ALWAYS search before writing** — check if a note already exists before creating a duplicate.
2. **Use descriptive file names** — `meetings/2026-03-25-whabi-review.md` not `note1.md`.
3. **Include frontmatter** — tags and dates help with organization and search.
4. **Use folders** — put notes in the right folder based on type.
5. **Link related notes** — use `[[note-name]]` syntax to connect related notes.
6. **Keep notes concise** — bullet points over paragraphs. Action items as checkboxes.
