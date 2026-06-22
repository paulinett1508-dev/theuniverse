#!/usr/bin/env python3
"""Auditoria de segredos hardcoded (subsistema do Sentinel).

Complementa o `secret_exposto` nativo (GitHub secret-scanning) com varredura de
CONTEÚDO por regex: pega segredos custom (senhas, tokens não-provider) que o
scanner nativo ignora — inclusive em repos privados sem Advanced Security.

Roda diário via Actions. Reusa gh.py (token/list_repos) e o canal Telegram do
Sentinel (send_telegram). Estado+dedup em state/secret-scan-state.json — guarda só
HASHES dos achados, nunca o segredo. Modo `--local DIR...` para CLI/teste offline.
Só stdlib.
"""
import io
import os
import re
import sys
import html
import json
import hashlib
import tarfile
import subprocess
import urllib.request
from pathlib import Path

from gh import ROOT, API, token, list_repos
from sentinel import send_telegram

STATE_PATH = ROOT / "state" / "secret-scan-state.json"
_GH = "https://github.com/paulinett1508-dev"
NOTIFY_CAP = 25          # teto de notificações por run (evita flood)
MAX_FILE_BYTES = 800_000

# (rótulo, regex). Mira segredos REAIS — não placeholders/fixtures.
PATTERNS = [
    ("Telegram bot token", re.compile(r"[0-9]{8,10}:[A-Za-z0-9_-]{35}")),
    ("age private key", re.compile(r"AGE-SECRET-KEY-1[0-9A-Z]+")),
    ("Private key block", re.compile(r"BEGIN[ A-Z]*PRIVATE KEY")),
    ("GitHub PAT", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,}")),
    ("Groq/OpenAI key", re.compile(r"\b(?:gsk|sk)_[A-Za-z0-9]{20,}")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    # valor DEVE ser literal entre aspas (corta declarações de tipo, schemas, destructuring)
    ("Senha/secret hardcoded", re.compile(
        r"(?i)(senha|password|webpassword|passwd|pwd|rtsp_pass|admin_password)"
        r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{5,})[\"']")),
]
IGNORE = re.compile(
    r"(?i)revogar|example|placeholder|xxxx|<[a-z]|your[_-]|changeme|dummy|fake|redact|"
    r"senha123|\bmock\b|\bsample\b")

# valores que são placeholder/exemplo, não segredo real
_PLACEHOLDER_WORD = re.compile(
    r"^(senha|password|passwd|pwd|string|secret|token|qualquer|null|none|true|false|"
    r"errada|errado|wrong|incorret\w*|teste?|123\d*|abc\d*)$", re.I)


def _is_placeholder(v):
    if _PLACEHOLDER_WORD.match(v):
        return True
    if re.match(r"^[A-Z][A-Z0-9_]{3,}$", v):          # ALL_CAPS_PLACEHOLDER
        return True
    if re.search(r"[<>${}]|\.\w+\(", v):              # template/interpolação/chamada
        return True
    if re.match(r"(?i)^(sua|seu|minha|exemplo|example|teste|placeholder|changeme|your|x{3,})", v):
        return True
    return False
SKIP_PATH = re.compile(r"(/|^)(\.git|node_modules|dist|build|vendor|__tests__|tests?)(/|$)|"
                       r"\.(test|spec)\.|/fixtures?/")
SKIP_EXT = re.compile(r"\.(png|jpe?g|gif|svg|pdf|zip|gz|tgz|ico|woff2?|ttf|eot|"
                      r"lock|min\.js|map|mp4|mp3|bin)$", re.I)


def redact(s):
    """Mascara o miolo de trechos longos — mantém localização legível, esconde o segredo."""
    return re.sub(r"([A-Za-z0-9@#]{2,3})[A-Za-z0-9@#:+/._-]{4,}([A-Za-z0-9]{2})", r"\1***\2", s)


def _key(repo, path, secret):
    return hashlib.sha256(f"{repo}|{path}|{secret}".encode()).hexdigest()[:16]


def scan_text(repo, path, text):
    """Núcleo testável: devolve achados de UM arquivo (sem o valor cru do segredo)."""
    if SKIP_PATH.search(path) or SKIP_EXT.search(path):
        return []
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if len(line) > 600 or IGNORE.search(line):
            continue
        for label, rx in PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            secret = m.group(2) if (m.lastindex or 0) >= 2 else m.group(0)
            if (m.lastindex or 0) >= 2 and _is_placeholder(secret):
                continue
            out.append({
                "repo": repo, "path": path, "line": lineno, "label": label,
                "redacted": redact(line.strip()[:120]),
                "key": _key(repo, path, secret),
            })
            break  # um achado por linha basta
    return out


def _is_textual(data):
    if b"\x00" in data[:4096]:
        return False
    return True


def scan_local(dirs):
    findings = []
    for d in dirs:
        d = Path(d)
        if not d.is_dir():
            print(f"skip (não é dir): {d}", file=sys.stderr)
            continue
        repo = d.name
        try:
            files = subprocess.run(["git", "-C", str(d), "ls-files"],
                                   capture_output=True, text=True, timeout=60).stdout.splitlines()
        except Exception:
            files = []
        if not files:
            files = [str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()]
        for rel in files:
            full = d / rel
            try:
                if not full.is_file() or full.stat().st_size > MAX_FILE_BYTES:
                    continue
                data = full.read_bytes()
                if not _is_textual(data):
                    continue
                findings += scan_text(repo, rel.replace("\\", "/"), data.decode("utf-8", "ignore"))
            except Exception:
                continue
    return findings


def _fetch_bytes(url, tok):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {tok}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "theuniverse-secret-scan"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def scan_remote(tok):
    findings = []
    for r in list_repos(tok):
        full_name, repo = r["full_name"], r["name"]
        try:
            blob = _fetch_bytes(f"{API}/repos/{full_name}/tarball", tok)
            tar = tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")
        except Exception as e:
            print(f"  tarball falhou em {full_name}: {e}", file=sys.stderr)
            continue
        for member in tar.getmembers():
            if not member.isfile() or member.size > MAX_FILE_BYTES:
                continue
            # nome vem como "<repo>-<sha>/caminho" — tira o 1º componente
            path = member.name.split("/", 1)[1] if "/" in member.name else member.name
            try:
                data = tar.extractfile(member).read()
                if not _is_textual(data):
                    continue
                findings += scan_text(repo, path, data.decode("utf-8", "ignore"))
            except Exception:
                continue
        tar.close()
    return findings


def format_finding(f):
    url = f"{_GH}/{f['repo']}/blob/HEAD/{f['path']}#L{f['line']}"
    return (
        f"🔑 <b>{html.escape(f['repo'])}</b> · segredo hardcoded\n"
        f"\n"
        f"tipo: <code>{html.escape(f['label'])}</code>\n"
        f"<code>{html.escape(f['path'])}:{f['line']}</code>\n"
        f"<code>{html.escape(f['redacted'])}</code>\n"
        f"\n"
        f'<a href="{url}">↗ ver linha</a>'
    )


def load_state(path):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_local(dirs):
    findings = scan_local(dirs)
    by_repo = {}
    for f in findings:
        by_repo.setdefault(f["repo"], []).append(f)
    for repo in sorted(by_repo):
        print(f"\n✗ {repo} — {len(by_repo[repo])} achado(s)")
        for f in by_repo[repo]:
            print(f"  [{f['label']}] {f['path']}:{f['line']}\n      {f['redacted']}")
    print(f"\n----- TOTAL: {len(findings)}")
    return 1 if findings else 0


def run_remote():
    tok = token()
    findings = scan_remote(tok)
    by_key = {f["key"]: f for f in findings}   # dedup intra-run
    state = load_state(STATE_PATH)
    seen = set(state["seen"]) if state else set()
    first_run = state is None

    fresh = [f for k, f in by_key.items() if k not in seen]
    if not fresh:
        print("Nenhum segredo novo.")
        save_state(STATE_PATH, {"seen": sorted(seen | set(by_key))})
        return 0

    sent = 0
    for f in fresh[:NOTIFY_CAP]:
        try:
            send_telegram(format_finding(f))
            sent += 1
        except Exception as e:
            print(f"  envio falhou ({f['repo']} {f['path']}): {e}", file=sys.stderr)
    if len(fresh) > NOTIFY_CAP:
        try:
            send_telegram(f"🔑 <b>+{len(fresh) - NOTIFY_CAP}</b> outros segredos hardcoded "
                          f"detectados (teto de {NOTIFY_CAP}/run). Rode a auditoria completa.")
        except Exception:
            pass

    save_state(STATE_PATH, {"seen": sorted(seen | set(by_key))})
    tag = " (1ª varredura)" if first_run else ""
    print(f"Segredos: {len(by_key)} no total, {len(fresh)} novos, {sent} notificados{tag}.")
    return 0


def main(argv):
    if "--local" in argv:
        i = argv.index("--local")
        dirs = argv[i + 1:]
        if not dirs:
            sys.exit("uso: secret_scan.py --local DIR [DIR...]")
        return run_local(dirs)
    return run_remote()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
