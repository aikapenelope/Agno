# Context Engineering Reference

Source: Advanced Context Engineering for Coding Agents (HumanLayer),
12-Factor Agents (HumanLayer), AI That Works (BoundaryML).

## The Core Insight

LLMs are stateless functions: context window in, next step out.
The context window is the ONLY lever to affect output quality.

Priority order for context:
1. Correctness — bad information is the worst failure
2. Completeness — missing information is second worst
3. Size — noise degrades performance (keep context at 40-60% utilization)
4. Trajectory — directional coherence matters

## What Consumes Context (avoid these)

- File searching and globbing (use targeted queries instead)
- Reading full articles (use search snippets)
- Large JSON tool outputs (extract only what you need)
- Repeated similar searches (diminishing returns)
- History from unrelated sessions (disable when not needed)

## The Research → Plan → Act Pattern

Phase 1 — Research: Understand the problem space. Output is structured findings.
Phase 2 — Plan: Precise steps with verification criteria.
Phase 3 — Act: Execute the plan. One step at a time.

Human review is most valuable at the PLAN stage, not the output stage.
A bad plan leads to hundreds of bad outputs. A bad output is localized damage.

## Error Compaction (12-Factor #9)

When something fails, fold the error back into context as structured information:
- What was attempted
- What failed
- What the error message said
- What to try differently

Do NOT retry blindly. Do NOT ignore errors. Compact them and adapt.

## Backpressure

If you're generating more work than the next step can handle, slow down.
Signs of missing backpressure:
- Looping 7 times when once would suffice
- Generating 20 search results when 3 are enough
- Producing output that the user can't review in reasonable time

The fix: explicit limits in instructions, deterministic workflows over
open-ended coordination, route mode over coordinate mode.
