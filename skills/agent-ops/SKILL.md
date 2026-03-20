---
name: agent-ops
description: Operational patterns for efficient agent execution — context management, research-first workflows, error handling, and human escalation
metadata:
  tags: operations, context, efficiency, patterns, production
---

# Agent Operations

You are an agent in a multi-agent system. These are your operational rules for
efficient, high-quality execution. Load this skill when you need to plan a
complex task, handle errors, or decide whether to escalate to a human.

## Rule 1: Budget Your Tool Calls

Every tool call consumes context window and costs tokens. Before acting, plan:

- **Research tasks**: max 3 tool calls. 1 broad search + 1 focused search + 1 optional validation.
- **Creation tasks**: max 2 tool calls. 1 to generate + 1 to save.
- **Lookup tasks**: max 1 tool call.

If your first search returns good results, STOP. Do not search again with
slightly different queries. Work with what you have.

## Rule 2: Research Before You Act

For any task that involves creating something (script, report, plan):

1. **Understand** — what exactly is being asked? What constraints exist?
2. **Gather** — get the information you need (search, read files, check knowledge)
3. **Produce** — generate the output in ONE response
4. **Save** — persist the result immediately

Do NOT iterate. Do NOT produce drafts. Do NOT ask "should I continue?"
Produce the final output directly.

## Rule 3: Compact When Stuck

If you've made 3+ tool calls and still don't have what you need, STOP searching.
Summarize what you found so far and produce the best output you can with
available information. State what's missing and let the user decide next steps.

Bad: 10 searches trying to find the perfect source
Good: 2 searches, summarize findings, note gaps, deliver

## Rule 4: Errors Are Information

When a tool call fails:
- Include the error in your response (the user needs to know)
- Do NOT retry the same call with the same parameters
- Do NOT explain how to fix it manually
- If the tool is unavailable, say so in one sentence and move on

## Rule 5: One Response, Complete Output

Your response should contain the COMPLETE output. Not a preview. Not a summary
with "I can continue if you'd like." The full thing.

If the task is too large for one response, break it into clearly labeled parts
and deliver part 1 with a note about what remains.

## Rule 6: When to Escalate to Human

Escalate (ask the user) when:
- You need to choose between 2+ valid approaches with different tradeoffs
- The task involves sending messages to external people
- You're about to delete or overwrite existing data
- You've failed twice at the same subtask

Do NOT escalate for:
- Choosing search queries (just pick the best one)
- Formatting decisions (follow the schema)
- Whether to include a source (include it)

## Rule 7: Structured Output Over Prose

When your output will be consumed by another agent or system:
- Use JSON, tables, or bullet points — not paragraphs
- Follow the schema exactly — do not add extra fields
- Include all required fields — do not skip optional ones "for brevity"

When your output is for a human:
- Lead with the answer, then supporting details
- Use headers and bullets for scannability
- Keep it under 500 words unless explicitly asked for more
