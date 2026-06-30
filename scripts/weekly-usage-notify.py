#!/usr/bin/env python3
"""Checkpoint de uso do Claude Code — 3x/dia (12h, 18h, 22h BRT) + alerta de meta semanal."""
import json
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
LIMIT_FILE = CLAUDE_DIR / "weekly-limit.json"
STATE_FILE = CLAUDE_DIR / "state" / "weekly-usage-notify-state.json"

_cfg_raw = json.loads(LIMIT_FILE.read_text(encoding="utf-8"))
VAULT = Path(_cfg_raw.get("vaultPath", str(Path.home() / "theuniverse" / ".vault")))

CCUSAGE = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "ccusage" / "dist" / "cli.js"

BRT = timezone(timedelta(hours=-3))


def read_vault():
    d = {}
    for line in VAULT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def send_telegram(text, token, chat_id):
    params = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def get_blocks():
    result = subprocess.run(
        ["node.exe", str(CCUSAGE), "blocks", "--json"],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout).get("blocks", [])


def get_weekly_tokens(blocks):
    """Soma todos os blocos dos últimos 7 dias (todos os modelos)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    total = 0
    for b in blocks:
        if b.get("isGap"):
            continue
        start = datetime.fromisoformat(b["startTime"].replace("Z", "+00:00"))
        if start >= cutoff:
            total += b.get("totalTokens", 0)
    return total


def get_active_block(blocks):
    for b in blocks:
        if b.get("isActive"):
            return b
    return None


def fmt(n):
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B".replace(".", ",")
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".", ",")
    return f"{n:,}".replace(",", ".")


def build_bar(pct, length=10):
    filled = int(round(pct / 100 * length))
    return "█" * min(filled, length) + "░" * max(length - filled, 0)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main():
    cfg = json.loads(LIMIT_FILE.read_text(encoding="utf-8"))
    weekly_limit = int(cfg["weeklyTokenLimit"])
    daily_threshold = float(cfg.get("dailyAlertThreshold", 0.10))

    now_brt = datetime.now(BRT)
    today = now_brt.strftime("%Y-%m-%d")
    hour_label = now_brt.strftime("%Hh")

    state = load_state()
    alert_flagged_today = state.get("alertFlaggedDate") == today

    blocks = get_blocks()
    weekly_tokens = get_weekly_tokens(blocks)
    active = get_active_block(blocks)

    week_pct = round(weekly_tokens / weekly_limit * 100, 1)
    threshold_pct = int(daily_threshold * 100)

    print(f"[usage] {hour_label} BRT · semana: {fmt(weekly_tokens)} ({week_pct}%)")

    vault = read_vault()
    token = vault["TELEGRAM_TOKEN"]
    chat_id = vault["SOL_CHAT_ID"]

    # Alerta de meta semanal — calculado sobre o dia de hoje nos blocos
    today_tokens = sum(
        b.get("totalTokens", 0) for b in blocks
        if not b.get("isGap") and
        datetime.fromisoformat(b["startTime"].replace("Z", "+00:00"))
        .astimezone(BRT).strftime("%Y-%m-%d") == today
    )
    today_pct = round(today_tokens / weekly_limit * 100, 1)
    threshold_crossed = today_pct >= threshold_pct

    if threshold_crossed and not alert_flagged_today:
        bar = build_bar(week_pct)
        msg = (
            f"🔴 <b>Claude Code — Meta Diária Atingida</b>\n\n"
            f"Hoje: <b>{today_pct}%</b> da cota semanal · meta: <b>{threshold_pct}%</b>\n"
            f"Semana: <code>{bar}</code> <b>{week_pct}%</b>\n\n"
            f"Hoje: <b>{fmt(today_tokens)}</b> · Semana: <b>{fmt(weekly_tokens)}</b>\n"
            f"<i>Limite: {fmt(weekly_limit)} · Reseta sex 08h BRT</i>"
        )
        send_telegram(msg, token, chat_id)
        print(f"[usage] alerta META enviado")
        state["alertFlaggedDate"] = today
        save_state(state)

    # Checkpoint (sempre, nos 3 horários fixos)
    bar = build_bar(week_pct)
    alert_tag = f" · ⚠️ meta {threshold_pct}%" if threshold_crossed else ""

    session_line = ""
    if active:
        session_tokens = active.get("totalTokens", 0)
        cost = active.get("costUSD", 0)
        proj = active.get("projection", {})
        proj_cost = proj.get("totalCost", 0) if proj else 0
        end_brt = datetime.fromisoformat(
            active["endTime"].replace("Z", "+00:00")
        ).astimezone(BRT).strftime("%Hh")
        models = active.get("models", [])
        model_tag = "opus+" if any("opus" in m for m in models) else "sonnet"
        proj_tag = f" → proj ${proj_cost:.2f}" if proj_cost > cost else ""
        session_line = (
            f"\n   └ sessão até {end_brt}: {fmt(session_tokens)} · ${cost:.2f} [{model_tag}]{proj_tag}"
        )

    checkpoint = (
        f"⚡ <b>Claude Code</b> · {hour_label}{alert_tag}\n\n"
        f"   └ semana: <code>{bar}</code> <b>{week_pct}%</b>"
        f"{session_line}\n\n"
        f"<i>{fmt(weekly_tokens)} / {fmt(weekly_limit)} · Reseta sex 08h BRT</i>"
    )
    send_telegram(checkpoint, token, chat_id)
    print(f"[usage] checkpoint {hour_label} enviado")


if __name__ == "__main__":
    main()
