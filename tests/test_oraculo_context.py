import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).parent.parent / "oraculo"))

import context


def test_summarize_repo_computes_idle():
    now = datetime(2026, 6, 19, tzinfo=timezone.utc)
    r = {"name": "zion", "pushed_at": "2026-05-20T00:00:00Z", "language": "Python",
         "open_issues_count": 3, "private": True}
    s = context.summarize_repo(r, now)
    assert s["name"] == "zion"
    assert s["idle_days"] == 30
    assert s["lang"] == "Python"
    assert s["issues"] == 3


def test_format_context_sorts_by_idle_desc():
    summaries = [
        {"name": "vibegaminghub", "idle_days": 5, "lang": "JS", "issues": 0, "private": False},
        {"name": "tokentown", "idle_days": 90, "lang": "Go", "issues": 1, "private": True},
    ]
    out = context.format_context(summaries)
    assert out.index("tokentown") < out.index("vibegaminghub")   # 90d antes de 5d
    assert "90" in out and "Go" in out
