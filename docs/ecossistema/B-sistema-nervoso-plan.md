# Sistema Nervoso (Subsistema B) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> ✅ **Onde executar:** **no próprio theuniverse** (casa do Guardião). Diferente do A, este plano roda aqui — sem detour pelo nexus.
>
> Spec de origem: [`B-sistema-nervoso-spec.md`](B-sistema-nervoso-spec.md). Depende de A só pelo bot (token + chat_id), que o Sol gera no deploy.

**Goal:** Workflow no theuniverse que poda a API do GitHub a cada 15 min, detecta eventos de sinal alto (planeta novo/sumido, CI falhou, issue nova) e empurra pro Telegram do Sol, reusando o bot do Hermes.

**Architecture:** Um `scripts/gh.py` centraliza o cliente GitHub (extraído do `censo.py`). `scripts/sentinel.py` lê o estado commitado, monta um snapshot via API, calcula deltas com funções puras, e notifica entrega-antes-de-avançar (só persiste o estado de um evento após o `sendMessage` dar certo). Um workflow Actions agenda tudo e commita o estado.

**Tech Stack:** Python 3.12 (stdlib only — `urllib`, `json`, `pathlib`), GitHub Actions, API do Telegram (`sendMessage`).

## Global Constraints

- **Sem dependências externas:** só stdlib do Python (o `censo.py` já é assim — `urllib.request`, sem `requests`). Não adicionar `requirements`.
- **Escreve só em casa:** o único `git push` é do `state/sentinel-state.json` no theuniverse. Zero toque em planeta.
- **Segredos via Actions:** `UNIVERSE_PAT` (= token do Censo), `TELEGRAM_TOKEN`, `SOL_CHAT_ID`. Nunca no código.
- **DRY:** `token()`, `api()`, `list_repos()` vivem só em `gh.py`; Censo e Sentinel importam de lá.
- **Eventos do MVP:** 🆕 novo planeta, 💥 sumido, 🔴 CI falhou, 🚨 issue nova. Nada além (YAGNI).
- **Baseline silencioso:** sem estado prévio, semeia tudo sem notificar.
- **Entrega antes de avançar:** estado de um evento só avança após `sendMessage` 200 OK.
- **Idioma:** mensagens em português.
- **Python:** 3.12 (igual ao Censo no workflow).

---

## File Structure

| arquivo | responsabilidade |
|---|---|
| `scripts/gh.py` | Cliente GitHub compartilhado: `token()`, `api()`, `list_repos()` + constantes `API`, `ROOT`, `SELF` |
| `scripts/censo.py` (modificar) | Passa a importar de `gh.py`; remove as cópias locais. Comportamento inalterado |
| `scripts/sentinel.py` | Estado (load/save/seed) + detecção pura (`compute_events`/`apply_event`/`format_event`) + `notify` + `main` |
| `.github/workflows/sentinel.yml` | Cron `*/15` + `workflow_dispatch`; roda o sentinel e commita o estado |
| `tests/test_gh.py` | Testes de `gh.py` (token via env, list_repos com `_api` injetado) |
| `tests/test_sentinel.py` | Testes das funções puras do sentinel |
| `state/sentinel-state.json` | Criado em runtime (1º run). **Não** versionar manualmente — o workflow commita |

As funções de detecção são puras (recebem `state` + `snapshot`, devolvem eventos/estado). Todo I/O (API, Telegram, disco) fica em `main()` e em `send_telegram()`, finos de propósito. `notify()` recebe a função de envio injetada — por isso a regra "entrega antes de avançar" é testável sem rede.

---

### Task 1: Cliente GitHub compartilhado (`gh.py`) + refactor do Censo

