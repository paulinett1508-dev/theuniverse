#!/usr/bin/env python3
"""Notificador de uso do Claude Code — digest a cada 2h + alerta de threshold."""
import json
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
LIMIT_FILE = CLAUDE_DIR / "weekly-limit.json"
STATE_FILE = CLAUDE_DIR / "state" / "weekly-usage-notify-state.json"

_cfg_raw = json.loads(LIMIT_FILE.read_text(encoding="utf-8"))
VAULT    = Path(_cfg_raw.get("vaultPath", str(Path.home() / "theuniverse" / ".vault")))

CCUSAGE = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "ccusage" / "dist" / "cli.js"

TOPIC_ALERTAS = 4


def read_vault():
    d = {}
    for line in VAULT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def send_telegram(text, token, chat_id, thread_id=None):
    params = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if thread_id:
        params["message_thread_id"] = thread_id
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def week_start_str():
    return (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")


def get_weekly_tokens():
    result = subprocess.run(
        ["node.exe", str(CCUSAGE), "weekly", "--json", "--since", week_start_str()],
        capture_output=True, text=True, timeout=30
    )
    data = json.loads(result.stdout)
    return sum(w.get("totalTokens", 0) for w in data.get("weekly", []))


def get_today_tokens():
    today_str = datetime.now().strftime("%Y%m%d")
    result = subprocess.run(
        ["node.exe", str(CCUSAGE), "daily", "--json", "--since", today_str, "--until", today_str],
        capture_output=True, text=True, timeout=30
    )
    data = json.loads(result.stdout)
    return sum(d.get("totalTokens", 0) for d in data.get("daily", []))


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def fmt(n):
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B".replace(".", ",")
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".", ",")
    return f"{n:,}".replace(",", ".")


def build_bar(pct, length=10):
    filled = int(round(pct / 100 * length))
    return "█" * min(filled, length) + "░" * max(length - filled, 0)


def main():
    cfg = json.loads(LIMIT_FILE.read_text(encoding="utf-8"))
    limit = int(cfg["weeklyTokenLimit"])
    threshold = float(cfg.get("dailyAlertThreshold", 0.10))

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour_label = now.strftime("%H:%M")

    state = load_state()
    threshold_flagged_today = state.get("thresholdFlaggedDate") == today

    weekly_tokens = get_weekly_tokens()
    today_tokens  = get_today_tokens()

    week_pct  = round(weekly_tokens / limit * 100, 1)
    today_pct = round(today_tokens  / limit * 100, 1)

    print(f"[weekly-notify] {hour_label} · semana: {fmt(weekly_tokens)} ({week_pct}%) · hoje: {fmt(today_tokens)} ({today_pct}%)")

    vault = read_vault()
    token = vault["TELEGRAM_TOKEN"]
    chat_id = vault["SOL_CHAT_ID"]

    alert_pct = int(threshold * 100)
    threshold_crossed = today_pct >= threshold * 100

    # Alerta de threshold — 1x por dia quando cruzar a meta
    if threshold_crossed and not threshold_flagged_today:
        week_before = round(week_pct - today_pct, 1)
        bar = build_bar(week_pct)
        msg = (
            f"🔴 <b>Claude Code — Meta Diária Atingida</b>\n\n"
            f"⚠️ Você consumiu <b>{today_pct}%</b> da cota semanal hoje"
            f" — meta de <b>{alert_pct}%</b> atingida.\n\n"
            f"Semana: <code>{bar}</code> <b>{week_pct}%</b> usada\n"
            f"<i>(iniciou hoje em {week_before}% · +{today_pct}% no dia)</i>\n\n"
            f"Hoje: <b>{fmt(today_tokens)}</b> · Semana: <b>{fmt(weekly_tokens)}</b>\n"
            f"<i>Limite: {fmt(limit)} · Reseta sex 08h BRT</i>"
        )
        send_telegram(msg, token, chat_id, thread_id=TOPIC_ALERTAS)
        print(f"[weekly-notify] alerta META enviado")
        state["thresholdFlaggedDate"] = today
        save_state(state)

    # Digest a cada execução (sempre)
    bar = build_bar(week_pct)
    threshold_tag = f" · ⚠️ meta {alert_pct}% atingida" if threshold_crossed else ""
    digest = (
        f"⚡ <b>Claude Code</b> · {hour_label}\n\n"
        f"Semana: <code>{bar}</code> <b>{week_pct}%</b>{threshold_tag}\n"
        f"Hoje: <b>{today_pct}%</b> ({fmt(today_tokens)})\n\n"
        f"<i>{fmt(weekly_tokens)} / {fmt(limit)} · Reseta sex 08h BRT</i>"
    )
    send_telegram(digest, token, chat_id, thread_id=TOPIC_ALERTAS)
    print(f"[weekly-notify] digest enviado")


if __name__ == "__main__":
    main()
