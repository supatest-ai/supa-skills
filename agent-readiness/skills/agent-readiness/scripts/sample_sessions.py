#!/usr/bin/env python3
"""Print deterministic session samples for qualitative agent-readiness review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_sessions import iter_session_files, parse_session, sample_payload, select_samples
from session_events import SESSION_FORMATS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions-dir", default=str(Path.home() / ".codex" / "sessions"))
    parser.add_argument("--repo", default=str(Path.cwd()))
    parser.add_argument("--sample-size", type=int, default=15)
    parser.add_argument("--max-sessions", type=int)
    parser.add_argument(
        "--format",
        default="auto",
        choices=SESSION_FORMATS,
        help="Session transcript format. auto detects supported CLI JSONL formats.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of compact text")
    args = parser.parse_args()

    files = iter_session_files(Path(args.sessions_dir), args.repo, args.max_sessions)
    stats = [parse_session(path, args.repo, args.format) for path in files]
    samples = select_samples(stats, args.sample_size)

    if args.json:
        print(json.dumps([sample_payload(item) for item in samples], indent=2, sort_keys=True))
    else:
        for item in samples:
            reasons = ",".join(item.sample_reasons)
            print(
                f"{item.id}\t{item.classification}\t{reasons}\t"
                f"tools={item.tool_calls}\tedits={item.edit_calls}\t"
                f"validation={item.validation_calls}\tfailed={item.failed_tool_calls}\t{item.path}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