**Files:**
- Create: `scripts/gh.py`
- Modify: `scripts/censo.py`
- Test: `tests/test_gh.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `API = "https://api.github.com"`, `ROOT = Path` (raiz do repo), `SELF = "theuniverse"`
  - `token() -> str` — lê `GITHUB_TOKEN` do env, senão do `.vault`; `sys.exit` se ausente.
  - `api(path: str, tok: str) -> tuple[object, http.client.HTTPMessage]` — GET autenticado; `path` absoluto ou relativo a `API`.
  - `list_repos(tok: str, _api=None) -> list[dict]` — todos os repos `owner`, paginados, exceto `SELF`. `_api` injetável (default = `api`) pra teste.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gh.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import gh


def test_token_prefers_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "  tok-123  ")
    assert gh.token() == "tok-123"


def test_list_repos_paginates_and_excludes_self():
    pages = {
        1: [{"name": "alpha"}, {"name": "theuniverse"}],
        2: [{"name": "beta"}],
        3: [],
    }
    calls = []

    def fake_api(path, tok):
        page = int(path.split("page=")[1].split("&")[0])
        calls.append(page)
        return pages[page], {}

    repos = gh.list_repos("tok", _api=fake_api)
    names = [r["name"] for r in repos]
    assert names == ["alpha", "beta"]   # theuniverse excluído
    assert calls == [1, 2, 3]           # parou na página vazia
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_gh.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gh'`

- [ ] **Step 3: Criar `scripts/gh.py`**

```python
# scripts/gh.py
"""Cliente GitHub compartilhado — usado pelo Censo e pelo Sentinel.

Só stdlib. Token via env GITHUB_TOKEN ou .vault (local).
"""
import os
import sys
import json
import urllib.request
from pathlib import Path

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
SELF = "theuniverse"  # o observatório não é planeta


def token():
    t = os.getenv("GITHUB_TOKEN")
    if t:
        return t.strip()
    vault = ROOT / ".vault"
    if vault.exists():
        for line in vault.read_text(encoding="utf-8").splitlines():
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip()
    sys.exit("ERRO: GITHUB_TOKEN ausente (env ou .vault).")


def api(path, tok):
    req = urllib.request.Request(
        path if path.startswith("http") else API + path,
        headers={"Authorization": f"token {tok}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "theuniverse-censo"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()), r.headers


def list_repos(tok, _api=None):
    _api = _api or api
    repos, page = [], 1
    while True:
        batch, _ = _api(f"/user/repos?per_page=100&page={page}&affiliation=owner", tok)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [r for r in repos if r["name"] != SELF]
```

- [ ] **Step 4: Refatorar `scripts/censo.py` pra usar `gh.py`**

Substituir, no topo de `censo.py`, o bloco de imports + constantes + as funções `token`, `api`, `list_repos`. Trocar:

```python
import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
PLANETS = ROOT / "planets"
CHANGELOG = ROOT / "CHANGELOG.md"
SELF = "theuniverse"  # o observatório não é planeta
```

por:

```python
import sys
import base64
import argparse
from datetime import datetime, timezone

from gh import API, ROOT, SELF, token, api, list_repos

PLANETS = ROOT / "planets"
CHANGELOG = ROOT / "CHANGELOG.md"
```

e **remover** de `censo.py` as definições das funções `token()`, `api(path, tok)` e `list_repos(tok)` (agora vêm de `gh.py`). O resto de `censo.py` permanece igual.

- [ ] **Step 5: Run test + smoke do Censo**

Run: `python -m pytest tests/test_gh.py -v && python scripts/censo.py --dry-run`
Expected: testes PASS (2 passed); Censo imprime `Censo: 31 planetas | 🆕 0 novos | 💥 0 sumidos` e `(dry-run: nada escrito)` — prova que o refactor não quebrou nada.

- [ ] **Step 6: Commit**

```bash
git add scripts/gh.py scripts/censo.py tests/test_gh.py
git commit -m "refactor: extrai cliente GitHub para gh.py (DRY censo+sentinel)"
```

---

### Task 2: Estado do Sentinel (load / save / seed)

