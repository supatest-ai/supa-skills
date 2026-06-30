#!/usr/bin/env python3
"""Render an agent-readiness assessment JSON model as a polished HTML report."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_CLASS = {
    "PASS": "status-pass",
    "WARN": "status-warn",
    "FAIL": "status-fail",
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def badge(text: str, class_name: str = "") -> str:
    extra = f" {class_name}" if class_name else ""
    return f'<span class="badge{extra}">{esc(text)}</span>'


def score_color(score: float, max_score: float = 5.0) -> str:
    ratio = score / max_score
    if ratio >= 0.8:
        return "var(--green)"
    elif ratio >= 0.6:
        return "var(--yellow)"
    return "var(--red)"


def list_items(items: list[Any]) -> str:
    if not items:
        return '<p class="muted">None.</p>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def metric_card(label: str, value: Any, note: str = "") -> str:
    note_html = f'<div class="metric-note">{esc(note)}</div>' if note else ""
    return f"""
    <section class="metric-card">
      <div class="metric-label">{esc(label)}</div>
      <div class="metric-value">{esc(value)}</div>
      {note_html}
    </section>
    """


def score_bar(score: float, max_score: float = 5.0) -> str:
    width = max(0, min(100, round((score / max_score) * 100)))
    color = score_color(score, max_score)
    return f'<div class="score-bar"><span style="width: {width}%;background:{color}"></span></div>'


def render_dimensions(dimensions: list[dict[str, Any]]) -> str:
    rows = []
    for item in dimensions:
        status = str(item.get("status", "")).upper()
        score = float(item.get("score", 0))
        evidence = item.get("evidence", "")
        num = item.get("number", "")
        dim_id = f"ev-{num}"
        # Truncate long evidence to ~280 chars with expand
        ev_short = evidence[:280] + "…" if len(evidence) > 280 else evidence
        has_more = len(evidence) > 280
        ev_html = f"""
            <div class="evidence" id="{dim_id}-short">{esc(ev_short)}</div>
            <div class="evidence" id="{dim_id}-full" style="display:none">{esc(evidence)}</div>"""
        if has_more:
            ev_html += f'<button class="ev-toggle" onclick="document.getElementById(\'{dim_id}-short\').style.display=\'none\';document.getElementById(\'{dim_id}-full\').style.display=\'inline\';this.style.display=\'none\'">Show more</button>'
        rows.append(
            f"""
            <tr>
              <td class="num">{esc(item.get("number", ""))}</td>
              <td class="dim-name">
                <strong>{esc(item.get("name", ""))}</strong>
                {ev_html}
              </td>
              <td class="score-cell">
                <span style="color:{score_color(score)};font-size:18px">{score:g}/5</span>
                {score_bar(score)}
              </td>
              <td>{badge(status, STATUS_CLASS.get(status, ""))}</td>
            </tr>
            """
        )
    # Build a compact radar-style visualization for the overview
    radar_bars = ""
    for item in dimensions:
        score = float(item.get("score", 0))
        pct = max(0, min(100, round((score / 5.0) * 100)))
        color = score_color(score)
        radar_bars += f"""
        <div class="radar-row">
          <div class="radar-label" title="{esc(item.get('name', ''))}">{esc(item.get('name', ''))}</div>
          <div class="radar-track"><span style="width:{pct}%;background:{color}"></span></div>
          <div class="radar-score" style="color:{color}">{score:g}</div>
        </div>
        """
    overview = f"""
    <details class="radar-details" open>
      <summary>Score Overview</summary>
      <div class="radar-grid">{radar_bars}</div>
    </details>
    """
    return overview + "<tbody>" + "".join(rows) + "</tbody>"


def render_classifications(classifications: dict[str, int]) -> str:
    total = sum(classifications.values()) or 1
    rows = []
    for name, count in sorted(classifications.items(), key=lambda item: item[1], reverse=True):
        width = round((count / total) * 100, 1)
        rows.append(
            f"""
            <div class="bar-row">
              <div class="bar-label">{esc(name)}</div>
              <div class="bar-track"><span style="width: {width}%"></span></div>
              <div class="bar-count">{esc(count)} <span>{width}%</span></div>
            </div>
            """
        )
    return "".join(rows)


def render_kv_table(items: list[Any], key_label: str, value_label: str) -> str:
    rows = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            key, value = item[0], item[1]
        elif isinstance(item, dict):
            key, value = item.get("name", item.get("key", "")), item.get("count", item.get("value", ""))
        else:
            continue
        rows.append(f"<tr><td>{esc(key)}</td><td>{esc(value)}</td></tr>")
    if not rows:
        rows.append('<tr><td colspan="2" class="muted">None.</td></tr>')
    return f"""
    <table class="compact-table">
      <thead><tr><th>{esc(key_label)}</th><th>{esc(value_label)}</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def render_failure_patterns(items: list[dict[str, Any]], session_count: int = 50) -> str:
    if not items:
        return '<p class="muted">No recurring failure patterns detected.</p>'
    rows = []
    for item in items[:8]:
        category = item.get("category", item.get("pattern", ""))
        samples = ", ".join(as_list(item.get("sampleSessionIds"))[:3])
        sessions = item.get("sessions", 0)
        mentions = item.get("mentions", 0)
        pct = max(0, min(100, (sessions / session_count) * 100)) if sessions else 0
        severity = "high" if pct >= 30 else "med" if pct >= 15 else "low"
        rows.append(
            f"""
            <tr class="fail-row fail-{severity}">
              <td><strong>{esc(category)}</strong></td>
              <td>
                <div class="fail-bar"><span style="width:{pct}%"></span></div>
              </td>
              <td class="num">{sessions}</td>
              <td class="num">{mentions}</td>
              <td class="evidence">{esc(samples)}</td>
            </tr>
            """
        )
    return f"""
    <table class="fail-table">
      <thead><tr><th>Pattern</th><th>Prevalence</th><th>Sessions</th><th>Mentions</th><th>Sample IDs</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def render_compact_findings(findings: list[str]) -> str:
    """Parse and render compact session findings as a structured table."""
    import re
    if not findings:
        return '<p class="muted">No compact-finding data.</p>'

    rows = []
    for text in findings:
        # Parse: "Session <id>: <classification>, <N> tools, <N> edits, <N> validations — <outcome>. Pattern: <pattern>."
        # Also handle "Sessions <id1>, <id2>, …" (plural, multi-session entries)
        m = re.match(
            r"Sessions?\s+(.+?):\s+([^,]+),\s+(\d+)\s+tools,\s+(\d+)\s+edits,\s+(\d+)\s+validations?(?:\s+calls?)?\s+[—–-]+\s+(.*?)(?:\.\s*Pattern:\s*(.*?)\.?)?\s*$",
            text,
        )
        if m:
            sid, cls, tools, edits, vals, outcome, pattern = m.groups()
            outcome = (outcome or "").strip()
            pattern = (pattern or "").strip()
            # Let outcomes wrap naturally — no truncation
            # Color code by pattern severity
            sev_class = ""
            med_patterns = {"test_failure", "tool_schema", "dependency"}
            if pattern:
                pl = pattern.lower()
                if "aiden_testing" in pl or "browser_login" in pl or "browser_navigation" in pl:
                    sev_class = "fail-high"
                elif any(p in pl for p in med_patterns):
                    sev_class = "fail-med"
            rows.append(
                f"""
            <tr class="{sev_class}">
              <td class="find-session">{esc(sid)}</td>
              <td class="find-type">{esc(cls)}</td>
              <td class="find-metrics">
                <span class="m">{esc(tools)}t</span>
                <span class="m">{esc(edits)}e</span>
                <span class="m">{esc(vals)}v</span>
              </td>
              <td class="find-pattern">{esc(pattern) if pattern else '<span class="muted">—</span>'}</td>
              <td class="find-outcome">{esc(outcome)}</td>
            </tr>"""
            )
        else:
            # Fallback: try multi-session or abbreviated format
            fb = re.match(r"Sessions?\s+(.+?):\s+([^,]+),\s*(.*?)\s+[—–-]+\s+(.*)", text)
            if fb:
                sid, cls, abbr, outcome = fb.groups()
                rows.append(
                    f"""
            <tr>
              <td class="find-session">{esc(sid)}</td>
              <td class="find-type">{esc(cls)}</td>
              <td class="find-metrics"><span class="muted">{esc(abbr)}</span></td>
              <td class="find-pattern"><span class="muted">—</span></td>
              <td class="find-outcome">{esc(outcome[:160])}</td>
            </tr>"""
                )
            else:
                rows.append(
                    f"""
            <tr>
              <td colspan="5" class="find-outcome">{esc(text[:200])}</td>
            </tr>"""
                )

    return f"""
    <div class="findings-scroll">
    <table class="findings-table">
      <thead><tr>
        <th>Session</th>
        <th>Type</th>
        <th>Scope <span class="find-legend" title="t = tool calls, e = edits, v = validations">ⓘ</span></th>
        <th>Pattern</th>
        <th>Key Outcome</th>
      </tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    </div>"""


def render_action_plan(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return '<p class="muted">No actions.</p>'
    rows = []
    for index, action in enumerate(actions, start=1):
        files = ", ".join(as_list(action.get("files")))
        files_html = f'<div class="files">{esc(files)}</div>' if files else ""
        rows.append(
            f"""
            <li class="action-item">
              <div class="action-num">{index}</div>
              <div class="action-body">
                <strong>{esc(action.get("action", ""))}</strong>
                <p>{esc(action.get("why", ""))}</p>
                {files_html}
              </div>
            </li>
            """
        )
    return f'<ol class="action-list">{"".join(rows)}</ol>'


def render_coverage(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        ready = str(row.get("ready", ""))
        rl = ready.lower()
        if rl == "ready":
            ready_class = "ready-yes"
        elif rl == "partial":
            ready_class = "ready-partial"
        elif rl == "warn":
            ready_class = "ready-warn"
        else:
            ready_class = "ready-no"
        body.append(
            f"""
            <tr>
              <td><strong>{esc(row.get("phase", ""))}</strong></td>
              <td>{badge(ready, ready_class)}</td>
              <td>{esc(row.get("notes", ""))}</td>
            </tr>
            """
        )
    return f"""
    <table class="coverage-table">
      <thead><tr><th>Phase</th><th>Ready?</th><th>Notes</th></tr></thead>
      <tbody>{''.join(body)}</tbody>
    </table>
    """


def render_raid(raid: dict[str, list[str]]) -> str:
    sections = []
    labels = [
        ("risks", "Risks"),
        ("assumptions", "Assumptions"),
        ("issues", "Issues"),
        ("dependencies", "Dependencies"),
    ]
    for key, label in labels:
        sections.append(
            f"""
            <section class="raid-card">
              <h3>{esc(label)}</h3>
              {list_items(as_list(raid.get(key)))}
            </section>
            """
        )
    return "".join(sections)


def section_link(name: str) -> str:
    """HTML id from section name."""
    return name.lower().replace(" ", "-").replace("&", "").replace("--", "-").strip("-")


def render_toc(report: dict[str, Any]) -> str:
    sections = [
        "Use Case",
        "Dimension Scores",
        "Evidence Summary",
        "Agent Usage Pattern",
        "Critical Gaps",
        "Recommended Action Plan",
        "Spec-To-Task Completion Coverage",
        "RAID",
        "Validation",
    ]
    links = "".join(
        f'<li><a href="#{section_link(s)}">{esc(s)}</a></li>' for s in sections
    )
    return f'<nav class="toc"><h3>Contents</h3><ul>{links}</ul></nav>'


def render_html(report: dict[str, Any]) -> str:
    project = report.get("projectName", "Repository")
    generated_at = report.get("generatedAt") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    overall = report.get("overall", {})
    usage = report.get("agentUsage", {})
    rates = usage.get("rates", {})
    dimensions = report.get("dimensions", [])
    average = overall.get("score", 0)

    # Compute overall score bar color
    overall_color = score_color(float(average)) if isinstance(average, (int, float)) else "var(--blue)"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agent Readiness Report - {esc(project)}</title>
  <style>
    :root {{
      --bg: #f5f6fa;
      --panel: #ffffff;
      --ink: #0f1826;
      --muted: #5e6f8d;
      --line: #d8dfe9;
      --green: #138a50;
      --green-bg: #e6f7ef;
      --yellow: #a06500;
      --yellow-bg: #fef3c7;
      --red: #c5281a;
      --red-bg: #fde8e6;
      --blue: #1e5bb5;
      --blue-bg: #e6effa;
      --hero-bg: #0f1826;
      --hero-muted: #9aa8c0;
      --shadow: 0 1px 3px rgba(15,23,42,0.06), 0 6px 16px rgba(15,23,42,0.05);
      --radius: 10px;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, system-ui, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.6 var(--font);
    }}
    main {{
      max-width: 1160px;
      margin: 0 auto;
      padding: 0 24px 56px;
    }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* Hero */
    .hero {{
      background: var(--hero-bg);
      color: white;
      border-radius: 0 0 var(--radius) var(--radius);
      padding: 36px 40px 32px;
      margin: 0 -24px 20px;
    }}
    .hero .eyebrow {{
      color: var(--hero-muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }}
    .hero h1 {{ margin: 8px 0 0; font-size: 36px; line-height: 1.05; letter-spacing: -0.02em; }}
    .hero-summary {{ max-width: 860px; color: #c8d2e0; font-size: 15px; margin: 14px 0 0; line-height: 1.55; }}
    .hero-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 22px;
    }}
    .hero-stat {{
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 8px;
      padding: 14px 16px;
      background: rgba(255,255,255,0.04);
    }}
    .hero-stat strong {{ display: block; font-size: 26px; font-weight: 700; letter-spacing: -0.01em; }}
    .hero-stat span {{ color: var(--hero-muted); font-size: 12px; }}

    /* TOC */
    .toc {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 18px 24px;
      margin-bottom: 20px;
      box-shadow: var(--shadow);
    }}
    .toc h3 {{ margin: 0 0 8px; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
    .toc ul {{ list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 4px 2px; }}
    .toc li {{ margin: 0; }}
    .toc a {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 99px;
      font-size: 13px;
      font-weight: 500;
      background: var(--blue-bg);
      color: var(--blue);
    }}
    .toc a:hover {{ background: #d4e2f7; text-decoration: none; }}

    /* Sections */
    .section {{
      margin-top: 20px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 24px 28px;
      box-shadow: var(--shadow);
    }}
    .section h2 {{
      font-size: 18px;
      margin: 0 0 16px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--bg);
      letter-spacing: -0.01em;
    }}
    .section h3 {{ font-size: 14px; margin: 0 0 8px; text-transform: uppercase; color: var(--muted); letter-spacing: 0.04em; }}

    /* Radar overview */
    .radar-details {{
      margin-bottom: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 18px;
      background: #fbfcfe;
    }}
    .radar-details summary {{
      font-weight: 700; font-size: 13px; cursor: pointer; color: var(--muted); user-select: none;
    }}
    .radar-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px 24px;
      margin-top: 12px;
    }}
    .radar-row {{
      display: grid;
      grid-template-columns: minmax(0, 1.8fr) minmax(0, 1fr) 28px;
      gap: 8px;
      align-items: center;
    }}
    .radar-label {{ font-size: 12px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .radar-track {{ height: 6px; background: #e8edf5; border-radius: 999px; overflow: hidden; }}
    .radar-track span {{ display: block; height: 100%; border-radius: 999px; }}
    .radar-score {{ font-size: 13px; font-weight: 700; text-align: right; }}

    h2, h3 {{ margin: 0; }}
    .section > p {{ margin: 8px 0 0; color: var(--muted); }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 11px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: var(--bg);
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .num {{ width: 48px; color: var(--muted); font-variant-numeric: tabular-nums; }}
    .dim-name {{ min-width: 200px; }}
    .score-cell {{ width: 140px; }}
    .score-bar {{
      margin-top: 6px;
      height: 6px;
      border-radius: 999px;
      background: #e8edf5;
      overflow: hidden;
    }}
    .score-bar span {{ display: block; height: 100%; border-radius: 999px; }}
    .evidence {{ margin-top: 4px; color: var(--muted); font-size: 12px; line-height: 1.55; }}
    .ev-toggle {{ background: none; border: none; color: var(--blue); cursor: pointer; font-size: 11px; font-weight: 600; padding: 0; margin-top: 2px; }}
    .ev-toggle:hover {{ text-decoration: underline; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 2px 10px;
      font-size: 11px;
      font-weight: 800;
      background: var(--blue-bg);
      color: var(--blue);
      white-space: nowrap;
    }}
    .status-pass, .ready-yes {{ background: var(--green-bg); color: var(--green); }}
    .status-warn, .ready-partial {{ background: var(--yellow-bg); color: var(--yellow); }}
    .status-fail, .ready-no {{ background: var(--red-bg); color: var(--red); }}
    .ready-warn {{ background: #fef0ca; color: #8a5f00; }}

    /* Bars */
    .bar-row {{
      display: grid;
      grid-template-columns: 170px minmax(0, 1fr) 110px;
      gap: 10px;
      align-items: center;
      margin: 8px 0;
    }}
    .bar-label {{ font-weight: 600; font-size: 13px; }}
    .bar-track {{
      height: 8px;
      background: #e8edf5;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-track span {{ display: block; height: 100%; background: var(--blue); border-radius: 999px; }}
    .bar-count {{ color: var(--muted); text-align: right; font-size: 13px; font-variant-numeric: tabular-nums; }}
    .bar-count span {{ font-size: 11px; color: #9aa8c0; }}

    .two-col {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 20px;
    }}
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .metric-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      background: #fbfcfe;
    }}
    .metric-label {{ color: var(--muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }}
    .metric-value {{ margin-top: 4px; font-size: 28px; font-weight: 800; letter-spacing: -0.02em; }}
    .metric-note {{ margin-top: 4px; color: var(--muted); font-size: 12px; }}

    /* Failure patterns */
    .fail-table th, .fail-table td {{ padding: 10px 10px; }}
    .fail-row td:first-child {{ min-width: 140px; }}
    .fail-bar {{
      height: 6px;
      border-radius: 999px;
      background: #e8edf5;
      overflow: hidden;
      min-width: 60px;
    }}
    .fail-bar span {{ display: block; height: 100%; border-radius: 999px; }}
    .fail-high .fail-bar span {{ background: var(--red); }}
    .fail-med .fail-bar span {{ background: var(--yellow); }}
    .fail-low .fail-bar span {{ background: var(--blue); }}

    /* Findings table */
    .findings-scroll {{ overflow-x: auto; }}
    .findings-table {{ font-size: 13px; min-width: 800px; }}
    .findings-table th, .findings-table td {{ padding: 9px 10px; }}
    .findings-table th {{ white-space: nowrap; }}
    .findings-table td:last-child {{ min-width: 180px; max-width: 400px; }}
    .find-session {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; white-space: nowrap; }}
    .find-type {{ font-size: 12px; white-space: nowrap; }}
    .find-metrics {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
    .find-metrics .m {{ display: inline-block; min-width: 28px; font-size: 12px; }}
    .find-metrics .m + .m {{ margin-left: 4px; }}
    .find-pattern {{ font-size: 12px; line-height: 1.5; color: var(--ink); white-space: normal; min-width: 180px; }}
    .find-outcome {{ font-size: 12px; line-height: 1.5; color: var(--muted); }}
    .find-legend {{ cursor: help; color: #9aa8c0; font-size: 12px; margin-left: 2px; }}

    /* Action plan */
    .action-list {{ list-style: none; padding: 0; margin: 0; }}
    .action-item {{
      display: flex;
      gap: 14px;
      padding: 14px 0;
      border-bottom: 1px solid var(--line);
    }}
    .action-item:last-child {{ border-bottom: 0; }}
    .action-num {{
      flex-shrink: 0;
      width: 28px; height: 28px;
      border-radius: 99px;
      background: var(--blue-bg);
      color: var(--blue);
      font-weight: 800;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .action-body strong {{ font-size: 15px; }}
    .action-body p {{ margin: 4px 0; color: var(--muted); font-size: 13px; line-height: 1.5; }}
    .files {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; color: #475569; font-size: 12px; margin-top: 4px; background: var(--bg); padding: 4px 8px; border-radius: 4px; display: inline-block; }}

    .muted {{ color: var(--muted); }}
    ul {{ padding-left: 18px; margin: 8px 0 0; }}
    li {{ margin: 6px 0; }}

    /* RAID */
    .raid-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .raid-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      background: #fbfcfe;
    }}
    .raid-card h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin: 0 0 8px; }}
    .raid-card ul {{ padding-left: 14px; margin: 0; }}
    .raid-card li {{ font-size: 13px; margin: 5px 0; line-height: 1.5; }}

    .footer {{
      margin-top: 28px;
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }}

    /* Coverage table */
    .coverage-table th, .coverage-table td {{ padding: 10px 12px; }}

    /* Scroll-to-top */
    .scroll-top {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 40px;
      height: 40px;
      border-radius: 99px;
      background: var(--hero-bg);
      color: white;
      border: none;
      font-size: 18px;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: opacity 0.2s;
      pointer-events: none;
    }}
    .scroll-top.visible {{ opacity: 1; pointer-events: auto; }}

    /* Print */
    @media print {{
      body {{ background: white; }}
      .hero {{ background: var(--ink) !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      .hero-stat {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      .section {{ box-shadow: none; border: 1px solid #ddd; break-inside: avoid; }}
      .toc {{ break-inside: avoid; }}
      .scroll-top {{ display: none !important; }}
      .badge, .bar-track span, .fail-bar span, .score-bar span {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}

    @media (max-width: 860px) {{
      main {{ padding: 0 14px 40px; }}
      .hero {{ padding: 24px 20px; margin: 0 -14px 14px; }}
      .hero h1 {{ font-size: 26px; }}
      .hero-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid-3, .two-col, .raid-grid {{ grid-template-columns: 1fr; }}
      .radar-grid {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 1fr; gap: 4px; }}
      .bar-count {{ text-align: left; }}
      .section {{ padding: 18px 16px; }}
      .toc ul {{ flex-direction: column; gap: 2px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="eyebrow">Agent Readiness Report</div>
      <h1>{esc(project)}</h1>
      <div class="hero-summary">{esc(overall.get("summary", ""))}</div>
      <div class="hero-grid">
        <div class="hero-stat"><strong>{esc(overall.get("name", ""))}</strong><span>Maturity level ({esc(overall.get("level", ""))})</span></div>
        <div class="hero-stat"><strong style="color:{overall_color}">{esc(average)}/5</strong><span>Average readiness score</span></div>
        <div class="hero-stat"><strong>{esc(usage.get("sessionCount", "n/a"))}</strong><span>Sessions analyzed</span></div>
        <div class="hero-stat"><strong style="color:var(--green)">{esc(round(float(rates.get("editSessionsWithValidationAfterEdit", 0)) * 100, 1))}%</strong><span>Edit sessions validated</span></div>
      </div>
    </section>

    {render_toc(report)}

    <section class="section" id="use-case">
      <h2>Use Case</h2>
      <p>{esc(report.get("useCase", ""))}</p>
    </section>

    <section class="section" id="dimension-scores">
      <h2>Dimension Scores</h2>
      <table>
        <thead><tr><th>#</th><th>Dimension</th><th>Score</th><th>Status</th></tr></thead>
        {render_dimensions(dimensions)}
      </table>
    </section>

    <section class="section" id="evidence-summary">
      <h2>Evidence Summary</h2>
      {list_items(as_list(report.get("evidenceSummary")))}
    </section>

    <section class="section" id="agent-usage-pattern">
      <h2>Agent Usage Pattern</h2>
      <div class="grid-3">
        {metric_card("Task finishers", usage.get("classificationCounts", {}).get("task-finisher", 0), "Sessions that edited, validated, and reported completion")}
        {metric_card("Sessions with edits", f'{round(float(rates.get("sessionsWithEdits", 0)) * 100, 1)}%', "Sessions containing code edits")}
        {metric_card("Final report rate", f'{round(float(rates.get("sessionsWithFinalReportMarkers", 0)) * 100, 1)}%', "Sessions with outcome summaries")}
      </div>
      <div class="two-col" style="margin-top: 18px;">
        <div>
          <h3>Classification Distribution</h3>
          {render_classifications(usage.get("classificationCounts", {}))}
        </div>
        <div>
          <h3>Top Failed Tools</h3>
          {render_kv_table(usage.get("topFailedTools", []), "Tool", "Failures")}
        </div>
      </div>
      <h3 style="margin-top: 20px;">Recurring Failure Patterns</h3>
      {render_failure_patterns(usage.get("topFailurePatterns", []), usage.get("sessionCount", 50))}
      <h3 style="margin-top: 20px;">Compact Session Findings</h3>
      {render_compact_findings(as_list(usage.get("compactFindings")))}
      <details style="margin-top: 12px;">
        <summary style="cursor:pointer;color:var(--muted);font-weight:600;font-size:13px;user-select:none;">Deterministic Sample IDs</summary>
        {list_items(as_list(usage.get("sampleIds")))}
      </details>
    </section>

    <section class="section" id="critical-gaps">
      <h2>Critical Gaps</h2>
      <div class="grid-3">
        <div><h3>P0 — Blockers</h3>{list_items(as_list(report.get("criticalGaps", {}).get("p0")))}</div>
        <div><h3>P1 — High Impact</h3>{list_items(as_list(report.get("criticalGaps", {}).get("p1")))}</div>
        <div><h3>P2/P3 — Improvements</h3>{list_items(as_list(report.get("criticalGaps", {}).get("p2")) + as_list(report.get("criticalGaps", {}).get("p3")))}</div>
      </div>
    </section>

    <section class="section" id="recommended-action-plan">
      <h2>Recommended Action Plan</h2>
      {render_action_plan(report.get("actionPlan", []))}
    </section>

    <section class="section" id="spec-to-task-completion-coverage">
      <h2>Spec-To-Task Completion Coverage</h2>
      {render_coverage(report.get("coverage", []))}
    </section>

    <section class="section" id="raid">
      <h2>RAID</h2>
      <div class="raid-grid">
        {render_raid(report.get("raid", {}))}
      </div>
    </section>

    <section class="section" id="validation">
      <h2>Validation</h2>
      {list_items(as_list(report.get("validation")))}
    </section>

    <div class="footer">Generated {esc(generated_at)} &middot; Repo-local assessment for spec-to-tested-task completion</div>
  </main>

  <button class="scroll-top" id="scrollTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="Back to top">&uarr;</button>
  <script>
    const btn = document.getElementById('scrollTop');
    window.addEventListener('scroll', function() {{
      btn.classList.toggle('visible', window.scrollY > 400);
    }});
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-json", required=True, help="Path to the report model JSON")
    parser.add_argument("--output", help="Optional output HTML path. Defaults to stdout.")
    args = parser.parse_args()

    with Path(args.report_json).open() as handle:
        report = json.load(handle)
    output = render_html(report)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
