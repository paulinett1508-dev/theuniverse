#!/usr/bin/env python3
"""Notificador de uso semanal do Claude Code.

Roda diariamente (Task Scheduler). Envia alerta no Telegram quando o uso
do dia corrente atingir >= DAILY_ALERT_PCT do limite semanal configurado.
"""
import json
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / ".vault"
LIMIT_FILE = Path.home() / ".claude" / "weekly-limit.json"
STATE_FILE = ROOT / "state" / "weekly-usage-notify-state.json"

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
    # janela deslizante de 7 dias — igual ao plano Max
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
    days = data.get("daily", [])
    return sum(d.get("totalTokens", 0) for d in days)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main():
    cfg = json.loads(LIMIT_FILE.read_text(encoding="utf-8"))
    limit = int(cfg["weeklyTokenLimit"])
    threshold = float(cfg.get("dailyAlertThreshold", 0.10))

    today = datetime.now().strftime("%Y-%m-%d")
    state = load_state()

    # Não notifica duas vezes no mesmo dia
    if state.get("lastAlertDate") == today:
        print(f"[weekly-notify] alerta já enviado hoje ({today}), pulando.")
        return

    weekly_tokens = get_weekly_tokens()
    today_tokens  = get_today_tokens()

    week_pct  = round(weekly_tokens / limit * 100, 1)
    today_pct = round(today_tokens  / limit * 100, 1)

    print(f"[weekly-notify] semana: {weekly_tokens:,} tokens ({week_pct}%)")
    print(f"[weekly-notify] hoje:   {today_tokens:,} tokens ({today_pct}%)")

    if today_pct >= threshold * 100:
        vault = read_vault()
        token = vault["TELEGRAM_TOKEN"]
        chat_id = vault["SOL_CHAT_ID"]

        bar_len = 10
        filled  = int(round(week_pct / 100 * bar_len))
        bar     = "█" * min(filled, bar_len) + "░" * max(bar_len - filled, 0)

        msg = (
            f"⚡ <b>Claude Code — Uso Semanal</b>\n\n"
            f"Hoje você consumiu <b>{today_pct}%</b> do limite semanal.\n\n"
            f"Semana: <code>{bar}</code> {week_pct}%\n"
            f"Hoje: <b>{today_tokens:,}</b> tokens\n"
            f"Semana: <b>{weekly_tokens:,}</b> tokens\n\n"
            f"<i>Limite semanal: {limit:,} tokens</i>"
        )

        send_telegram(msg, token, chat_id, thread_id=TOPIC_ALERTAS)
        print(f"[weekly-notify] alerta enviado — {today_pct}% no dia")

        state["lastAlertDate"] = today
        state["lastAlertWeekPct"] = week_pct
        state["lastAlertTodayPct"] = today_pct
        save_state(state)
    else:
        print(f"[weekly-notify] abaixo do limiar ({threshold*100}%), sem alerta.")


if __name__ == "__main__":
    main()
