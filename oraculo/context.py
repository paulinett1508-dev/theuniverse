"""Estado vivo do universo, injetado no prompt do Oráculo."""
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh import token, list_repos  # noqa: E402


def summarize_repo(r, now):
    pushed = datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return {
        "name": r["name"],
        "idle_days": (now - pushed).days,
        "lang": r.get("language") or "-",
        "issues": r["open_issues_count"],
        "private": r["private"],
    }


def format_context(summaries):
    lines = ["## Estado atual do universo (via API GitHub)"]
    for s in sorted(summaries, key=lambda x: x["idle_days"], reverse=True):
        vis = "privado" if s["private"] else "público"
        lines.append(f"- {s['name']}: {s['idle_days']}d sem commit · {s['lang']} · "
                     f"{s['issues']} issues · {vis}")
    return "\n".join(lines)


def gather(tok, now=None):
    now = now or datetime.now(timezone.utc)
    summaries = [summarize_repo(r, now) for r in list_repos(tok)]
    return format_context(summaries)
