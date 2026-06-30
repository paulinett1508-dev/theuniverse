#!/usr/bin/env python3
"""Checkpoint de uso do Claude Code — 3x/dia (12h, 18h, 22h BRT) + alerta de meta semanal."""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
LIMIT_FILE = CLAUDE_DIR / "weekly-limit.json"
STATE_FILE = CLAUDE_DIR / "state" / "weekly-usage-notify-state.json"

_cfg_raw = json.loads(LIMIT_FILE.read_text(encoding="utf-8"))
VAULT = Path(_cfg_raw.get("vaultPath", str(Path.home() / "theuniverse" / ".vault")))

RL_FILE = CLAUDE_DIR / "state" / "rate-limits.json"

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


def get_rate_limits() -> dict:
    """Lê rate_limits gravados pelo statusline.sh a cada interação com Claude Code."""
    if not RL_FILE.exists():
        return {}
    return json.loads(RL_FILE.read_text(encoding="utf-8"))


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
    daily_threshold = float(cfg.get("dailyAlertThreshold", 0.10))
    threshold_pct = int(daily_threshold * 100)

    now_brt = datetime.now(BRT)
    today = now_brt.strftime("%Y-%m-%d")
    hour_label = now_brt.strftime("%Hh")

    state = load_state()
    alert_flagged_today = state.get("alertFlaggedDate") == today

    rl = get_rate_limits()
    seven_day = rl.get("seven_day") or {}
    five_hour = rl.get("five_hour") or {}
    updated_at = rl.get("updated_at", "?")

    week_pct = round(float(seven_day.get("used_percentage", 0)), 1)
    day_pct = round(float(five_hour.get("used_percentage", 0)), 1)

    if not rl:
        print("[usage] AVISO: rate-limits.json ausente — abra uma sessão Claude Code primeiro")
        return

    print(f"[usage] {hour_label} BRT · semana: {week_pct}% · 5h: {day_pct}%")

    vault = read_vault()
    token = vault["TELEGRAM_TOKEN"]
    chat_id = vault["SOL_CHAT_ID"]

    # Alerta de meta — today = janela de 5h atual como proxy do dia
    threshold_crossed = day_pct >= threshold_pct

    if threshold_crossed and not alert_flagged_today:
        bar = build_bar(week_pct)
        msg = (
            f"🔴 <b>Claude Code — Meta Diária Atingida</b>\n\n"
            f"Janela 5h: <b>{day_pct}%</b> · meta: <b>{threshold_pct}%</b>\n"
            f"Semana: <code>{bar}</code> <b>{week_pct}%</b>\n\n"
            f"<i>Reseta sex 08h BRT</i>"
        )
        send_telegram(msg, token, chat_id)
        print("[usage] alerta META enviado")
        state["alertFlaggedDate"] = today
        save_state(state)

    # Checkpoint (sempre, nos 3 horários fixos)
    bar = build_bar(week_pct)
    alert_tag = f" · ⚠️ meta {threshold_pct}%" if threshold_crossed else ""

    resets_at = seven_day.get("resets_at")
    resets_str = ""
    if resets_at:
        resets_dt = datetime.fromtimestamp(resets_at, tz=BRT)
        resets_str = f" · reseta {resets_dt.strftime('%d/%m %Hh')} BRT"

    checkpoint = (
        f"⚡ <b>Claude Code</b> · {hour_label}{alert_tag}\n\n"
        f"   └ semana: <code>{bar}</code> <b>{week_pct}%</b>\n"
        f"   └ janela 5h: <b>{day_pct}%</b>\n\n"
        f"<i>Fonte: Claude Code{resets_str}</i>"
    )
    send_telegram(checkpoint, token, chat_id)
    print(f"[usage] checkpoint {hour_label} enviado")


if __name__ == "__main__":
    main()
