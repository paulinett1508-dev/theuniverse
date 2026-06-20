"""Webhook receiver: GitHub → Telegram. Notifica commits e PRs do universo."""
import hashlib
import hmac
import json
import logging
import os
import sys
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

load_dotenv("/opt/oraculo/.env")

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("webhook")

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
SOL_CHAT_ID = os.environ["SOL_CHAT_ID"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

app = FastAPI(title="Universe Webhook Receiver")


# ── auth ──────────────────────────────────────────────────────────────────────

def _verify(payload: bytes, sig_header: str) -> bool:
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


# ── telegram ──────────────────────────────────────────────────────────────────

def _send(text: str) -> None:
    try:
        r = httpx.post(TELEGRAM_API, json={
            "chat_id": SOL_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
        r.raise_for_status()
    except Exception as e:
        log.error("telegram send failed: %s", e)


# ── formatters ────────────────────────────────────────────────────────────────

def _parse_time(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%H:%M")
    except Exception:
        return ""


def _fmt_push(data: dict) -> str | None:
    ref = data.get("ref", "")
    if ref.startswith("refs/tags/"):
        return None

    commits = data.get("commits", [])
    if not commits:
        return None

    branch = ref.replace("refs/heads/", "")
    repo = data["repository"]["name"]
    pusher = data.get("pusher", {}).get("name", "?")

    if len(commits) == 1:
        msg = commits[0]["message"].split("\n")[0][:80]
        url = commits[0]["url"]
        ts = _parse_time(commits[0].get("timestamp", ""))
        time_part = f" · {ts}" if ts else ""
        return (
            f"🌍 <b>{repo}</b> · <code>{branch}</code>{time_part}\n"
            f"\n"
            f"{msg}\n"
            f"— {pusher}\n"
            f"\n"
            f'<a href="{url}">↗ ver commit</a>'
        )

    lines = "\n".join(
        f"  · {c['message'].split(chr(10))[0][:60]}" for c in commits[:4]
    )
    extra = f"\n  +{len(commits) - 4} mais" if len(commits) > 4 else ""
    url = data.get("compare", "")
    ts = _parse_time(commits[-1].get("timestamp", ""))
    time_part = f" · {ts}" if ts else ""
    return (
        f"🌍 <b>{repo}</b> · <code>{branch}</code>{time_part}  ({len(commits)} commits)\n"
        f"\n"
        f"{lines}{extra}\n"
        f"— {pusher}\n"
        f"\n"
        f'<a href="{url}">↗ ver diff</a>'
    )


def _fmt_pr(data: dict) -> str | None:
    action = data.get("action")
    pr = data.get("pull_request", {})
    repo = data["repository"]["name"]
    title = pr.get("title", "")[:80]
    url = pr.get("html_url", "")
    user = pr.get("user", {}).get("login", "?")
    number = pr.get("number", "?")

    if action == "opened":
        base = pr["base"]["ref"]
        head = pr["head"]["ref"]
        return (
            f"🔀 <b>{repo}</b> · PR #{number}\n"
            f"\n"
            f"{title}\n"
            f"<code>{head}</code> → <code>{base}</code>\n"
            f"— {user}\n"
            f"\n"
            f'<a href="{url}">↗ ver PR</a>'
        )
    if action == "closed":
        if pr.get("merged"):
            merger = (pr.get("merged_by") or {}).get("login", "?")
            return (
                f"✅ <b>{repo}</b> · PR #{number}\n"
                f"\n"
                f"{title}\n"
                f"— mergeado por {merger}\n"
                f"\n"
                f'<a href="{url}">↗ ver PR</a>'
            )
        return (
            f"❌ <b>{repo}</b> · PR #{number}\n"
            f"\n"
            f"{title}\n"
            f"— fechado sem merge\n"
            f"\n"
            f'<a href="{url}">↗ ver PR</a>'
        )
    if action == "reopened":
        return (
            f"🔄 <b>{repo}</b> · PR #{number}\n"
            f"\n"
            f"{title}\n"
            f"\n"
            f'<a href="{url}">↗ ver PR</a>'
        )
    return None


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhook")
async def receive(request: Request):
    payload = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")

    if not _verify(payload, sig):
        log.warning("invalid signature from %s", request.client)
        raise HTTPException(status_code=401, detail="invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    data = json.loads(payload)
    repo = data.get("repository", {}).get("full_name", "?")
    log.info("event=%s repo=%s", event, repo)

    text = None
    if event == "push":
        text = _fmt_push(data)
    elif event == "pull_request":
        text = _fmt_pr(data)

    if text:
        _send(text)

    return JSONResponse({"ok": True})