**Files:**
- Create: `scripts/sentinel.py`
- Test: `tests/test_sentinel.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - Estrutura do estado: `{"known_repos": list[str], "last_run_id": dict[str,int], "last_issue_number": dict[str,int]}`
  - Estrutura do snapshot: `{"repos": list[str], "latest_run": dict[str, {"id": int, "conclusion": str} | None], "issues": dict[str, list[{"number": int, "title": str}]]}`
  - `load_state(path: Path) -> dict | None` — `None` se o arquivo não existe.
  - `save_state(path: Path, state: dict) -> None` — escreve JSON indentado.
  - `seed_state(snapshot: dict) -> dict` — estado-baseline a partir do snapshot (todos os repos conhecidos, último run e maior issue por repo; sem eventos).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sentinel.py
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import sentinel


def test_load_state_missing_returns_none(tmp_path):
    assert sentinel.load_state(tmp_path / "nope.json") is None


def test_save_and_load_roundtrip(tmp_path):
    p = tmp_path / "state.json"
    state = {"known_repos": ["a"], "last_run_id": {"a": 7}, "last_issue_number": {"a": 3}}
    sentinel.save_state(p, state)
    assert sentinel.load_state(p) == state


def test_seed_state_from_snapshot():
    snapshot = {
        "repos": ["alpha", "beta"],
        "latest_run": {"alpha": {"id": 100, "conclusion": "success"}, "beta": None},
        "issues": {"alpha": [{"number": 5, "title": "x"}, {"number": 2, "title": "y"}], "beta": []},
    }
    state = sentinel.seed_state(snapshot)
    assert state["known_repos"] == ["alpha", "beta"]
    assert state["last_run_id"] == {"alpha": 100}      # beta sem run → ausente
    assert state["last_issue_number"] == {"alpha": 5}  # maior número; beta sem issue → ausente
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sentinel.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sentinel'`

- [ ] **Step 3: Criar `scripts/sentinel.py` com o bloco de estado**

```python
# scripts/sentinel.py
"""Sistema Nervoso (subsistema B): poll da API → eventos → Telegram.

Roda no theuniverse via GitHub Actions. Só observação (leitura). O único
git push é do próprio estado. Reusa o cliente de gh.py.
"""
import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

from gh import ROOT, token, api, list_repos

STATE_PATH = ROOT / "state" / "sentinel-state.json"


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
    return {
        "known_repos": list(snapshot["repos"]),
        "last_run_id": last_run_id,
        "last_issue_number": last_issue,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sentinel.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/sentinel.py tests/test_sentinel.py
git commit -m "feat(sentinel): estado load/save/seed"
```

---

### Task 3: Detecção de eventos (funções puras)

**Files:**
- Modify: `scripts/sentinel.py`
- Test: `tests/test_sentinel.py`

**Interfaces:**
- Consumes: estado + snapshot (Task 2).
- Produces:
  - Estrutura do evento: `{"kind": str, "repo": str, ...}` onde `kind ∈ {"novo_planeta","planeta_sumido","ci_falhou","issue_nova"}`. `ci_falhou` carrega `run_id` + `detail`; `issue_nova` carrega `number` + `detail`.
  - `compute_events(state: dict, snapshot: dict) -> list[dict]` — deltas entre estado e snapshot. CI/issue só para repos já em `known_repos` (baseline); repos novos só geram `novo_planeta` (sua história é silenciada no `apply_event`).
  - `apply_event(state: dict, event: dict, snapshot: dict) -> dict` — devolve **novo** estado com o efeito do evento aplicado (chamado só após envio OK).
  - `format_event(event: dict) -> str` — texto da mensagem Telegram.

- [ ] **Step 1: Write the failing test**

