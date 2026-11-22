"""
@file dependabot_alerts.py
@description The open Dependabot alerts that no open Dependabot PR covers, each with the reason
    GitHub opened none and what to do (/start Step 0b). Always prints how many alerts are open
    and how many a PR covers, so an empty list can be told apart from a check that read nothing.
    It reports only: a fix by hand keeps the 72 h window a Dependabot PR waits, so the community
    can report a bad release first.

    Free: two read-only gh calls (the repo's open alerts, its Dependabot PRs). Stdlib only, so
    one file serves every repo; this copy differs from the canonical one only in this header.

    Usage: python3 scripts/internal/dependabot_alerts.py

@author ScarcityTransitionSim_Dev
@version 1.0.0
@date 2026-11-02
@changelog
- 2026-11-02: v1.0.0 - Initial creation
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta

# GitHub opens a security PR within minutes to hours of an alert; a younger alert is not yet a gap.
NEW_ALERT = timedelta(days=1)
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

ALERTS_QUERY = (
    ".[] | {number, package: .dependency.package.name, severity: .security_advisory.severity,"
    " patched: .security_vulnerability.first_patched_version.identifier,"
    " relationship: .dependency.relationship, created: .created_at, url: .html_url}"
)


def package_key(name: str) -> str:
    """A package name as the registries compare it: case and -_. separators ignored."""
    return re.sub(r"[-_.]+", "-", name).lower()


def pr_package(title: str, head_ref: str) -> str | None:
    """The package a Dependabot PR updates, from its title or else its branch.

    Args:
        title: "Bump <package> from <old> to <new>".
        head_ref: "dependabot/<ecosystem>/<package>-<version>".

    Returns:
        The package's key, or None for a PR that names no single package (a grouped update).
    """
    m = re.match(r"^Bump (\S+) from ", title) or re.match(
        r"^dependabot/[^/]+/(.+)-\d[^/]*$", head_ref
    )
    return package_key(m.group(1)) if m else None


def no_pr_reason(alert: dict, open_prs: dict, closed_prs: dict, now: datetime) -> str | None:
    """Why no open Dependabot PR covers this alert, and what to do; None when one does.

    Args:
        alert: One open alert: package, patched (None when no fix is released), created.
        open_prs: Package key -> number of an open Dependabot PR.
        closed_prs: Package key -> number of a Dependabot PR closed without a merge.
        now: The current time, UTC.
    """
    key = package_key(alert["package"])
    if key in open_prs:
        return None
    if not alert.get("patched"):
        return "no fixed version is released: migrate off the package, or accept it with a note"
    created = datetime.fromisoformat(alert["created"].replace("Z", "+00:00"))
    if now - created < NEW_ALERT:
        return "opened less than a day ago: the PR may still come"
    if key in closed_prs:
        return (
            f"its Dependabot PR #{closed_prs[key]} was closed unmerged (ignored or superseded):"
            " read that PR's last comment"
        )
    return (
        "GitHub opened none: the alert page says why (most often the fixed version conflicts"
        " with another pin). A fix by hand waits until the fixed release is 72 h old, as a"
        " Dependabot PR does, then takes the same audit"
    )


def report(alerts: list[dict], prs: list[dict], now: datetime) -> list[str]:
    """The briefing's lines: the count first, then one line per package left without a PR."""
    open_prs, closed_prs = {}, {}
    for pr in prs:
        key = pr_package(pr.get("title", ""), pr.get("headRefName", ""))
        if not key:
            continue
        if pr["state"] == "OPEN":
            open_prs[key] = pr["number"]
        elif pr["state"] == "CLOSED" and not pr.get("mergedAt"):
            closed_prs.setdefault(key, pr["number"])

    gaps: dict[str, list[dict]] = {}
    for alert in alerts:
        if no_pr_reason(alert, open_prs, closed_prs, now):
            gaps.setdefault(package_key(alert["package"]), []).append(alert)

    without = sum(len(group) for group in gaps.values())
    lines = [
        f"{len(alerts)} open alerts: {len(alerts) - without} covered by an open Dependabot PR,"
        f" {without} without one ({len(gaps)} package{'' if len(gaps) == 1 else 's'})"
    ]
    ranked = sorted(
        gaps.values(),
        key=lambda g: (min(SEVERITY_ORDER.get(a["severity"], 9) for a in g), g[0]["package"]),
    )
    for group in ranked:
        first = min(group, key=lambda a: SEVERITY_ORDER.get(a["severity"], 9))
        fixed = first.get("patched") or "none"
        numbers = ", ".join(f"#{a['number']}" for a in sorted(group, key=lambda a: a["number"]))
        lines.append(
            f"- {first['severity'].upper()} {first['package']} ({numbers}; fixed in {fixed};"
            f" {first.get('relationship') or 'unknown'}): "
            f"{no_pr_reason(first, open_prs, closed_prs, now)}. {first['url']}"
        )
    return lines


def _gh(*args: str) -> str:
    """Run one read-only gh command and return its output; exit with gh's error on failure."""
    done = subprocess.run(["gh", *args], capture_output=True, text=True)
    if done.returncode != 0:
        first = (done.stderr.strip().splitlines() or ["no output"])[0]
        sys.exit(f"Could not read Dependabot data (gh {args[0]}): {first}")
    return done.stdout


def main() -> None:
    """Print the open alerts no Dependabot PR covers, with the count first."""
    alerts_raw = _gh(
        "api",
        "repos/{owner}/{repo}/dependabot/alerts?state=open&per_page=100",
        "--paginate",
        "--jq",
        ALERTS_QUERY,
    )
    alerts = [json.loads(line) for line in alerts_raw.splitlines() if line.strip()]
    prs = json.loads(
        _gh(
            "pr",
            "list",
            "--author",
            "app/dependabot",
            "--state",
            "all",
            "--limit",
            "300",
            "--json",
            "number,state,title,headRefName,mergedAt",
        )
    )
    print("\n".join(report(alerts, prs, datetime.now(UTC))))


if __name__ == "__main__":
    main()
