---
name: prompt-patterns
description: Advanced prompting patterns for getting better results from LLMs — chain-of-thought, few-shot, self-consistency, and structured output techniques.
metadata:
  version: "1.0.0"
  tags: [prompting, llm, patterns, chain-of-thought, few-shot]
---

# Prompt Patterns

Advanced techniques for getting better results from LLMs. Load this skill
when you need to improve the quality of a response or handle a complex task.

## When to Use Each Pattern

| Pattern | Use When | Example |
|---------|----------|---------|
| **Chain-of-thought** | Complex reasoning, math, multi-step logic | "Think step by step about..." |
| **Few-shot** | You need a specific output format | Provide 2-3 examples first |
| **Self-consistency** | High-stakes decisions, need confidence | Generate 3 answers, pick majority |
| **Structured output** | Data extraction, API responses | Define exact JSON/table format |
| **Role prompting** | Domain expertise needed | "You are a senior data analyst..." |

## Chain-of-Thought

Force step-by-step reasoning before the final answer:

```
Analyze this lead and score them 1-10:

Step 1: What product are they interested in?
Step 2: How many interactions have they had?
Step 3: Did they ask about pricing?
Step 4: What's their company size?
Step 5: Based on steps 1-4, assign a score.
```

Use when: math, logic, multi-factor decisions, debugging.

## Few-Shot Examples

Show the model exactly what you want:

```
Extract the key metric from each sentence:

Input: "Revenue grew 23% year-over-year to $4.2M"
Output: {"metric": "revenue", "value": "$4.2M", "change": "+23% YoY"}

Input: "Monthly active users declined to 50,000 from 65,000"
Output: {"metric": "MAU", "value": "50,000", "change": "-23% from 65,000"}

Input: "The company raised a $15M Series A"
Output:
```

Use when: specific format needed, extraction tasks, classification.

## Structured Output

Define the exact format before asking:

```
Respond in this exact format:

FINDING: [one sentence]
SOURCE: [URL]
CONFIDENCE: [high/medium/low]
ACTION: [what to do about it]
```

Use when: output will be parsed by another agent or system.

## Anti-Patterns

- "Be creative" (too vague, produces inconsistent results)
- "Write a comprehensive analysis" (no structure = rambling)
- "Do your best" (the model always does its best, this adds nothing)
- Long instructions without examples (show, don't just tell)
- Asking for "all" of something (always specify a number: "top 5", "3 examples")