```python
# (append em tests/test_sentinel.py)

def _snapshot(repos, latest_run=None, issues=None):
    return {
        "repos": repos,
        "latest_run": latest_run or {r: None for r in repos},
        "issues": issues or {r: [] for r in repos},
    }


def test_compute_events_novo_e_sumido():
    state = {"known_repos": ["alpha"], "last_run_id": {}, "last_issue_number": {}}
    snap = _snapshot(["alpha", "beta"])
    events = sentinel.compute_events(state, snap)
    kinds = {(e["kind"], e["repo"]) for e in events}
    assert ("novo_planeta", "beta") in kinds
    snap2 = _snapshot(["beta"])
    events2 = sentinel.compute_events(state, snap2)
    assert ("planeta_sumido", "alpha") in {(e["kind"], e["repo"]) for e in events2}


def test_compute_events_ci_falhou_so_em_novo_run():
    state = {"known_repos": ["alpha"], "last_run_id": {"alpha": 10}, "last_issue_number": {}}
    snap_fail = _snapshot(["alpha"], latest_run={"alpha": {"id": 11, "conclusion": "failure"}})
    assert any(e["kind"] == "ci_falhou" and e["run_id"] == 11
               for e in sentinel.compute_events(state, snap_fail))
    # mesmo run id já visto → não dispara
    state_seen = {"known_repos": ["alpha"], "last_run_id": {"alpha": 11}, "last_issue_number": {}}
    assert not any(e["kind"] == "ci_falhou" for e in sentinel.compute_events(state_seen, snap_fail))
    # run novo mas com sucesso → não dispara
    snap_ok = _snapshot(["alpha"], latest_run={"alpha": {"id": 12, "conclusion": "success"}})
    assert not any(e["kind"] == "ci_falhou" for e in sentinel.compute_events(state, snap_ok))


def test_compute_events_issue_nova_acima_do_baseline():
    state = {"known_repos": ["alpha"], "last_run_id": {}, "last_issue_number": {"alpha": 4}}
    snap = _snapshot(["alpha"], issues={"alpha": [{"number": 5, "title": "bug"}, {"number": 3, "title": "velha"}]})
    events = sentinel.compute_events(state, snap)
    nums = [e["number"] for e in events if e["kind"] == "issue_nova"]
    assert nums == [5]  # só a 5 (> baseline 4); a 3 ignorada


def test_apply_event_novo_planeta_silencia_historico():
    state = {"known_repos": [], "last_run_id": {}, "last_issue_number": {}}
    snap = _snapshot(["beta"], latest_run={"beta": {"id": 9, "conclusion": "failure"}},
                     issues={"beta": [{"number": 2, "title": "x"}]})
    ev = {"kind": "novo_planeta", "repo": "beta"}
    new = sentinel.apply_event(state, ev, snap)
    assert "beta" in new["known_repos"]
    assert new["last_run_id"]["beta"] == 9      # baseline silencioso
    assert new["last_issue_number"]["beta"] == 2


def test_apply_event_ci_e_issue_avancam_estado():
    state = {"known_repos": ["alpha"], "last_run_id": {"alpha": 10}, "last_issue_number": {"alpha": 4}}
    snap = _snapshot(["alpha"])
    s1 = sentinel.apply_event(state, {"kind": "ci_falhou", "repo": "alpha", "run_id": 11, "detail": "CI"}, snap)
    assert s1["last_run_id"]["alpha"] == 11
    s2 = sentinel.apply_event(s1, {"kind": "issue_nova", "repo": "alpha", "number": 6, "detail": "bug"}, snap)
    assert s2["last_issue_number"]["alpha"] == 6


def test_apply_event_planeta_sumido_remove():
    state = {"known_repos": ["alpha", "beta"], "last_run_id": {}, "last_issue_number": {}}
    new = sentinel.apply_event(state, {"kind": "planeta_sumido", "repo": "beta"}, _snapshot(["alpha"]))
    assert new["known_repos"] == ["alpha"]


def test_format_event_has_emoji_and_repo():
    txt = sentinel.format_event({"kind": "ci_falhou", "repo": "alpha", "run_id": 1, "detail": "build"})
    assert "🔴" in txt and "alpha" in txt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sentinel.py -v`
Expected: FAIL — `AttributeError: module 'sentinel' has no attribute 'compute_events'`

- [ ] **Step 3: Implementar detecção em `sentinel.py`**

Adicionar a `sentinel.py` (após `seed_state`):

