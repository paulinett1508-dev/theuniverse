#!/usr/bin/env python3
"""Sistema Nervoso (subsistema B): poll da API → eventos → Telegram.

Roda no theuniverse via GitHub Actions. Só observação (leitura). O único
git push é do próprio estado. Reusa o cliente de gh.py.
"""
import os
import sys
import json
import copy
import urllib.request
import urllib.parse
from pathlib import Path

from gh import ROOT, token, api, list_repos

STATE_PATH = ROOT / "state" / "sentinel-state.json"

_EMOJI = {
    "novo_planeta": "🆕",
    "planeta_sumido": "💥",
    "ci_falhou": "🔴",
    "issue_nova": "🚨",
    "secret_exposto": "🔑",
}

TOPICS = {
    "planetas": 2,
    "alertas":  4,
    "ci":       6,
    "pulso":    8,
    "deps":     10,
    "deploy":   12,
    "seguranca": 14,
    "heartbeat": 16,
}

_KIND_TOPIC = {
    "novo_planeta":   TOPICS["planetas"],
    "planeta_sumido": TOPICS["alertas"],
    "ci_falhou":      TOPICS["ci"],
    "issue_nova":     TOPICS["alertas"],
    "secret_exposto": TOPICS["seguranca"],
}


def load_state(path):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def seed_state(snapshot):
    last_run_id = {r: run["id"] for r, run in snapshot["latest_run"].items() if run}
    last_issue = {}
    for r, issues in snapshot["issues"].items():
        if issues:
            last_issue[r] = max(i["number"] for i in issues)
    last_secret = {}
    for r, alerts in snapshot["secrets"].items():
        if alerts:
            last_secret[r] = max(a["number"] for a in alerts)
    return {
        "known_repos": list(snapshot["repos"]),
        "last_run_id": last_run_id,
        "last_issue_number": last_issue,
        "last_secret_alert_number": last_secret,
    }


def compute_events(state, snapshot):
    events = []
    known = set(state["known_repos"])
    cur = set(snapshot["repos"])

    for r in sorted(cur - known):
        events.append({"kind": "novo_planeta", "repo": r})
    for r in sorted(known - cur):
        events.append({"kind": "planeta_sumido", "repo": r})

    for r in sorted(cur & known):
        run = snapshot["latest_run"].get(r)
        if (run and run["conclusion"] == "failure"
                and run["id"] != state["last_run_id"].get(r)):
            events.append({"kind": "ci_falhou", "repo": r,
                           "run_id": run["id"], "detail": run.get("name", "")})
        baseline = state["last_issue_number"].get(r, 0)
        for issue in sorted(snapshot["issues"].get(r, []), key=lambda i: i["number"]):
            if issue["number"] > baseline:
                events.append({"kind": "issue_nova", "repo": r,
                               "number": issue["number"], "detail": issue["title"]})
        secret_baseline = state.get("last_secret_alert_number", {}).get(r, 0)
        for alert in sorted(snapshot["secrets"].get(r, []), key=lambda a: a["number"]):
            if alert["number"] > secret_baseline:
                events.append({"kind": "secret_exposto", "repo": r,
                               "number": alert["number"], "detail": alert["secret_type"]})
    return events


def apply_event(state, event, snapshot):
    s = copy.deepcopy(state)
    kind, repo = event["kind"], event["repo"]
    if kind == "novo_planeta":
        if repo not in s["known_repos"]:
            s["known_repos"].append(repo)
        run = snapshot["latest_run"].get(repo)
        if run:
            s["last_run_id"][repo] = run["id"]
        issues = snapshot["issues"].get(repo, [])
        if issues:
            s["last_issue_number"][repo] = max(i["number"] for i in issues)
    elif kind == "planeta_sumido":
        if repo in s["known_repos"]:
            s["known_repos"].remove(repo)
    elif kind == "ci_falhou":
        s["last_run_id"][repo] = event["run_id"]
    elif kind == "issue_nova":
        s["last_issue_number"][repo] = max(s["last_issue_number"].get(repo, 0), event["number"])
    elif kind == "secret_exposto":
        if "last_secret_alert_number" not in s:
            s["last_secret_alert_number"] = {}
        s["last_secret_alert_number"][repo] = max(
            s["last_secret_alert_number"].get(repo, 0), event["number"]
        )
    return s


_GH = "https://github.com/paulinett1508-dev"


