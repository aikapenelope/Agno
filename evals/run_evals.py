"""
NEXUS Evals - Evaluation suite for agent quality.
==================================================

Runs test cases against NEXUS agents and teams to measure:
- Accuracy: Does the agent produce correct/relevant output?
- Reliability: Does it call the right tools?
- Performance: How fast is it?

Uses Groq llama-3.1-8b-instant as the LLM judge (cheap, fast).

Usage:
    python -m evals.run_evals
    python -m evals.run_evals --category content
    python -m evals.run_evals --verbose
"""

import argparse
import time
import sys
from pathlib import Path

# Add project root to path so we can import nexus modules.
sys.path.insert(0, str(Path(__file__).parent.parent))

from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.groq import Groq

# LLM judge: llama-3.1-8b-instant on Groq (560 tps, $0.05/M input).
EVAL_MODEL = Groq(id="llama-3.1-8b-instant")


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestCase:
    def __init__(
        self,
        name: str,
        category: str,
        agent_name: str,
        input_text: str,
        expected_output: str,
        guidelines: str = "",
    ):
        self.name = name
        self.category = category
        self.agent_name = agent_name
        self.input_text = input_text
        self.expected_output = expected_output
        self.guidelines = guidelines


TEST_CASES = [
    # --- Content pipeline ---
    TestCase(
        name="trend_scout_finds_topic",
        category="content",
        agent_name="trend_scout",
        input_text="Find the most relevant AI trend today for a Spanish-language tech content brand.",
        expected_output="A content brief with a topic, key facts with numbers, sources with URLs, and hook ideas in Spanish.",
        guidelines="Must include at least 2 source URLs. Hooks must be in Spanish. Must have a relevance score.",
    ),
    TestCase(
        name="scriptwriter_generates_storyboard",
        category="content",
        agent_name="scriptwriter",
        input_text=(
            "Create a video storyboard about: AI is now being used in hospitals "
            "in Latin America to detect cancer earlier. 70% accuracy improvement. "
            "Source: WHO report 2026. Hook: 'La IA ya salva vidas en hospitales'"
        ),
        expected_output="A VideoStoryboard JSON with title, hook, scenes (5-6), hashtags, CTA, saved to a file.",
        guidelines=(
            "Must be valid JSON. Must have 5-6 scenes. Text must be in Spanish. "
            "Visual descriptions must be concise (under 20 words each). "
            "Must include a save_file tool call."
        ),
    ),
    # --- Research ---
    TestCase(
        name="research_agent_web_search",
        category="research",
        agent_name="research_agent",
        input_text="What are the latest developments in EHR systems in Latin America?",
        expected_output="A research summary with key findings, specific data points, and source URLs.",
        guidelines="Must include at least 1 source URL. Must mention specific countries or companies.",
    ),
    TestCase(
        name="knowledge_agent_internal",
        category="research",
        agent_name="knowledge_agent",
        input_text="What do we know about Docflow's architecture?",
        expected_output="Information about Docflow: PostgreSQL database, Redis DB 1, MinIO bucket, deployment on Coolify.",
        guidelines="Must reference internal knowledge. Should mention PostgreSQL and the data plane.",
    ),
    # --- Automation ---
    TestCase(
        name="automation_agent_crm",
        category="automation",
        agent_name="automation_agent",
        input_text="List all companies in the CRM.",
        expected_output="A list of companies from Twenty CRM or a message that the CRM is not configured.",
        guidelines="Must attempt to use a CRM tool or explain that the tool is not available.",
    ),
]


def get_agent(name: str):
    """Import and return an agent by name."""
    from nexus import (
        trend_scout,
        scriptwriter,
        research_agent,
        knowledge_agent,
        automation_agent,
    )

    agents = {
        "trend_scout": trend_scout,
        "scriptwriter": scriptwriter,
        "research_agent": research_agent,
        "knowledge_agent": knowledge_agent,
        "automation_agent": automation_agent,
    }
    return agents.get(name)


def run_evals(category: str | None = None, verbose: bool = False) -> None:
    """Run evaluation suite."""
    tests = TEST_CASES
    if category:
        tests = [t for t in tests if t.category == category]

    if not tests:
        print(f"No tests found for category: {category}")
        return

    print(f"\n=== NEXUS Evals: {len(tests)} tests ===\n")

    results: list[dict] = []
    total_start = time.time()

    for i, tc in enumerate(tests):
        print(f"[{i + 1}/{len(tests)}] {tc.name} ({tc.agent_name})...", end=" ", flush=True)
        start = time.time()

        agent = get_agent(tc.agent_name)
        if not agent:
            print("SKIP (agent not found)")
            results.append({"name": tc.name, "status": "SKIP", "duration": 0})
            continue

        try:
            evaluation = AccuracyEval(
                model=EVAL_MODEL,
                agent=agent,
                input=tc.input_text,
                expected_output=tc.expected_output,
                additional_guidelines=tc.guidelines,
            )
            result: AccuracyResult = evaluation.run(print_results=False)
            duration = time.time() - start

            status = "PASS" if result.passed else "FAIL"
            print(f"{status} ({duration:.1f}s) score={result.score:.2f}")

            if verbose and not result.passed:
                print(f"  Reason: {result.reason}")

            results.append({
                "name": tc.name,
                "status": status,
                "duration": duration,
                "score": result.score,
                "reason": result.reason,
            })

        except Exception as e:
            duration = time.time() - start
            print(f"ERROR ({duration:.1f}s): {e}")
            results.append({
                "name": tc.name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e),
            })

    # Summary
    total_duration = time.time() - total_start
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    print(f"\n=== Summary ({total_duration:.1f}s) ===")
    print(f"  PASS: {passed}/{len(results)}")
    if failed:
        print(f"  FAIL: {failed}")
    if errors:
        print(f"  ERROR: {errors}")
    if skipped:
        print(f"  SKIP: {skipped}")

    scores = [r["score"] for r in results if "score" in r]
    if scores:
        print(f"  Avg score: {sum(scores) / len(scores):.2f}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run NEXUS evaluations")
    parser.add_argument(
        "--category", "-c",
        choices=["content", "research", "automation"],
        help="Filter by category",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show failure reasons")
    args = parser.parse_args()

    run_evals(category=args.category, verbose=args.verbose)
