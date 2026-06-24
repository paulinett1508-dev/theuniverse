#!/usr/bin/env python3
"""Sentinel · Deploy: monitora saúde dos deploys via API de Deployments do GitHub.

Vercel (e outras plataformas) criam deployments no GitHub — o status fica
acessível sem token Vercel. Detecta regressões (success→failure) e
recuperações (failure→success). Heartbeat ao final. Só stdlib.
"""
import html
import json
import sys
import time
from pathlib import Path

from gh import ROOT, API, token, list_repos, api as gh_api
from sentinel import send_telegram

STATE_PATH = ROOT / "state" / "deploy-state.json"
TARGET_ENV = "production"


def _fetch_latest_deployment(full_name, tok):
    """Devolve dict {id, state, env} do último deploy em produção, ou None."""
    try:
        deploys, _ = gh_api(
            f"/repos/{full_name}/deployments?environment={TARGET_ENV}&per_page=1", tok)
        if not deploys:
            return None
        dep = deploys[0]
        statuses, _ = gh_api(
            f"/repos/{full_name}/deployments/{dep['id']}/statuses?per_page=1", tok)
        state = statuses[0]["state"] if statuses else "unknown"
        return {"id": dep["id"], "state": state, "env": dep.get("environment", TARGET_ENV)}
    except Exception as e:
        print(f"  deploy fetch falhou em {full_name}: {e}", file=sys.stderr)
        return None


def compute_events(state, current):
    """Pure: compara deployment atual com estado anterior."""
    prev = state.get("last", {})
    events = []
    for repo, dep in current.items():
        old = prev.get(repo)
        if old is None:
            if dep["state"] in ("failure", "error"):
                events.append({"kind": "deploy_falhou", "repo": repo,
                               "env": dep["env"], "deployment_id": dep["id"]})
            continue
        if old["id"] == dep["id"]:
            continue
        if dep["state"] in ("failure", "error") and old["state"] not in ("failure", "error"):
            events.append({"kind": "deploy_falhou", "repo": repo,
                           "env": dep["env"], "deployment_id": dep["id"]})
        elif dep["state"] == "success" and old["state"] in ("failure", "error"):
            events.append({"kind": "deploy_ok", "repo": repo,
                           "env": dep["env"], "deployment_id": dep["id"]})
    return events


def format_event(ev):
    if ev["kind"] == "deploy_falhou":
        return (f"🚨 <b>{html.escape(ev['repo'])}</b> — deploy falhou\n"
                f"env: {html.escape(ev['env'])} · id: {ev['deployment_id']}")
    return (f"✅ <b>{html.escape(ev['repo'])}</b> — deploy recuperado\n"
            f"env: {html.escape(ev['env'])} · id: {ev['deployment_id']}")


def build_report(checked, events):
    footer = "✅ todos os deploys saudáveis" if not events else f"⚠️ {len(events)} evento(s)"
    return (f"<b>Sentinel · Deploy</b> — {time.strftime('%H:%M UTC', time.gmtime())}\n"
            f"Repos checados: {checked}\n"
            f"{footer}")


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
    current = {}
    for r in repos:
        dep = _fetch_latest_deployment(r["full_name"], tok)
        if dep:
            current[r["name"]] = dep

    state = load_state(STATE_PATH)
    if state is None:
        save_state(STATE_PATH, {"last": current})
        print(f"Estado inicial: {len(current)} repos com deploy registrado.")
        try:
            send_telegram(build_report(len(repos), []))
        except Exception:
            pass
        return 0

    events = compute_events(state, current)
    for ev in events:
        try:
            send_telegram(format_event(ev))
        except Exception as e:
            print(f"  envio falhou ({ev['repo']}): {e}", file=sys.stderr)

    save_state(STATE_PATH, {"last": current})

    try:
        send_telegram(build_report(len(repos), events))
    except Exception:
        pass

    print(f"Deploy: {len(repos)} repos · {len(current)} com deploy · {len(events)} evento(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