def format_event(event):
    kind = event["kind"]
    repo = event["repo"]
    emoji = _EMOJI[kind]

    if kind == "novo_planeta":
        return (
            f"{emoji} <b>{repo}</b> · novo planeta\n"
            f"\n"
            f"entrou no universo observável\n"
            f"\n"
            f'<a href="{_GH}/{repo}">↗ ver repo</a>'
        )
    if kind == "planeta_sumido":
        return (
            f"💫 <b>{repo}</b> · planeta sumiu\n"
            f"\n"
            f"não consta mais no GitHub"
        )
    if kind == "ci_falhou":
        run_url = f"{_GH}/{repo}/actions/runs/{event['run_id']}"
        detail = event.get("detail", "")
        body = f"workflow: <i>{detail}</i>\n" if detail else ""
        return (
            f"{emoji} <b>{repo}</b> · CI falhou\n"
            f"\n"
            f"{body}"
            f"\n"
            f'<a href="{run_url}">↗ ver run</a>'
        )
    if kind == "issue_nova":
        issue_url = f"{_GH}/{repo}/issues/{event['number']}"
        return (
            f"{emoji} <b>{repo}</b> · issue #{event['number']}\n"
            f"\n"
            f"{event['detail']}\n"
            f"\n"
            f'<a href="{issue_url}">↗ ver issue</a>'
        )
    if kind == "secret_exposto":
        sec_url = f"{_GH}/{repo}/security/secret-scanning"
        return (
            f"{emoji} <b>{repo}</b> · SECRET EXPOSTO\n"
            f"\n"
            f"tipo: <code>{event['detail']}</code>\n"
            f"\n"
            f'<a href="{sec_url}">↗ painel de segurança</a>'
        )
    return f"Evento em {repo}"


def build_heartbeat_report(scanned_repos, detected_events):
    import datetime
    from collections import defaultdict
    brt = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    ts = brt.strftime("%d/%m · %H:%M BRT")
    n = len(scanned_repos)
    n_ev = len(detected_events)

    header = f"🧠 <b>Sistema Nervoso · theuniverse</b>\n{ts} · {n} planetas"

    if not n_ev:
        return f"{header}\n\n✅ universo quieto"

    _SECTIONS = [
        ("ci_falhou",      "🔴", "CI com falha"),
        ("planeta_sumido", "💥", "Planetas sumidos"),
        ("secret_exposto", "🔑", "Segredos expostos"),
        ("issue_nova",     "🚨", "Issues novas"),
        ("novo_planeta",   "🆕", "Novos planetas"),
    ]

    by_type = defaultdict(list)
    for ev in detected_events:
        by_type[ev["type"]].append(ev)

    blocks = []
    for kind, emoji, label in _SECTIONS:
        evs = by_type.get(kind, [])
        if not evs:
            continue
        count = f" ({len(evs)})" if len(evs) > 1 else ""
        lines = [f"{emoji} <b>{label}{count}</b>"]
        for ev in evs:
            repo = ev["repo"]
            detail = ev.get("detail") or ""
            suffix = f" · {detail}" if detail else ""
            lines.append(f"   └ <code>{repo}</code>{suffix}")
        blocks.append("\n".join(lines))

    return f"{header} · {n_ev} evento{'s' if n_ev != 1 else ''}\n\n" + "\n\n".join(blocks)


def build_universe_snapshot(state: dict, detected_events: list) -> bytes:
    import datetime
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"UNIVERSO — SNAPSHOT {ts}",
        "=" * 45,
        "",
        f"Planetas conhecidos: {len(state.get('known_repos', []))}",
    ]
    if detected_events:
        lines += ["", "EVENTOS:", ""]
        for ev in detected_events:
            emoji = _EMOJI.get(ev.get("type", ""), "·")
            detail = f" · {ev['detail']}" if ev.get("detail") else ""
            lines.append(f"  {emoji} {ev['repo']} · {ev['type']}{detail}")
    lines += ["", "ESTADO POR PLANETA:", ""]
    for repo in sorted(state.get("known_repos", [])):
        issues = state.get("last_issue_number", {}).get(repo, 0)
        ci = state.get("last_run_id", {}).get(repo, "-")
        lines.append(f"  {repo}: issues={issues} ci_run={ci}")
    return "\n".join(lines).encode("utf-8")


def send_document(tok: str, chat_id: str, filename: str, content: bytes,
                  caption: str = "", thread_id: int | None = None) -> None:
    boundary = b"TGBoundary1234"

    def _field(name: str, value: str) -> bytes:
        return (b"--" + boundary + b"\r\n"
                b"Content-Disposition: form-data; name=\"" + name.encode() + b"\"\r\n\r\n"
                + value.encode() + b"\r\n")

    parts = [_field("chat_id", str(chat_id))]
    if thread_id is not None:
        parts.append(_field("message_thread_id", str(thread_id)))
    if caption:
        parts.append(_field("caption", caption))
        parts.append(_field("parse_mode", "HTML"))
    parts.append(
        b"--" + boundary + b"\r\n"
        b"Content-Disposition: form-data; name=\"document\"; filename=\""
        + filename.encode() + b"\"\r\n"
        b"Content-Type: text/plain\r\n\r\n"
        + content + b"\r\n"
    )
    parts.append(b"--" + boundary + b"--\r\n")
    body = b"".join(parts)

    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendDocument",
            data=body, method="POST",
        )
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary.decode()}")
        with urllib.request.urlopen(req, timeout=30):
            pass
    except Exception:
        pass


