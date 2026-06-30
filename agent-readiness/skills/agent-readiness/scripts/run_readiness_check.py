#!/usr/bin/env python3
"""Combined agent-readiness runner — analyze, sample, compact, and render in one command.

Usage:
  python3 scripts/run_readiness_check.py --sessions-dir ~/.claude/projects/PROJECT --repo /path/to/repo
  python3 scripts/run_readiness_check.py --sessions-dir ~/.claude/projects/PROJECT --repo /path/to/repo --skip-sessions
  python3 scripts/run_readiness_check.py --sessions-dir ~/.claude/projects/PROJECT --repo /path/to/repo --output /tmp/report.html
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add scripts dir to path so imports work regardless of cwd
_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))

from analyze_sessions import (
    iter_session_files,
    load_cache,
    parse_session,
    save_cache,
    select_samples,
    summarize,
    SESSION_FORMATS,
)
from compact_sessions import compact_session, markdown_digest
from render_html_report import render_html
from session_events import SESSION_FORMATS as EVT_FORMATS  # same values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-dir", help="Path to session JSONL directory")
    parser.add_argument("--repo", default=str(Path.cwd()), help="Repo root path")
    parser.add_argument("--skip-sessions", action="store_true", help="Skip session analysis (static audit only)")
    parser.add_argument("--sample-size", type=int, default=15, help="Number of session samples for deep analysis")
    parser.add_argument("--max-sessions", type=int, help="Max sessions to scan (most recent)")
    parser.add_argument("--no-cache", action="store_true", help="Disable session parse cache")
    parser.add_argument("--no-progress", action="store_true", help="Suppress progress output")
    parser.add_argument(
        "--format",
        default="auto",
        choices=SESSION_FORMATS,
        help="Session transcript format (auto detects most CLIs)",
    )
    parser.add_argument(
        "--output",
        default="/tmp/agent-readiness-report.html",
        help="Output HTML report path",
    )
    parser.add_argument(
        "--report-json",
        help="Write intermediate report JSON to this path (optional)",
    )
    args = parser.parse_args()

    report: dict = {"agentUsage": {}}

    # --- Phase 0: Session scan (skip if --skip-sessions or no sessions-dir) ---
    if args.skip_sessions or not args.sessions_dir:
        if not args.skip_sessions:
            print("No --sessions-dir provided; running static-only audit.", file=sys.stderr)
        report["agentUsage"]["sessionCount"] = 0
        report["agentUsage"]["classificationCounts"] = {}
        report["agentUsage"]["rates"] = {}
        report["agentUsage"]["topFailedTools"] = []
        report["agentUsage"]["topFailurePatterns"] = []
        report["agentUsage"]["commonValidationCommands"] = []
        report["agentUsage"]["sampleIds"] = []
        report["agentUsage"]["compactFindings"] = []
    else:
        sessions_dir = Path(args.sessions_dir)
        if not sessions_dir.is_dir():
            print(f"ERROR: sessions-dir not found: {sessions_dir}", file=sys.stderr)
            return 1

        t0 = time.time()
        show_progress = not args.no_progress and sys.stderr.isatty()

        # Load cache
        cache_path = sessions_dir / ".agent-readiness-cache.json"
        cache = None if args.no_cache else load_cache(cache_path)

        # Find and parse sessions
        files = iter_session_files(sessions_dir, args.repo, args.max_sessions)
        total = len(files)
        if show_progress:
            print(f"[{time.strftime('%H:%M:%S')}] Analyzing {total} sessions...", file=sys.stderr)

        error_count = 0
        stats = []
        for idx, path in enumerate(files, start=1):
            try:
                stats.append(parse_session(path, args.repo, args.format, cache))
            except Exception as exc:
                error_count += 1
                if show_progress:
                    print(f"  [ERROR] {path.name}: {exc}", file=sys.stderr)
            if show_progress and total >= 10 and (idx % max(1, total // 10) == 0 or idx == total):
                elapsed = round(time.time() - t0, 1)
                print(f"\r  Parsed {idx}/{total} sessions ({elapsed}s)...   ", file=sys.stderr, end="")
        if show_progress:
            print(file=sys.stderr)

        # Save cache
        if cache is not None:
            try:
                save_cache(cache_path, cache)
            except OSError as exc:
                if show_progress:
                    print(f"  Warning: could not write cache: {exc}", file=sys.stderr)

        # Select samples
        samples = select_samples(stats, args.sample_size)
        summary = summarize(stats, samples)
        summary["skippedCount"] = error_count

        # Compact samples
        if show_progress:
            print(f"[{time.strftime('%H:%M:%S')}] Compacting {len(samples)} sample sessions...", file=sys.stderr)
        digests = [
            compact_session(item, max_message_chars=900, max_events=24, session_format=args.format)
            for item in samples
        ]

        elapsed = round(time.time() - t0, 1)
        if show_progress:
            print(f"[{time.strftime('%H:%M:%S')}] Session analysis complete ({elapsed}s).", file=sys.stderr)

        # Build agentUsage from summary
        report["agentUsage"] = {
            "sessionCount": summary["sessionCount"],
            "classificationCounts": summary["classificationCounts"],
            "rates": summary["rates"],
            "topFailedTools": summary["topFailedTools"],
            "topFailurePatterns": summary["topFailurePatterns"],
            "commonValidationCommands": summary["commonValidationCommands"],
            "sampleIds": [s.get("sessionId", "") for s in summary.get("recommendedSamples", [])],
            "compactFindings": [
                f"Sessions: {d.get('classification', '?')} — {d.get('metrics', {}).get('toolCalls', 0)} tools, "
                f"{d.get('metrics', {}).get('editCalls', 0)} edits, "
                f"{d.get('metrics', {}).get('validationCalls', 0)} validations"
                for d in digests
            ],
        }

    # --- Phase 1-3: Framework for static scoring ---
    # The report JSON returned here is intended to be filled in by the agent
    # running this script. The output file is a partial template.
    report["projectName"] = Path(args.repo).name
    report["generatedAt"] = f"{time.strftime('%Y-%m-%d %H:%M')} UTC"
    report["overall"] = {"level": 0, "name": "Not scored", "score": 0, "summary": "Run agent-readiness skill for full assessment."}
    report["useCase"] = "Autonomous coding agent taking a spec to tested implementation."
    report["dimensions"] = []
    report["evidenceSummary"] = []
    report["criticalGaps"] = {"p0": [], "p1": [], "p2": [], "p3": []}
    report["actionPlan"] = []
    report["coverage"] = []
    report["raid"] = {"risks": [], "assumptions": [], "issues": [], "dependencies": []}
    report["validation"] = []

    # Write intermediate JSON if requested
    if args.report_json:
        Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.report_json, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Intermediate JSON written to {args.report_json}", file=sys.stderr)

    # Render HTML
    html = render_html(report)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    print(f"HTML report written to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
