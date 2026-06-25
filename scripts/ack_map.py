"""ACK map — persiste {telegram_message_id: github_issue_url} via GitHub API.

Artoo escreve (save_entry) ao criar issues.
Obi-Wan lê (load) ao processar reactions ✅ e fecha issues (close_issue).
"""
import base64
import json
import re
import urllib.request

OWNER = "paulinett1508-dev"
REPO = "theuniverse"
_FILE_PATH = "state/ack-map.json"
_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{_FILE_PATH}"


def _headers(gh_token: str) -> dict:
    return {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "theuniverse-ack",
    }


def _read_file(gh_token: str) -> tuple:
    req = urllib.request.Request(_API_URL, headers=_headers(gh_token))
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
        content = base64.b64decode(data["content"]).decode("utf-8")
        entries = json.loads(content).get("entries", {})
        return entries, data.get("sha")


def load(gh_token: str) -> dict:
    """Retorna {str(message_id): issue_url}. Empty dict em caso de erro."""
    try:
        entries, _ = _read_file(gh_token)
        return entries
    except Exception:
        return {}


def save_entry(message_id: int, issue_url: str, gh_token: str) -> None:
    """Adiciona ou atualiza entrada no ack-map via GitHub API."""
    try:
        entries, sha = _read_file(gh_token)
    except Exception:
        entries, sha = {}, None

    entries[str(message_id)] = issue_url
    encoded = base64.b64encode(
        json.dumps({"entries": entries}, indent=2, ensure_ascii=False).encode()
    ).decode()

    payload: dict = {
        "message": f"chore: ack-map +msg{message_id}",
        "content": encoded,
        "committer": {"name": "artoo[bot]", "email": "artoo@theuniverse"},
    }
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(
        _API_URL, data=json.dumps(payload).encode(),
        method="PUT", headers=_headers(gh_token),
    )
    with urllib.request.urlopen(req, timeout=30):
        pass


def close_issue(issue_url: str, gh_token: str) -> bool:
    """Fecha uma GitHub issue via PATCH. Retorna True se sucesso."""
    m = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', issue_url)
    if not m:
        return False
    owner, repo, number = m.group(1), m.group(2), m.group(3)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    req = urllib.request.Request(
        url, data=json.dumps({"state": "closed"}).encode(),
        method="PATCH", headers=_headers(gh_token),
    )
    with urllib.request.urlopen(req, timeout=30):
        return True