def send_heartbeat(tok, chat_id, report):
    try:
        payload = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": report,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
            "message_thread_id": str(TOPICS["heartbeat"]),
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            data=payload,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30):
            pass
    except Exception:
        pass


def notify(events, state, snapshot, send_fn):
    sent = 0
    for event in events:
        topic = _KIND_TOPIC.get(event["kind"])
        try:
            send_fn(format_event(event), thread_id=topic)
        except Exception as e:
            print(f"  envio falhou ({event['kind']} {event['repo']}): {e}", file=sys.stderr)
            continue
        state = apply_event(state, event, snapshot)
        sent += 1
    return state, sent


def send_telegram(text, thread_id=None):
    tg_token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["SOL_CHAT_ID"]
    params = {
        "chat_id": chat_id, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    if thread_id:
        params["message_thread_id"] = str(thread_id)
    payload = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tg_token}/sendMessage",
        data=payload, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise RuntimeError(f"Telegram status {r.status}")


def build_snapshot(tok):
    repo_objs = list_repos(tok)
    repos = [r["name"] for r in repo_objs]
    full = {r["name"]: r["full_name"] for r in repo_objs}
    latest_run, issues, secrets = {}, {}, {}
    for name in repos:
        fn = full[name]
        try:
            runs, _ = api(f"/repos/{fn}/actions/runs?per_page=1", tok)
            items = runs.get("workflow_runs", [])
            latest_run[name] = (
                {"id": items[0]["id"], "conclusion": items[0].get("conclusion") or "",
                 "name": items[0].get("name", "")}
                if items else None
            )
        except Exception as e:
            print(f"  runs falhou em {fn}: {e}", file=sys.stderr)
            latest_run[name] = None
        try:
            raw, _ = api(f"/repos/{fn}/issues?state=open&sort=created&direction=asc&per_page=100", tok)
            issues[name] = [{"number": i["number"], "title": i["title"]}
                            for i in raw if "pull_request" not in i]
        except Exception as e:
            print(f"  issues falhou em {fn}: {e}", file=sys.stderr)
            issues[name] = []
        try:
            raw, headers = api(
                f"/repos/{fn}/secret-scanning/alerts?state=open&per_page=100", tok
            )
            secrets[name] = [{"number": a["number"], "secret_type": a.get("secret_type", "?")}
                             for a in raw] if isinstance(raw, list) else []
        except Exception:
            secrets[name] = []  # feature não habilitada ou sem permissão — ignorar
    return {"repos": repos, "latest_run": latest_run, "issues": issues, "secrets": secrets}


def main():
    tok = token()
    snapshot = build_snapshot(tok)
    state = load_state(STATE_PATH)
    if state is None:
        save_state(STATE_PATH, seed_state(snapshot))
        print(f"Baseline semeado: {len(snapshot['repos'])} planetas. (sem notificar)")
        return 0

    scanned_repos = list(snapshot["repos"])
    events = compute_events(state, snapshot)
    detected_events = [
        {"type": e["kind"], "repo": e["repo"], "detail": e.get("detail", "")}
        for e in events
    ]

    if not events:
        print("Universo quieto — nenhum evento novo.")
    else:
        new_state, sent = notify(events, state, snapshot, send_telegram)
        save_state(STATE_PATH, new_state)
        print(f"Eventos: {len(events)} detectados, {sent} notificados.")

        # Despacha Artoo para novos CI failures — alerta o mundo do planeta
        ci_failures = [e for e in events if e["kind"] == "ci_falhou"]
        if ci_failures:
            try:
                from artoo import dispatch as artoo_dispatch
                for e in ci_failures:
                    artoo_dispatch(e["repo"], "CI falhou", e.get("detail", ""), tok=tok)
            except Exception as e:
                print(f"  Artoo falhou: {e}", file=sys.stderr)

    tg_token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("SOL_CHAT_ID", "")
    if tg_token and chat_id:
        report = build_heartbeat_report(scanned_repos, detected_events)
        send_heartbeat(tg_token, chat_id, report)
        if detected_events:
            import datetime
            fname = datetime.datetime.utcnow().strftime("universo-%Y%m%d-%H%M.txt")
            state_now = load_state(STATE_PATH) or {}
            snapshot_bytes = build_universe_snapshot(state_now, detected_events)
            send_document(tg_token, chat_id, fname, snapshot_bytes,
                          caption="📊 Snapshot completo do universo",
                          thread_id=TOPICS["heartbeat"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
