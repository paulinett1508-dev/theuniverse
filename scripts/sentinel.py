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


def notify(events, state, snapshot, send_fn):
    sent = 0
    for event in events:
        try:
            send_fn(format_event(event))
        except Exception as e:
            print(f"  envio falhou ({event['kind']} {event['repo']}): {e}", file=sys.stderr)
            continue
        state = apply_event(state, event, snapshot)
        sent += 1
    return state, sent


def send_telegram(text):
    tg_token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["SOL_CHAT_ID"]
    payload = urllib.parse.urlencode({
        "chat_id": chat_id, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
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
    events = compute_events(state, snapshot)
    if not events:
        print("Universo quieto — nenhum evento novo.")
        return 0
    new_state, sent = notify(events, state, snapshot, send_telegram)
    save_state(STATE_PATH, new_state)
    print(f"Eventos: {len(events)} detectados, {sent} notificados.")

    # Despacha Voyager para novos CI failures — alerta o mundo do planeta
    ci_failures = [e for e in events if e["kind"] == "ci_falhou"]
    if ci_failures:
        try:
            from voyager import dispatch as voyager_dispatch
            for e in ci_failures:
                voyager_dispatch(e["repo"], "CI falhou", e.get("detail", ""), tok=tok)
        except Exception as e:
            print(f"  Voyager falhou: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
