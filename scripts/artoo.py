#!/usr/bin/env python3
"""
Artoo — Mensageiro Cósmico do Observatório.

Quando o Observatório detecta uma ameaça num planeta, Artoo atravessa a
órbita e entrega um alerta diretamente no mundo deles (GitHub Issue).
O mundo deles não sabe da ameaça — até Artoo chegar.

Personalidade evolui com missões acumuladas (state/artoo-state.json):
  novice (0-9) · journeyman (10-49) · veteran (50+)

Uso manual:
  python scripts/artoo.py sbrgestao --reason "CI falhou" --detail "agnvendas-unit-tests"

Integrado ao sentinel.py para disparo automático em ci_falhou.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from artoo_voice import format_rota, format_chegou, format_perdido
from gh import API, ROOT

def token():
    """Prefere ARTOO_TOKEN (master PAT com repo scope). Fallback: GITHUB_TOKEN."""
    import os
    t = os.getenv("ARTOO_TOKEN") or os.getenv("GITHUB_TOKEN")
    if t:
        return t.strip()
    vault = ROOT / ".vault"
    if vault.exists():
        for line in vault.read_text(encoding="utf-8").splitlines():
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip()
    import sys
    sys.exit("ERRO: ARTOO_TOKEN ou GITHUB_TOKEN ausente.")

OWNER = "paulinett1508-dev"
OBSERVATORY_LABEL = "observatory-alert"
OBSERVATORY_LABEL_COLOR = "b60205"
DASHBOARD_URL = "https://theuniverse-lake.vercel.app"
_GH = f"https://github.com/{OWNER}"
_STATE_FILE = ROOT / "state" / "artoo-state.json"
_HISTORY_MAX = 20


def _load_state():
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"missions": 0, "history": []}


def _save_state(state):
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _tg_send(text) -> int | None:
    from sentinel import TOPICS
    tg_token = os.environ.get("TELEGRAM_TOKEN_ARTOO") or os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["SOL_CHAT_ID"]
    payload = urllib.parse.urlencode({
        "chat_id": chat_id, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": "true",
        "message_thread_id": str(TOPICS["alertas"]),
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tg_token}/sendMessage",
        data=payload, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise RuntimeError(f"Telegram HTTP {r.status}")
        resp = json.loads(r.read())
        return (resp.get("result") or {}).get("message_id")


def _gh_request(method, path, tok, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        path if path.startswith("http") else API + path,
        data=data, method=method,
        headers={
            "Authorization": f"token {tok}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "theuniverse-voyager",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _ensure_label(full_name, tok):
    try:
        _gh_request("GET", f"/repos/{full_name}/labels/{OBSERVATORY_LABEL}", tok)
        return
    except Exception:
        pass
    try:
        _gh_request("POST", f"/repos/{full_name}/labels", tok, {
            "name": OBSERVATORY_LABEL,
            "color": OBSERVATORY_LABEL_COLOR,
            "description": "Alerta emitido pelo Observatório Cósmico (theuniverse)",
        })
    except Exception:
        pass  # issue será criada sem label se falhar


def _issue_body(repo, reason, detail, today):
    detail_row = f"\n| **Detalhe** | {detail} |" if detail else ""
    run_link = ""
    if reason.lower().startswith("ci") and detail:
        run_link = f'\n\n🔗 <a href="{_GH}/{repo}/actions">Ver Actions de {repo}</a>'
    return (
        f"## ⚠️ Alerta do Observatório Cósmico\n\n"
        f"O Observatório detectou uma ameaça neste planeta.\n\n"
        f"| campo | valor |\n"
        f"|---|---|\n"
        f"| **Ameaça** | {reason} |\n"
        f"| **Detectado** | {today} |"
        f"{detail_row}\n\n"
        f"---\n\n"
        f"Quando a ameaça for resolvida, feche esta issue — é o sinal de que o planeta está saudável.\n\n"
        f"> 🔭 Enviado automaticamente por [theuniverse]({DASHBOARD_URL})"
    )


def dispatch(repo, reason, detail="", tok=None, notify=True):
    """
    Despacha Artoo para um planeta.

    Returns:
        dict {'issue_url', 'issue_number'} em caso de sucesso, None se falhou.
    """
    tok = tok or token()
    full_name = f"{OWNER}/{repo}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    state = _load_state()
    mc = state.get("missions", 0)

    if notify:
        try:
            _tg_send(format_rota(repo, reason, detail=detail, mission_count=mc))
        except Exception as e:
            print(f"  Telegram (launch) falhou: {e}", file=sys.stderr)

    try:
        _ensure_label(full_name, tok)
        issue = _gh_request("POST", f"/repos/{full_name}/issues", tok, {
            "title": f"🔴 Alerta do Observatório — {reason}",
            "body": _issue_body(repo, reason, detail, today),
            "labels": [OBSERVATORY_LABEL],
        })
        issue_url = issue["html_url"]
        issue_number = issue["number"]

        state["missions"] = mc + 1
        history = state.get("history") or []
        history.append({"repo": repo, "reason": reason, "issue": issue_number, "date": today})
        state["history"] = history[-_HISTORY_MAX:]
        _save_state(state)

        if notify:
            try:
                msg_id = _tg_send(format_chegou(repo, issue_number, issue_url, mission_count=mc))
                if msg_id:
                    try:
                        from ack_map import save_entry
                        save_entry(msg_id, issue_url, tok)
                    except Exception as e:
                        print(f"  ack-map save falhou: {e}", file=sys.stderr)
            except Exception as e:
                print(f"  Telegram (delivered) falhou: {e}", file=sys.stderr)

        print(f"✅ {repo} alertado — #{issue_number}: {issue_url}")
        return {"issue_url": issue_url, "issue_number": issue_number}

    except Exception as e:
        err = str(e)
        if notify:
            try:
                _tg_send(format_perdido(repo, err, mission_count=mc))
            except Exception:
                pass
        print(f"❌ Falha ao alertar {repo}: {err}", file=sys.stderr)
        return None


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Artoo — Mensageiro Cósmico do Observatório")
    ap.add_argument("repo", help="Repo destino (ex: sbrgestao)")
    ap.add_argument("--reason", required=True, help="Tipo de ameaça (ex: 'CI falhou')")
    ap.add_argument("--detail", default="", help="Detalhe adicional (ex: nome do workflow)")
    ap.add_argument("--no-notify", action="store_true", help="Não envia Telegram")
    args = ap.parse_args()

    result = dispatch(args.repo, args.reason, args.detail, notify=not args.no_notify)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
