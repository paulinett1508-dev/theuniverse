#!/usr/bin/env python3
"""Sentinel · Pulso: monitora uptime das URLs de produção dos planetas.

Descobre URLs via campo `homepage` da API GitHub (configurado no repo).
Roda a cada 15 min via Actions. Notifica no Telegram ao detectar queda ou
retorno. Sempre envia heartbeat ao final — sem silêncio no universo.
Só stdlib.
"""
import html
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

from gh import ROOT, token, list_repos
from sentinel import send_telegram, TOPICS
_TOPIC = TOPICS["pulso"]

STATE_PATH = ROOT / "state" / "pulso-state.json"
TIMEOUT_S = 10


def filter_urls(repos):
    """Pure: extrai URLs válidas dos objetos de repo da API GitHub."""
    result = []
    for r in repos:
        hp = (r.get("homepage") or "").strip()
        if hp.startswith("http"):
            result.append({"repo": r["name"], "url": hp})
    return result


def check_url(entry):
    url, repo = entry["url"], entry["repo"]
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "theuniverse-pulso"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            status = r.status
        latency_ms = int((time.monotonic() - t0) * 1000)
        ok = 200 <= status < 400
    except urllib.error.HTTPError as e:
        status = e.code
        latency_ms = int((time.monotonic() - t0) * 1000)
        ok = False
    except Exception:
        status = 0
        latency_ms = int((time.monotonic() - t0) * 1000)
        ok = False
    return {"repo": repo, "url": url, "ok": ok,
            "status": status, "latency_ms": latency_ms}


def compute_events(state, results):
    """Pure: compara resultados com estado anterior, devolve eventos de mudança."""
    prev = state.get("status", {})
    events = []
    for r in results:
        url, ok = r["url"], r["ok"]
        was_up = prev.get(url, True)
        if was_up and not ok:
            events.append({"kind": "url_caiu", "url": url, "repo": r["repo"],
                           "status": r["status"], "latency_ms": r["latency_ms"]})
        elif not was_up and ok:
            events.append({"kind": "url_voltou", "url": url, "repo": r["repo"],
                           "status": r["status"], "latency_ms": r["latency_ms"]})
    return events


def format_event(ev):
    if ev["kind"] == "url_caiu":
        return (f"🔴 <b>{html.escape(ev['repo'])}</b> caiu\n"
                f"   └ <code>{html.escape(ev['url'])}</code>\n"
                f"   └ HTTP <code>{ev['status']}</code> · <code>{ev['latency_ms']}ms</code>")
    return (f"🟢 <b>{html.escape(ev['repo'])}</b> voltou\n"
            f"   └ <code>{html.escape(ev['url'])}</code>\n"
            f"   └ HTTP <code>{ev['status']}</code> · <code>{ev['latency_ms']}ms</code>")


def build_report(results, events):
    import datetime
    brt = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    ts = brt.strftime("%d/%m · %H:%M BRT")
    total = len(results)
    up = sum(1 for r in results if r["ok"])
    down = total - up
    header = f"💓 <b>Pulso · theuniverse</b>\n{ts} · {total} URLs · ✅ {up} · 🔴 {down}"
    if not events:
        return f"{header}\n\n✅ tudo no ar"
    quedas = [ev for ev in events if ev["kind"] == "url_caiu"]
    retornos = [ev for ev in events if ev["kind"] == "url_voltou"]
    blocks = []
    if quedas:
        count = f" ({len(quedas)})" if len(quedas) > 1 else ""
        lines = [f"🔴 <b>Quedas{count}</b>"]
        for ev in quedas:
            lines.append(
                f"   └ <code>{html.escape(ev['repo'])}</code> · "
                f"<code>{html.escape(ev['url'])}</code> · "
                f"HTTP <code>{ev['status']}</code> · <code>{ev['latency_ms']}ms</code>"
            )
        blocks.append("\n".join(lines))
    if retornos:
        count = f" ({len(retornos)})" if len(retornos) > 1 else ""
        lines = [f"🟢 <b>Retornos{count}</b>"]
        for ev in retornos:
            lines.append(
                f"   └ <code>{html.escape(ev['repo'])}</code> · "
                f"<code>{html.escape(ev['url'])}</code> · "
                f"HTTP <code>{ev['status']}</code> · <code>{ev['latency_ms']}ms</code>"
            )
        blocks.append("\n".join(lines))
    n = len(events)
    return f"{header} · {n} evento{'s' if n != 1 else ''}\n\n" + "\n\n".join(blocks)


def load_state(path):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def main():
    tok = token()
    repos = list_repos(tok)
    entries = filter_urls(repos)
    if not entries:
        print("Nenhuma URL de produção encontrada nos repos.")
        return 0

    results = [check_url(e) for e in entries]

    state = load_state(STATE_PATH)
    if state is None:
        save_state(STATE_PATH, {"status": {r["url"]: r["ok"] for r in results}})
        print(f"Estado inicial: {len(results)} URLs. Próxima run detectará mudanças.")
        try:
            send_telegram(build_report(results, []), thread_id=_TOPIC)
        except Exception:
            pass
        return 0

    events = compute_events(state, results)
    for ev in events:
        try:
            send_telegram(format_event(ev), thread_id=_TOPIC)
        except Exception as e:
            print(f"  envio falhou ({ev['url']}): {e}")

    save_state(STATE_PATH, {"status": {r["url"]: r["ok"] for r in results}})

    try:
        send_telegram(build_report(results, events), thread_id=_TOPIC)
    except Exception:
        pass

    up = sum(1 for r in results if r["ok"])
    print(f"Pulso: {len(results)} URLs · {up} up · {len(events)} evento(s).")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
