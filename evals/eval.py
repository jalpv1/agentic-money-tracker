"""uv run python -m evals.eval [-k substring] [--repeats 3]"""
import argparse
from collections import defaultdict

import evals                       # noqa: F401  (sets the temp DB path first)
from evals import data
from evals.cases import CASES
from evals.runner import run_case


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", default="")
    ap.add_argument("--repeats", type=int, default=1)
    args = ap.parse_args()

    from src.agent.agent import build_agent      # import after the env var is set
    data.fill_db()
    app = build_agent()

    per_family = defaultdict(lambda: [0, 0])
    failures, total_secs, runs = [], 0.0, 0
    for case in [c for c in CASES if args.k in c.name]:
        passes = 0
        for _ in range(args.repeats):
            run = run_case(app, case)
            total_secs += run.seconds
            runs += 1
            verdicts = [chk(run, case) for chk in case.checks]
            ok = run.error is None and all(v.ok for v in verdicts)
            passes += ok
            if not ok:
                failures.append((case, run, [v.reason for v in verdicts if not v.ok]))
        per_family[case.family][0] += passes
        per_family[case.family][1] += args.repeats
        print(f"{case.name:<28} {passes}/{args.repeats}")

    print("\nby family:")
    for fam, (p, n) in sorted(per_family.items()):
        print(f"  {fam:<10} {p}/{n}")
    print(f"avg latency: {total_secs / max(runs, 1):.1f}s")

    for case, run, reasons in failures:
        print(f"\nFAIL {case.name}\n  Q: {case.questions}\n  reasons: {reasons}"
              f"\n  tools: {[c['name'] for c in run.tool_calls]}\n  error: {run.error}"
              f"\n  reply: {run.reply[:300]!r}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())