```python
import copy

_EMOJI = {
    "novo_planeta": "🆕",
    "planeta_sumido": "💥",
    "ci_falhou": "🔴",
    "issue_nova": "🚨",
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
    return s


def format_event(event):
    emoji = _EMOJI[event["kind"]]
    repo = event["repo"]
    if event["kind"] == "novo_planeta":
        return f"{emoji} Novo planeta detectado: *{repo}*"
    if event["kind"] == "planeta_sumido":
        return f"{emoji} Planeta sumiu do GitHub: *{repo}*"
    if event["kind"] == "ci_falhou":
        return f"{emoji} CI falhou em *{repo}* (run {event['run_id']})"
    if event["kind"] == "issue_nova":
        return f"{emoji} Issue nova em *{repo}* #{event['number']}: {event['detail']}"
    return f"Evento em {repo}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sentinel.py -v`
Expected: PASS (10 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/sentinel.py tests/test_sentinel.py
git commit -m "feat(sentinel): deteccao de eventos (puro) + formatacao"
```

---

### Task 4: Notificação (entrega antes de avançar) + orquestração

**Files:**
- Modify: `scripts/sentinel.py`
- Test: `tests/test_sentinel.py`

**Interfaces:**
- Consumes: `compute_events`, `apply_event`, `format_event` (Task 3); `seed_state`/`load_state`/`save_state` (Task 2); `token`/`list_repos`/`api` (Task 1).
- Produces:
  - `notify(events: list, state: dict, snapshot: dict, send_fn) -> tuple[dict, int]` — para cada evento: `send_fn(format_event(e))`; só em sucesso aplica `apply_event`. Devolve `(novo_estado, qtd_enviados)`. Falha de envio não avança o estado daquele evento.
  - `send_telegram(text: str) -> None` — `sendMessage` real; levanta em status != 200.
  - `build_snapshot(tok: str) -> dict` — monta o snapshot via API.
  - `main() -> int` — entrypoint.

- [ ] **Step 1: Write the failing test**

```python
# (append em tests/test_sentinel.py)

def test_notify_avanca_so_em_envio_ok():
    state = {"known_repos": ["alpha"], "last_run_id": {"alpha": 10}, "last_issue_number": {}}
    snap = _snapshot(["alpha"])
    events = [
        {"kind": "ci_falhou", "repo": "alpha", "run_id": 11, "detail": "x"},
        {"kind": "issue_nova", "repo": "alpha", "number": 5, "detail": "y"},
    ]
    sent = []

    def send_fn(text):
        sent.append(text)
        if "Issue" in text:
            raise RuntimeError("telegram caiu")

    new_state, count = sentinel.notify(events, state, snap, send_fn)
    assert count == 1                                   # só o CI foi
    assert new_state["last_run_id"]["alpha"] == 11      # CI avançou
    assert "alpha" not in new_state["last_issue_number"]  # issue NÃO avançou → re-tenta
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sentinel.py::test_notify_avanca_so_em_envio_ok -v`
Expected: FAIL — `AttributeError: module 'sentinel' has no attribute 'notify'`

- [ ] **Step 3: Implementar `notify`, `send_telegram`, `build_snapshot`, `main`**

Adicionar a `sentinel.py`:

```python
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
        "chat_id": chat_id, "text": text, "parse_mode": "Markdown",
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
    latest_run, issues = {}, {}
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
    return {"repos": repos, "latest_run": latest_run, "issues": issues}


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sentinel.py -v`
Expected: PASS (11 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/sentinel.py tests/test_sentinel.py
git commit -m "feat(sentinel): notify entrega-antes-de-avancar + main"
```

---

### Task 5: Workflow Actions + `.gitignore` do estado em dev

**Files:**
- Create: `.github/workflows/sentinel.yml`
- Modify: `.gitignore` (garantir que o estado seja versionado pelo workflow, não ignorado)

**Interfaces:**
- Consumes: `scripts/sentinel.py` (Task 4).
- Produces: workflow agendado que roda o sentinel e commita `state/sentinel-state.json`.

> Sem ciclo de teste unitário — é configuração. Validação: `workflow_dispatch` manual após cadastrar os 3 secrets.

- [ ] **Step 1: Criar o workflow**

```yaml
# .github/workflows/sentinel.yml
name: Sentinel — Sistema Nervoso

on:
  schedule:
    - cron: "*/15 * * * *"   # a cada 15 min
  workflow_dispatch:

permissions:
  contents: write

# evita runs concorrentes pisando no estado
concurrency:
  group: sentinel
  cancel-in-progress: false

jobs:
  sentinel:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Rodar Sentinel
        env:
          GITHUB_TOKEN: ${{ secrets.UNIVERSE_PAT }}
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          SOL_CHAT_ID: ${{ secrets.SOL_CHAT_ID }}
        run: python scripts/sentinel.py

      - name: Commitar estado (se mudou)
        run: |
          git config user.name  "guardiao-do-universo"
          git config user.email "guardiao@theuniverse.local"
          if [ -n "$(git status --porcelain state/)" ]; then
            git add state/sentinel-state.json
            git commit -m "sentinel: atualiza estado do sistema nervoso"
            git push
          else
            echo "Estado inalterado."
          fi
```

- [ ] **Step 2: Garantir que `state/` não seja ignorado**

Verificar o `.gitignore` do repo. Se houver alguma regra que pegue `state/` ou `*.json`, adicionar exceção:

```
!state/sentinel-state.json
```

Se não houver regra que afete `state/`, nenhuma mudança é necessária (registrar isso no commit msg).

- [ ] **Step 3: Validar a sintaxe YAML**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/sentinel.yml')); print('YAML ok')"`
Expected: `YAML ok` (se `pyyaml` não estiver instalado: `pip install pyyaml` ou validar via push e aba Actions)

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/sentinel.yml .gitignore
git commit -m "feat(sentinel): workflow Actions (cron 15min) do sistema nervoso"
```

---

## Pré-requisitos do Sol antes de ativar — `[PENDENTE SOL]`

Cadastrar 3 secrets em **Settings → Secrets and variables → Actions**:

1. **`UNIVERSE_PAT`** — token do `.vault` (mesmo do Censo; provavelmente já cadastrado).
2. **`TELEGRAM_TOKEN`** — do BotFather (mesmo bot do A). *Sol gera.*
3. **`SOL_CHAT_ID`** — chat_id do Sol. *Sol gera.*

## Validação fim-a-fim (após secrets)

1. Disparar `workflow_dispatch` na aba Actions → 1ª run cria `state/sentinel-state.json` e **não** envia nada (baseline silencioso). Confirmar o commit do estado.
2. Abrir uma issue de teste em qualquer planeta → próxima run (≤15 min ou dispatch manual) manda 🚨 no Telegram.
3. Fechar/arquivar a issue de teste.
4. Conferir os logs da run (`Eventos: N detectados, N notificados`).

---

## Self-Review

**Cobertura do spec:**
- Fonte = só API, zero toque em planeta → Task 4 `build_snapshot` (só GET) ✓
- Roda no theuniverse (Actions) → Task 5 ✓
- 4 eventos de sinal alto → Task 3 `compute_events` ✓
- `gh.py` DRY entre Censo e Sentinel → Task 1 ✓
- `sentinel-state.json` commitado → Task 5 ✓
- Baseline silencioso no 1º run → Task 4 `main` (state is None → seed, return) ✓
- Entrega antes de avançar → Task 4 `notify` (+ teste dedicado) ✓
- Isolamento de falha por repo → Task 4 `build_snapshot` (try/except por repo) ✓
- Secrets `UNIVERSE_PAT`/`TELEGRAM_TOKEN`/`SOL_CHAT_ID` → Task 5 + pré-requisitos ✓
- Só stdlib → todo o código usa `urllib`/`json`/`pathlib` ✓
- YAGNI (sem webhook/runtime/digest) → respeitado ✓

**Consistência de tipos:** estado `{known_repos, last_run_id, last_issue_number}` idêntico em seed/compute/apply/notify. Snapshot `{repos, latest_run, issues}` idêntico em build/seed/compute/apply. Evento com `kind`/`repo` + `run_id`/`number` consumido igual em `apply_event`/`format_event`. `notify` devolve `(dict, int)` e `main` desempacota `new_state, sent`.

**Placeholders:** nenhum. `[PENDENTE SOL]` são credenciais externas (fronteira correta), com a nota explícita de que o Sol gera os dois tokens do bot.
