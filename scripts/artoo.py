#!/usr/bin/env python3
"""
Artoo — Mensageiro Cósmico do Observatório.

Quando o Observatório detecta uma ameaça num planeta, Artoo atravessa a
órbita e entrega um alerta diretamente no mundo deles (GitHub Issue).
O mundo deles não sabe da ameaça — até Artoo chegar.

TheGod é notificado em dois momentos:
  🛸 lançamento — "Artoo em rota para X"
  ✅ entrega confirmada — "Artoo chegou · issue #N aberta"
  ❌ perdido — "Artoo perdido na órbita · erro: ..."

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

from gh import API, token

OWNER = "paulinett1508-dev"
OBSERVATORY_LABEL = "observatory-alert"
OBSERVATORY_LABEL_COLOR = "b60205"
DASHBOARD_URL = "https://theuniverse-lake.vercel.app"
_GH = f"https://github.com/{OWNER}"


def _tg_send(text):
    tg_token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["SOL_CHAT_ID"]
    payload = urllib.parse.urlencode({
        "chat_id": chat_id, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tg_token}/sendMessage",
        data=payload, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status != 200:
            raise RuntimeError(f"Telegram HTTP {r.status}")


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

    if notify:
        try:
            _tg_send(
                f"🛸 <b>Artoo</b> em rota\n\n"
                f"destino: <b>{repo}</b>\n"
                f"ameaça: {reason}"
                + (f"\ndetalhe: <i>{detail}</i>" if detail else "")
            )
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

        if notify:
            try:
                _tg_send(
                    f"✅ <b>Artoo chegou</b>\n\n"
                    f"<b>{repo}</b> · issue #{issue_number} aberta\n"
                    f"o mundo deles foi alertado\n\n"
                    f'<a href="{issue_url}">↗ ver issue</a>'
                )
            except Exception as e:
                print(f"  Telegram (delivered) falhou: {e}", file=sys.stderr)

        print(f"✅ {repo} alertado — #{issue_number}: {issue_url}")
        return {"issue_url": issue_url, "issue_number": issue_number}

    except Exception as e:
        err = str(e)
        if notify:
            try:
                _tg_send(
                    f"❌ <b>Artoo perdido na órbita</b>\n\n"
                    f"destino: <b>{repo}</b>\n"
                    f"erro: <code>{err[:200]}</code>"
                )
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
