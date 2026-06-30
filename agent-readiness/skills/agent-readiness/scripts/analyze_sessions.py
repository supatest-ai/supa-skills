#!/usr/bin/env python3
"""Analyze agent session JSONL logs for repo-local task completion patterns."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from session_events import SESSION_FORMATS, NormalizedSessionEvent, parse_session_events


VALIDATION_RE = re.compile(
    r"("
    r"\bpnpm\b[^\n]*(test|lint|type-check|design:check|coverage)|"
    r"\b(npm|yarn)\b[^\n]*(test|lint|type|build)|"
    r"\b(vitest|pytest|go test|cargo test|swift test|xcodebuild)\b|"
    r"\btsc\b|"
    r"\bplaywright\b|"
    r"git diff --check|"
    r"quick_validate\.py"
    r")",
    re.IGNORECASE,
)

EDIT_TOOL_NAMES = {
    "apply_patch",
    "edit_file",
    "mcp__morph_mcp.edit_file",
    "mcp__morph_mcp__edit_file",
}

WRITE_SHELL_RE = re.compile(
    r"("
    r"\bapply_patch\b|"
    r"\bcat\s+>|"
    r"\btee\s+|"
    r"\bpython3?\b[\s\S]{0,160}\.write\(|"
    r"\bnode\b[\s\S]{0,160}writeFile"
    r")",
    re.IGNORECASE,
)

READ_ONLY_SHELL_RE = re.compile(
    r"^\s*("
    r"rg|grep|sed|awk|find|ls|pwd|wc|head|tail|nl|cat|"
    r"git\s+(status|diff|log|show|rev-parse|ls-files|grep)"
    r")\b",
    re.IGNORECASE,
)

FAILURE_RE = re.compile(
    r"("
    r"Exit code:\s*[1-9]|"
    r"Traceback|"
    r"ModuleNotFoundError|"
    r"timed out|"
    r"permission denied|"
    r"No such file"
    r")",
    re.IGNORECASE,
)

BLOCKED_RE = re.compile(
    r"("
    r"\bblocked\b|"
    r"\bcan't\b|"
    r"\bcannot\b|"
    r"missing .*?(env|credential|permission|dependency)|"
    r"permission denied|"
    r"timed out"
    r")",
    re.IGNORECASE,
)

MANUAL_HANDOFF_RE = re.compile(
    r"("
    r"did you test|"
    r"have you tested|"
    r"i.?ll test|"
    r"manual(ly)? test|"
    r"not working|"
    r"fix the rest"
    r")",
    re.IGNORECASE,
)

PLAN_ONLY_RE = re.compile(r"plan-only mode|do not make code changes|do not execute write operations", re.IGNORECASE)

FINAL_REPORT_RE = re.compile(
    r"(Changed files|Validation|Residual risk|Tests? run|Verification|"
    r"gh pr create|Pull request|PR created|opened a pull request|"
    r"https?://github\.com/[^/]+/[^/]+/pull/)",
    re.IGNORECASE,
)

FAILURE_CONTEXT_RE = re.compile(
    r"(fail|failed|failing|error|blocked|stuck|stall|timed out|timeout|cannot|can't|unable|not working|unauthorized|401|403|not logged|login failed|still on login|login screen|sign in page|redirected to login)",
    re.IGNORECASE,
)

INJECTED_PREFIXES = (
    "# AGENTS.md instructions",
    "You are Aiden, the software factory agent",
    "<environment_context>",
    "<permissions instructions>",
)

PATTERN_RULES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "browser_login_auth_failure",
        "Browser login/auth",
        re.compile(
            r"(agent[-_ ]?browser|browser-use|playwright|browser).{0,240}(log ?in|login|sign ?in|auth|unauthorized|401|403|cookie|session)"
            r"|(log ?in|login|sign ?in|auth|unauthorized|401|403|cookie|session).{0,240}(agent[-_ ]?browser|browser-use|playwright|browser)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "aiden_testing_login_failure",
        "Aiden testing login",
        re.compile(
            r"(aiden[-_ ]?testing|aiden-test-feature|aiden-journey-dogfood).{0,300}(log ?in|login|sign ?in|auth|cookie|session|unauthorized|401|403)"
            r"|(log ?in|login|sign ?in|auth|cookie|session|unauthorized|401|403).{0,300}(aiden[-_ ]?testing|aiden-test-feature|aiden-journey-dogfood)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "browser_navigation_or_selector_stall",
        "Browser navigation/selector stall",
        re.compile(r"(timeout|timed out|waiting for|selector|locator|element).{0,180}(browser|page|click|navigation|visible|attached|detached|not found|not visible)", re.IGNORECASE | re.DOTALL),
    ),
    (
        "provider_or_model_route_failure",
        "Provider/model route",
        re.compile(r"(unsupported model|model route|provider.*failed|selectedProviderId|kimi_cli|claude-sonnet|Task failed)", re.IGNORECASE),
    ),
    (
        "missing_env_or_secret",
        "Missing env/secret",
        re.compile(r"(missing|required|not set).{0,120}(env|environment variable|secret|token|api key|credential)", re.IGNORECASE | re.DOTALL),
    ),
    (
        "tool_schema_or_mcp_failure",
        "Tool/MCP schema",
        re.compile(r"(schema|invalid arguments|unknown tool|tool.*not found|MCP|failed to call tool|missing required parameter)", re.IGNORECASE),
    ),
    (
        "dependency_missing",
        "Missing dependency",
        re.compile(r"(ModuleNotFoundError|Cannot find module|command not found|No such file or directory|ENOENT)", re.IGNORECASE),
    ),
    (
        "test_failure",
        "Test failure",
        re.compile(r"(FAIL|failed).{0,120}(vitest|pytest|playwright|test|spec)|AssertionError|expected .* to", re.IGNORECASE | re.DOTALL),
    ),
    (
        "typecheck_failure",
        "Typecheck failure",
        re.compile(r"(tsc|type-check|TypeScript).{0,180}(error TS|failed|exited with|Exit code:\s*[1-9])", re.IGNORECASE | re.DOTALL),
    ),
    (
        "lint_failure",
        "Lint failure",
        re.compile(r"(biome|eslint|lint).{0,180}(error|warning|diagnostic|failed|Exit code:\s*[1-9])", re.IGNORECASE | re.DOTALL),
    ),
    (
        "git_push_rejected",
        "Git push rejected",
        re.compile(r"(non-fast-forward|\[rejected\].*->|fetch first|Updates were rejected|cannot lock ref)", re.IGNORECASE),
    ),
    (
        "electric_sync_failure",
        "Electric SQL sync",
        re.compile(r"(electric|shape).{0,200}(stale|expired|404|409|connection closed|sync error)", re.IGNORECASE | re.DOTALL),
    ),
    (
        "sandbox_provisioning_failure",
        "Sandbox provisioning",
        re.compile(r"(sandbox|daytona|provision|cloud.{0,40}environment).{0,200}(timeout|failed|cannot create|unavailable)", re.IGNORECASE | re.DOTALL),
    ),
]

# Session cache — keyed by (file_path, file_size, file_mtime) hash
CACHE_VERSION = 1


def file_sig(path: Path) -> str:
    stat = path.stat()
    return hashlib.sha256(f"{path}:{stat.st_size}:{stat.st_mtime_ns}".encode()).hexdigest()[:16]


def load_cache(path: Path) -> dict[str, Any]:
    try:
        with path.open() as f:
            cache = json.load(f)
        if cache.get("_version") == CACHE_VERSION:
            return cache
    except (OSError, json.JSONDecodeError):
        pass
    return {"_version": CACHE_VERSION}


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    cache["_version"] = CACHE_VERSION
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(cache, f, default=str)


@dataclass
class SessionStats:
    id: str
    path: str
    timestamp: str = ""
    cwd: str = ""
    tool_calls: int = 0
    shell_calls: int = 0
    edit_calls: int = 0
    validation_calls: int = 0
    failed_tool_calls: int = 0
    first_edit_index: int | None = None
    first_validation_after_edit_index: int | None = None
    assistant_messages: int = 0
    user_messages: int = 0
    final_report_markers: int = 0
    blocked_markers: int = 0
    manual_handoff_markers: int = 0
    plan_only_markers: int = 0
    validation_commands: list[str] = field(default_factory=list)
    failed_tools: Counter[str] = field(default_factory=Counter)
    failure_patterns: Counter[str] = field(default_factory=Counter)
    failure_pattern_evidence: dict[str, list[str]] = field(default_factory=dict)
    sample_reasons: list[str] = field(default_factory=list)
    classification: str = "unclear"

    @property
    def validation_after_edit(self) -> bool:
        return self.first_validation_after_edit_index is not None


def compact_text(value: Any, limit: int = 4000) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:limit]
    try:
        return json.dumps(value, ensure_ascii=False)[:limit]
    except TypeError:
        return str(value)[:limit]


def extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return compact_text(content)
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict):
            text = item.get("text") or item.get("input_text") or item.get("output_text")
            if isinstance(text, str):
                parts.append(text)
        elif isinstance(item, str):
            parts.append(item)
    return "\n".join(parts)


def is_injected_message(text: str) -> bool:
    stripped = text.lstrip()
    if len(stripped) > 12_000:
        return True
    return any(stripped.startswith(prefix) for prefix in INJECTED_PREFIXES)


def parse_arguments(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def find_repo_session(path: Path, repo: str | None) -> bool:
    if not repo:
        return True
    needle = repo
    short = repo.split("/Documents/")[-1] if "/Documents/" in repo else repo
    try:
        with path.open(errors="ignore") as handle:
            for index, line in enumerate(handle):
                if index > 80:
                    break
                if needle in line or short in line:
                    return True
    except OSError:
        return False
    return False


def iter_session_files(sessions_dir: Path, repo: str | None, max_sessions: int | None) -> list[Path]:
    files = sorted(sessions_dir.glob("**/*.jsonl"))
    if repo:
        files = [path for path in files if find_repo_session(path, repo)]
    if max_sessions is not None:
        files = files[-max_sessions:]
    return files


def session_id_from_path(path: Path) -> str:
    match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", path.stem)
    return match.group(1) if match else path.stem


def apply_session_meta(stats: SessionStats, line: str) -> None:
    id_match = re.search(r'"id"\s*:\s*"([^"\\]+)"', line)
    timestamp_match = re.search(r'"timestamp"\s*:\s*"([^"\\]+)"', line)
    cwd_match = re.search(r'"cwd"\s*:\s*"([^"\\]+)"', line)
    if id_match:
        stats.id = id_match.group(1)
    if timestamp_match:
        stats.timestamp = timestamp_match.group(1)
    if cwd_match:
        stats.cwd = cwd_match.group(1)


def command_from_args(args: Any) -> str:
    if isinstance(args, dict):
        for key in ("command", "cmd", "script"):
            value = args.get(key)
            if isinstance(value, str):
                return value
    return ""


def is_read_only_shell_command(command_text: str) -> bool:
    if not READ_ONLY_SHELL_RE.search(command_text):
        return False
    return not re.search(r"(\s>|\s>>|\btee\s+|\bapply_patch\b|\bmv\b|\bcp\b|\brm\b|\bchmod\b)", command_text)


def evidence_excerpt(text: str, match: re.Match[str], limit: int = 220) -> str:
    start = max(0, match.start() - 70)
    end = min(len(text), match.end() + 70)
    return " ".join(text[start:end].split())[:limit]


def record_failure_patterns(stats: SessionStats, text: str) -> None:
    if not text or is_injected_message(text):
        return
    scan_text = text if len(text) <= 8000 else f"{text[:4000]}\n{text[-4000:]}"
    if not FAILURE_CONTEXT_RE.search(scan_text):
        return
    for name, _category, pattern in PATTERN_RULES:
        match = pattern.search(scan_text)
        if not match:
            continue
        stats.failure_patterns[name] += 1
        evidence = stats.failure_pattern_evidence.setdefault(name, [])
        if len(evidence) < 3:
            evidence.append(evidence_excerpt(scan_text, match))


def parse_session(path: Path, repo: str | None = None, session_format: str = "auto", cache: dict[str, Any] | None = None) -> SessionStats:
    """Parse a session file, optionally using a cache keyed by file signature."""
    sig = file_sig(path)
    if cache is not None:
        cached = cache.get(sig)
        if cached is not None and cached.get("_format", "") == session_format:
            return SessionStats(**{k: v for k, v in cached.items() if k != "_format"})

    stats = SessionStats(id=session_id_from_path(path), path=str(path))
    event_index = 0
    last_tool_name_by_call_id: dict[str, str] = {}

    for event in parse_session_events(path, session_format):
        if event.kind == "metadata":
            stats.timestamp = event.timestamp or stats.timestamp
            stats.cwd = event.cwd or stats.cwd
            stats.id = event.session_id or stats.id
            continue

        if event.kind == "turn_context":
            stats.cwd = event.cwd or stats.cwd
            continue

        if event.kind == "user_message":
            handle_user_text(stats, event.text)
            record_failure_patterns(stats, event.text)
            continue

        if event.kind == "assistant_message":
            if is_injected_message(event.text):
                continue
            stats.assistant_messages += 1
            handle_assistant_text(stats, event.text)
            record_failure_patterns(stats, event.text)
            continue

        if event.kind == "tool_call":
            event_index += 1
            handle_tool_call(stats, event, event_index, last_tool_name_by_call_id)
            continue

        if event.kind == "tool_result":
            event_index += 1
            handle_tool_result(stats, event, last_tool_name_by_call_id)
            continue

    classify(stats)

    if cache is not None:
        cache[sig] = {**asdict(stats), "_format": session_format}

    return stats


def handle_tool_call(
    stats: SessionStats,
    event: NormalizedSessionEvent,
    event_index: int,
    last_tool_name_by_call_id: dict[str, str],
) -> None:
    tool_name = event.tool_name or "tool"
    if event.tool_call_id:
        last_tool_name_by_call_id[event.tool_call_id] = tool_name

    args = parse_arguments(event.tool_args)
    args_text = compact_text(args, 20_000)
    command_text = command_from_args(args) or args_text
    stats.tool_calls += 1
    if tool_name == "shell_command" or "shell_command" in tool_name:
        stats.shell_calls += 1
    is_shell = bool(command_from_args(args)) or tool_name == "shell_command" or "shell_command" in tool_name

    is_edit = tool_name in EDIT_TOOL_NAMES or "edit_file" in tool_name or (
        is_shell
        and not is_read_only_shell_command(command_text)
        and WRITE_SHELL_RE.search(command_text)
    )
    if is_edit:
        mark_edit(stats, event_index)

    if is_shell and VALIDATION_RE.search(command_text):
        mark_validation(stats, event_index, command_text)


def handle_tool_result(
    stats: SessionStats,
    event: NormalizedSessionEvent,
    last_tool_name_by_call_id: dict[str, str],
) -> None:
    tool_name = event.tool_name or last_tool_name_by_call_id.get(event.tool_call_id, "tool")
    output = event.text
    if event.failed or FAILURE_RE.search(output):
        stats.failed_tool_calls += 1
        stats.failed_tools[tool_name] += 1
        record_failure_patterns(stats, output)


def mark_edit(stats: SessionStats, event_index: int) -> None:
    stats.edit_calls += 1
    if stats.first_edit_index is None:
        stats.first_edit_index = event_index


def mark_validation(stats: SessionStats, event_index: int, command_text: str) -> None:
    stats.validation_calls += 1
    if stats.first_edit_index is not None and event_index > stats.first_edit_index:
        if stats.first_validation_after_edit_index is None:
            stats.first_validation_after_edit_index = event_index
    command = " ".join(command_text.split())
    if command and command not in stats.validation_commands:
        stats.validation_commands.append(command[:240])


def handle_user_text(stats: SessionStats, text: str) -> None:
    if is_injected_message(text):
        return
    stats.user_messages += 1
    if PLAN_ONLY_RE.search(text):
        stats.plan_only_markers += 1
    if MANUAL_HANDOFF_RE.search(text):
        stats.manual_handoff_markers += 1
    if BLOCKED_RE.search(text):
        stats.blocked_markers += 1


def handle_assistant_text(stats: SessionStats, text: str) -> None:
    stats.final_report_markers += len(FINAL_REPORT_RE.findall(text))
    if BLOCKED_RE.search(text):
        stats.blocked_markers += 1


def classify(stats: SessionStats) -> None:
    if stats.plan_only_markers and not stats.edit_calls:
        stats.classification = "planning-only"
    elif stats.edit_calls and stats.validation_after_edit and stats.final_report_markers >= 2:
        stats.classification = "task-finisher"
    elif stats.edit_calls and stats.validation_after_edit:
        stats.classification = "assisted-implementor"
    elif stats.edit_calls and not stats.validation_after_edit:
        stats.classification = "code-generator"
    elif stats.validation_calls and not stats.edit_calls:
        stats.classification = "validation-only"
    elif stats.blocked_markers and not stats.edit_calls:
        stats.classification = "blocked"
    elif stats.failed_tool_calls >= 4 and stats.tool_calls >= 12:
        stats.classification = "debug-loop"
    elif not stats.edit_calls and not stats.validation_calls:
        stats.classification = "research-only"
    else:
        stats.classification = "unclear"


def select_samples(stats: list[SessionStats], sample_size: int) -> list[SessionStats]:
    selected: list[SessionStats] = []
    seen: set[str] = set()

    def add(reason: str, items: list[SessionStats], limit: int) -> None:
        added = 0
        for item in items:
            if item.id in seen:
                continue
            item.sample_reasons.append(reason)
            selected.append(item)
            seen.add(item.id)
            added += 1
            if added >= limit or len(selected) >= sample_size:
                return

    newest = sorted(stats, key=lambda item: (item.timestamp, item.id), reverse=True)
    add("recent", newest, 3)
    add("high_failed_tools", sorted(stats, key=lambda item: (item.failed_tool_calls, item.tool_calls, item.timestamp), reverse=True), 3)
    # For pattern-based samples: pick the session with the MOST evidence for that pattern (not newest)
    for pattern_name in ("aiden_testing_login_failure", "browser_login_auth_failure", "browser_navigation_or_selector_stall"):
        candidates = [s for s in stats if pattern_name in s.failure_patterns]
        candidates.sort(key=lambda s: (s.failure_patterns.get(pattern_name, 0), s.tool_calls), reverse=True)
        add(f"pattern:{pattern_name}", candidates, 2)
    add("edits_without_validation", [item for item in newest if item.classification == "code-generator"], 3)
    add("task_finishers", [item for item in newest if item.classification == "task-finisher"], 2)
    add("blocked", [item for item in newest if item.classification == "blocked"], 2)
    add("long_sessions", sorted(stats, key=lambda item: (item.tool_calls, item.failed_tool_calls, item.timestamp), reverse=True), 2)
    add("fill", newest, sample_size - len(selected))
    return selected[:sample_size]


def summarize(stats: list[SessionStats], samples: list[SessionStats]) -> dict[str, Any]:
    classifications = Counter(item.classification for item in stats)
    failed_tools: Counter[str] = Counter()
    validation_commands: Counter[str] = Counter()
    pattern_mentions: Counter[str] = Counter()
    pattern_sessions: Counter[str] = Counter()
    pattern_session_ids: dict[str, set[str]] = defaultdict(set)
    pattern_sample_ids: dict[str, list[str]] = defaultdict(list)
    pattern_evidence: dict[str, list[str]] = defaultdict(list)
    pattern_categories = {name: category for name, category, _pattern in PATTERN_RULES}
    for item in stats:
        failed_tools.update(item.failed_tools)
        validation_commands.update(item.validation_commands[:3])
        pattern_mentions.update(item.failure_patterns)
        for pattern_name in item.failure_patterns:
            pattern_session_ids[pattern_name].add(item.id)
            if item.id not in pattern_sample_ids[pattern_name] and len(pattern_sample_ids[pattern_name]) < 5:
                pattern_sample_ids[pattern_name].append(item.id)
            if len(pattern_evidence[pattern_name]) < 3:
                pattern_evidence[pattern_name].extend(item.failure_pattern_evidence.get(pattern_name, [])[: 3 - len(pattern_evidence[pattern_name])])
    for pattern_name, session_ids in pattern_session_ids.items():
        pattern_sessions[pattern_name] = len(session_ids)

    def rate(count: int) -> float:
        return round(count / len(stats), 3) if stats else 0.0

    tool_counts = [item.tool_calls for item in stats]
    failure_counts = [item.failed_tool_calls for item in stats]
    edit_sessions = sum(1 for item in stats if item.edit_calls)
    validation_after_edit = sum(1 for item in stats if item.validation_after_edit)

    return {
        "sessionCount": len(stats),
        "classificationCounts": dict(classifications),
        "rates": {
            "sessionsWithEdits": rate(edit_sessions),
            "sessionsWithValidationAfterEdit": rate(validation_after_edit),
            "editSessionsWithValidationAfterEdit": round(validation_after_edit / edit_sessions, 3) if edit_sessions else 0.0,
            "sessionsWithFinalReportMarkers": rate(sum(1 for item in stats if item.final_report_markers)),
            "sessionsWithManualHandoffMarkers": rate(sum(1 for item in stats if item.manual_handoff_markers)),
        },
        "toolCalls": distribution(tool_counts),
        "failedToolCalls": distribution(failure_counts),
        "topFailedTools": failed_tools.most_common(10),
        "topFailurePatterns": [
            {
                "pattern": name,
                "category": pattern_categories.get(name, name),
                "sessions": pattern_sessions[name],
                "mentions": pattern_mentions[name],
                "sampleSessionIds": pattern_sample_ids.get(name, []),
                "evidence": pattern_evidence.get(name, []),
            }
            for name, _count in pattern_sessions.most_common(12)
        ],
        "commonValidationCommands": validation_commands.most_common(10),
        "recommendedSamples": [sample_payload(item) for item in samples],
    }


def distribution(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"min": 0, "p50": 0, "p90": 0, "max": 0, "avg": 0.0}
    ordered = sorted(values)
    p90_index = int((len(ordered) - 1) * 0.9)
    return {
        "min": ordered[0],
        "p50": statistics.median(ordered),
        "p90": ordered[p90_index],
        "max": ordered[-1],
        "avg": round(statistics.mean(ordered), 2),
    }


def sample_payload(item: SessionStats) -> dict[str, Any]:
    return {
        "sessionId": item.id,
        "timestamp": item.timestamp,
        "classification": item.classification,
        "reasons": item.sample_reasons,
        "toolCalls": item.tool_calls,
        "editCalls": item.edit_calls,
        "validationCalls": item.validation_calls,
        "failedToolCalls": item.failed_tool_calls,
        "finalReportMarkers": item.final_report_markers,
        "failurePatterns": dict(item.failure_patterns),
        "path": item.path,
    }


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Session Pattern Scan",
        "",
        f"Sessions analyzed: {summary['sessionCount']}",
        "",
        "## Classifications",
    ]
    for name, count in summary["classificationCounts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Rates"])
    for name, value in summary["rates"].items():
        lines.append(f"- {name}: {value}")
    lines.extend(["", "## Top Failed Tools"])
    for name, count in summary["topFailedTools"]:
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Top Failure Patterns"])
    for item in summary["topFailurePatterns"]:
        lines.append(f"- {item['category']}: {item['sessions']} sessions, {item['mentions']} mentions")
    lines.extend(["", "## Recommended Samples"])
    for sample in summary["recommendedSamples"]:
        lines.append(
            f"- {sample['sessionId']} [{', '.join(sample['reasons'])}] "
            f"{sample['classification']} tools={sample['toolCalls']} "
            f"failed={sample['failedToolCalls']}"
        )
    return "\n".join(lines)


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
        help="Session transcript format. auto detects Codex, Claude, Copilot, Cursor, Droid, Gemini, Kimi, OpenCode, Supatest, or generic JSONL.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of markdown")
    parser.add_argument("--no-progress", action="store_true", help="Suppress progress output on stderr")
    parser.add_argument("--no-cache", action="store_true", help="Disable session parse cache")
    args = parser.parse_args()

    sessions_dir = Path(args.sessions_dir)
    cache_path = sessions_dir / ".agent-readiness-cache.json"
    cache: dict[str, Any] | None = None if args.no_cache else load_cache(cache_path)

    show_progress = not args.no_progress and sys.stderr.isatty()

    files = iter_session_files(sessions_dir, args.repo, args.max_sessions)
    total = len(files)
    error_count = 0
    start_time: list[float] = []  # mutable container for closure

    stats: list[SessionStats] = []
    for idx, path in enumerate(files, start=1):
        try:
            stats.append(parse_session(path, args.repo, args.format, cache))
        except Exception as exc:
            error_count += 1
            if show_progress:
                print(f"  [ERROR] {path.name}: {exc}", file=sys.stderr)
        if show_progress:
            if not start_time:
                start_time.append(time.time())
            if idx % max(1, total // 10) == 0 or idx == total:
                elapsed = round(time.time() - start_time[0], 1)
                print(f"\r  [{time.strftime('%H:%M:%S')}] Parsed {idx}/{total} sessions ({elapsed}s)...   ", file=sys.stderr, end="")

    if show_progress:
        print(file=sys.stderr)  # newline after progress

    if error_count > 0 and show_progress:
        print(f"  Warning: {error_count} session(s) had parse errors.", file=sys.stderr)

    # Zero-events warning
    zero_tool = sum(1 for s in stats if s.tool_calls == 0)
    if zero_tool == total:
        print("WARNING: 0 tool calls detected across all sessions.", file=sys.stderr)
        print("  The --format or --sessions-dir may be wrong.", file=sys.stderr)
        print(f"  Try --format generic-jsonl or check path: {sessions_dir}", file=sys.stderr)
    elif zero_tool > total * 0.5:
        print(f"WARNING: {zero_tool}/{total} sessions have 0 tool calls.", file=sys.stderr)
        print(f"  The --format ({args.format}) may not match the session file structure.", file=sys.stderr)

    # Save cache if used
    if cache is not None:
        try:
            save_cache(cache_path, cache)
        except OSError as exc:
            if show_progress:
                print(f"  Warning: could not write cache: {exc}", file=sys.stderr)

    samples = select_samples(stats, args.sample_size)
    summary = summarize(stats, samples)
    summary["skippedCount"] = error_count

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(markdown_report(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
