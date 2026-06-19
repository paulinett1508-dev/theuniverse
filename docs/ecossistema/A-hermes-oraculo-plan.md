> ⚠️ **OBSOLETO (2026-06-19).** Este plano implementava o design v1 (RAG-puro Ollama+Qdrant no nexus-labsobral). O spec foi reescrito pra v2 (agente/receita-SHELDON: Groq+BM25, código no theuniverse, runtime na Polaris) — ver `A-hermes-oraculo-spec.md`. Um novo plano será escrito. Mantido só como histórico.

# Hermes-Oráculo Implementation Plan (v1 — OBSOLETO)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> ⚠️ **Onde executar:** este plano é executado **dentro do repo `nexus-labsobral`** (casa do código, `hermes/bot/`). O Guardião do theuniverse **não** executa — só escreveu o plano. Quem implementar trabalha no `nexus-labsobral`.
>
> Spec de origem: [`A-hermes-oraculo-spec.md`](A-hermes-oraculo-spec.md). Blueprint: [`00-blueprint.md`](00-blueprint.md).

**Goal:** Bot Telegram conversacional (long-polling) que deixa o Sol perguntar em linguagem natural e responde consultando o RAG local (Ollama + Qdrant) na estrela Polaris.

**Architecture:** Loop de long-polling em `bot.py` recebe mensagens; um *guard* descarta tudo que não vem do `chat_id` do Sol; a pergunta autorizada vai pro `rag.py` (embed via Ollama → busca no Qdrant `lab_knowledge` → chat via Ollama) e a resposta + fontes voltam pro Telegram. Reusa a lógica de embed/busca já existente em `hermes/mcp/rag_server.py`. Tudo roda dentro da Polaris — sem porta nova exposta.

**Tech Stack:** Python 3, python-telegram-bot 21.x, qdrant-client 1.9.1, requests 2.32.3, Ollama (`nomic-embed-text` para embed + modelo de chat a confirmar), Qdrant, systemd.

## Global Constraints

- **Casa do código:** `nexus-labsobral/hermes/bot/` — todos os arquivos novos vivem aqui, exceto modificações marcadas em `hermes/ingestor/ingest.py` e `hermes/deploy.sh`.
- **Coleção Qdrant:** `lab_knowledge` (mesma do ingestor/MCP existente). **Não** criar coleção nova.
- **Modelo de embed:** `nomic-embed-text` via `POST {OLLAMA_URL}/api/embeddings`, campo de resposta `embedding`. Valor verbatim do código existente.
- **Parâmetros de busca:** `limit=5`, `score_threshold=0.75`, `with_payload=True`. Payload tem chaves `source` e `text`.
- **Segurança:** guard de `chat_id` único **antes** de qualquer processamento. `TELEGRAM_TOKEN` só em `/opt/hermes-bot/.env` (chmod 600). **Nunca** commitar segredo. Sem webhook (long-polling).
- **Versões fixas:** `qdrant-client==1.9.1`, `requests==2.32.3`, `python-telegram-bot==21.6`.
- **Idioma:** respostas e prompts do bot em português.
- **YAGNI (fora do MVP):** push, comandos slash, multi-usuário, histórico persistente, streaming.

---

## File Structure

| arquivo | responsabilidade |
|---|---|
| `hermes/bot/config.py` | Carrega e valida env (`TELEGRAM_TOKEN`, `SOL_CHAT_ID`, `OLLAMA_URL`, `QDRANT_URL`, `CHAT_MODEL`) |
| `hermes/bot/rag.py` | Cliente RAG puro: `embed` → `search` → `build_prompt` → `answer` |
| `hermes/bot/bot.py` | Loop Telegram (long-polling), guard de `chat_id`, formatação de resposta, wiring |
| `hermes/bot/requirements.txt` | Dependências do bot |
| `hermes/bot/tests/test_config.py` | Testes de carga/validação de env |
| `hermes/bot/tests/test_rag.py` | Testes do cliente RAG (Ollama/Qdrant mockados) |
| `hermes/bot/tests/test_bot.py` | Testes das funções puras do bot (guard, formatação) |
| `hermes/systemd/hermes-bot.service` | Unit systemd long-running, restart on-failure |
| `hermes/ingestor/ingest.py` (modificar) | `--source-dir` repetível, aceita dir **ou** arquivo (2ª fonte: theuniverse) |
| `hermes/ingestor/tests/test_ingest.py` | Testes dos helpers `collect_files` / `compute_source` |
| `hermes/deploy.sh` (modificar) | Bloco de deploy do bot + espelhamento do theuniverse |

`config.py`, `rag.py` e as funções puras de `bot.py` são desenhados pra serem testáveis sem rede (dependências injetadas). O loop PTB em `main()` é o único trecho não testado por unidade — fino de propósito.

---

### Task 1: Config — carga e validação de env

**Files:**
- Create: `hermes/bot/config.py`
- Test: `hermes/bot/tests/test_config.py`

**Interfaces:**
- Consumes: nada.
- Produces: `class Config(env: dict | None = None)` com atributos `telegram_token: str`, `sol_chat_id: int`, `ollama_url: str`, `qdrant_url: str`, `chat_model: str`. Levanta `ValueError` se `TELEGRAM_TOKEN` ou `SOL_CHAT_ID` ausentes.

- [ ] **Step 1: Write the failing test**

```python
# hermes/bot/tests/test_config.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from config import Config


def test_config_requires_telegram_token():
    with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
        Config(env={"SOL_CHAT_ID": "123"})


def test_config_requires_sol_chat_id():
    with pytest.raises(ValueError, match="SOL_CHAT_ID"):
        Config(env={"TELEGRAM_TOKEN": "abc"})


def test_config_parses_and_defaults():
    cfg = Config(env={"TELEGRAM_TOKEN": "abc", "SOL_CHAT_ID": "42"})
    assert cfg.telegram_token == "abc"
    assert cfg.sol_chat_id == 42
    assert cfg.ollama_url == "http://localhost:11434"
    assert cfg.qdrant_url == "http://localhost:6333"
    assert cfg.chat_model == "qwen2.5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes/bot && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Write minimal implementation**

```python
# hermes/bot/config.py
"""Carrega e valida configuração do Hermes-Oráculo a partir do ambiente."""
import os


class Config:
    def __init__(self, env=None):
        env = env if env is not None else os.environ
        self.telegram_token = self._require(env, "TELEGRAM_TOKEN")
        self.sol_chat_id = int(self._require(env, "SOL_CHAT_ID"))
        self.ollama_url = env.get("OLLAMA_URL", "http://localhost:11434")
        self.qdrant_url = env.get("QDRANT_URL", "http://localhost:6333")
        self.chat_model = env.get("CHAT_MODEL", "qwen2.5")

    @staticmethod
    def _require(env, key):
        val = env.get(key)
        if not val:
            raise ValueError(f"Variável de ambiente obrigatória ausente: {key}")
        return val
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes/bot && python -m pytest tests/test_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add hermes/bot/config.py hermes/bot/tests/test_config.py
git commit -m "feat(hermes-bot): config loader com validação de env"
```

---

### Task 2: RAG client — embed → search → chat

**Files:**
- Create: `hermes/bot/rag.py`
- Test: `hermes/bot/tests/test_rag.py`

**Interfaces:**
- Consumes: nada do plano (usa `qdrant_client.QdrantClient` e `requests`, ambos injetáveis).
- Produces:
  - `class Rag(ollama_url: str, qdrant_url: str, chat_model: str, qdrant=None, http=requests)`
  - `Rag.embed(text: str) -> list[float]`
  - `Rag.search(vector: list[float]) -> list` (hits do Qdrant, cada um com `.payload` dict e `.score`)
  - `Rag.build_prompt(context: str, question: str) -> str`
  - `Rag.answer(question: str) -> tuple[str, list[str]]` → `(texto_resposta, fontes_ordenadas)`. Sem hits, retorna mensagem de "não encontrei" e `[]`.
  - Constantes módulo: `COLLECTION="lab_knowledge"`, `EMBED_MODEL="nomic-embed-text"`, `TOP_K=5`, `SCORE_THRESHOLD=0.75`.

- [ ] **Step 1: Write the failing test**

```python
# hermes/bot/tests/test_rag.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag import Rag


class FakeResp:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self):
        pass
    def json(self):
        return self._payload


class FakeHit:
    def __init__(self, text, source, score=0.9):
        self.payload = {"text": text, "source": source}
        self.score = score


class FakeHttp:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
    def post(self, url, json, timeout):
        self.calls.append({"url": url, "json": json})
        return self.responses.pop(0)


class FakeQdrant:
    def __init__(self, hits):
        self.hits = hits
        self.search_kwargs = None
    def search(self, **kwargs):
        self.search_kwargs = kwargs
        return self.hits


def test_answer_no_results_returns_fallback():
    http = FakeHttp([FakeResp({"embedding": [0.1, 0.2]})])
    rag = Rag("http://o", "http://q", "m", qdrant=FakeQdrant([]), http=http)
    text, sources = rag.answer("qualquer coisa")
    assert "não encontrei" in text.lower()
    assert sources == []


def test_answer_with_context_calls_chat_and_returns_sources():
    http = FakeHttp([
        FakeResp({"embedding": [0.1, 0.2]}),                 # /api/embeddings
        FakeResp({"message": {"content": "Resposta do Oráculo"}}),  # /api/chat
    ])
    hits = [
        FakeHit("texto sobre zion", "planets/zion.md"),
        FakeHit("texto do changelog", "CHANGELOG.md"),
    ]
    qdrant = FakeQdrant(hits)
    rag = Rag("http://o", "http://q", "m", qdrant=qdrant, http=http)

    text, sources = rag.answer("o que é zion?")

    assert text == "Resposta do Oráculo"
    assert sources == ["CHANGELOG.md", "planets/zion.md"]  # ordenado e deduplicado
    # busca usou os parâmetros corretos
    assert qdrant.search_kwargs["collection_name"] == "lab_knowledge"
    assert qdrant.search_kwargs["limit"] == 5
    assert qdrant.search_kwargs["score_threshold"] == 0.75
    # contexto recuperado entrou no prompt de chat
    chat_payload = http.calls[1]["json"]
    user_msg = chat_payload["messages"][1]["content"]
    assert "texto sobre zion" in user_msg
    assert chat_payload["model"] == "m"
    assert chat_payload["stream"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes/bot && python -m pytest tests/test_rag.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rag'`

- [ ] **Step 3: Write minimal implementation**

```python
# hermes/bot/rag.py
"""Cliente RAG do Hermes-Oráculo: embed → busca Qdrant → chat Ollama.

Reusa o padrão de embed/busca de hermes/mcp/rag_server.py, adicionando
a etapa generativa (/api/chat) que o MCP não tinha.
"""
import requests
from qdrant_client import QdrantClient

COLLECTION = "lab_knowledge"
EMBED_MODEL = "nomic-embed-text"
TOP_K = 5
SCORE_THRESHOLD = 0.75

SYSTEM_PROMPT = (
    "Você é o Oráculo do Laboratório Sobral. Responda em português, de forma "
    "direta e técnica, usando SOMENTE o contexto fornecido. Se o contexto não "
    "contém a resposta, diga que não sabe — não invente."
)

NO_RESULTS = "Não encontrei nada na base de conhecimento sobre isso."


class Rag:
    def __init__(self, ollama_url, qdrant_url, chat_model, qdrant=None, http=requests):
        self.ollama_url = ollama_url
        self.chat_model = chat_model
        self.qdrant = qdrant if qdrant is not None else QdrantClient(url=qdrant_url)
        self.http = http

    def embed(self, text):
        resp = self.http.post(
            f"{self.ollama_url}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    def search(self, vector):
        return self.qdrant.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=TOP_K,
            score_threshold=SCORE_THRESHOLD,
            with_payload=True,
        )

    def build_prompt(self, context, question):
        return f"Contexto:\n{context}\n\nPergunta: {question}"

    def answer(self, question):
        vector = self.embed(question)
        results = self.search(vector)
        if not results:
            return NO_RESULTS, []
        context = "\n\n---\n\n".join(r.payload.get("text", "") for r in results)
        sources = sorted({r.payload.get("source", "desconhecido") for r in results})
        resp = self.http.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": self.chat_model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": self.build_prompt(context, question)},
                ],
            },
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["message"]["content"].strip()
        return text, sources
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes/bot && python -m pytest tests/test_rag.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add hermes/bot/rag.py hermes/bot/tests/test_rag.py
git commit -m "feat(hermes-bot): cliente RAG embed+busca+chat"
```

---

### Task 3: Bot — guard, formatação e wiring do long-polling

**Files:**
- Create: `hermes/bot/bot.py`
- Test: `hermes/bot/tests/test_bot.py`

**Interfaces:**
- Consumes: `Config` (Task 1), `Rag` (Task 2) — em especial `Rag.answer(question) -> (str, list[str])`.
- Produces:
  - `is_authorized(chat_id: int, sol_chat_id: int) -> bool`
  - `format_reply(text: str, sources: list[str]) -> str`
  - `build_application(cfg: Config, rag: Rag) -> telegram.ext.Application`
  - `main()` — entrypoint, chamado pelo systemd.

- [ ] **Step 1: Write the failing test**

```python
# hermes/bot/tests/test_bot.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot import is_authorized, format_reply


def test_is_authorized_matches_sol():
    assert is_authorized(42, 42) is True


def test_is_authorized_rejects_others():
    assert is_authorized(99, 42) is False


def test_format_reply_appends_sources():
    out = format_reply("a resposta", ["planets/zion.md", "CHANGELOG.md"])
    assert "a resposta" in out
    assert "planets/zion.md" in out
    assert "CHANGELOG.md" in out
    assert "Fontes" in out


def test_format_reply_without_sources_is_plain():
    assert format_reply("só a resposta", []) == "só a resposta"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes/bot && python -m pytest tests/test_bot.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bot'` (ou `telegram`, se a dep ainda não instalada — instalar via requirements antes; ver Task 4)

- [ ] **Step 3: Write minimal implementation**

```python
# hermes/bot/bot.py
"""Hermes-Oráculo — bot Telegram conversacional (long-polling).

Guard de chat_id único: só o Sol é atendido; o resto é ignorado em silêncio.
"""
import logging

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from config import Config
from rag import Rag

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s — %(message)s", level=logging.INFO
)
log = logging.getLogger("hermes-bot")


def is_authorized(chat_id, sol_chat_id):
    return chat_id == sol_chat_id


def format_reply(text, sources):
    if not sources:
        return text
    fontes = "\n".join(f"• {s}" for s in sources)
    return f"{text}\n\n📚 Fontes:\n{fontes}"


def build_application(cfg, rag):
    app = Application.builder().token(cfg.telegram_token).build()

    async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not is_authorized(chat_id, cfg.sol_chat_id):
            log.warning("Ignorado chat_id não autorizado: %s", chat_id)
            return
        question = update.message.text
        log.info("Pergunta do Sol: %s", question)
        try:
            text, sources = rag.answer(question)
        except Exception:
            log.exception("Falha ao consultar o RAG")
            await update.message.reply_text("Falhei ao consultar o Oráculo. Tenta de novo.")
            return
        await update.message.reply_text(format_reply(text, sources))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    return app


def main():
    cfg = Config()
    rag = Rag(cfg.ollama_url, cfg.qdrant_url, cfg.chat_model)
    app = build_application(cfg, rag)
    log.info("Hermes-Oráculo online. Long-polling iniciado.")
    app.run_polling()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes/bot && python -m pytest tests/test_bot.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add hermes/bot/bot.py hermes/bot/tests/test_bot.py
git commit -m "feat(hermes-bot): loop Telegram com guard de chat_id"
```

---

### Task 4: Dependências e unit systemd do bot

**Files:**
- Create: `hermes/bot/requirements.txt`
- Create: `hermes/systemd/hermes-bot.service`

**Interfaces:**
- Consumes: `bot.py:main()` (Task 3).
- Produces: ambiente instalável e unit `hermes-bot.service` que roda `bot.py` lendo `/opt/hermes-bot/.env`.

> Sem ciclo de teste automatizado próprio — é configuração/scaffolding. Validação acontece no deploy (Task 6). Esta task instala as deps que as Tasks 1-3 precisam pra rodar localmente: se rodar os testes antes, faça `pip install -r hermes/bot/requirements.txt` primeiro.

- [ ] **Step 1: Criar `requirements.txt`**

```
# hermes/bot/requirements.txt
python-telegram-bot==21.6
qdrant-client==1.9.1
requests==2.32.3
```

- [ ] **Step 2: Criar a unit systemd**

```ini
# hermes/systemd/hermes-bot.service
[Unit]
Description=Hermes-Oráculo — bot Telegram conversacional
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hermes-bot
EnvironmentFile=/opt/hermes-bot/.env
ExecStart=/opt/hermes-bot/venv/bin/python /opt/hermes-bot/bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-bot

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: Verificar a sintaxe da unit (sem subir)**

Run: `systemd-analyze verify hermes/systemd/hermes-bot.service` (se disponível na máquina de dev; senão, validação ocorre na Polaris no deploy)
Expected: sem erros de sintaxe. (Aviso sobre `EnvironmentFile` inexistente é esperado fora da Polaris — ignorar.)

- [ ] **Step 4: Commit**

```bash
git add hermes/bot/requirements.txt hermes/systemd/hermes-bot.service
git commit -m "feat(hermes-bot): requirements + unit systemd"
```

---

### Task 5: Ingestor — segunda fonte (theuniverse), multi `--source-dir`

**Files:**
- Modify: `hermes/ingestor/ingest.py`
- Test: `hermes/ingestor/tests/test_ingest.py`

**Interfaces:**
- Consumes: nada novo.
- Produces:
  - `collect_files(source: str) -> list[Path]` — se `source` é arquivo, retorna `[Path(source)]` (quando extensão suportada); se é diretório, retorna os arquivos com extensão em `{.md,.txt,.pdf,.docx}` (rglob).
  - `compute_source(path: Path, base: Path) -> str` — caminho relativo de `path` em relação a `base`, como string.
  - `main()` aceita `--source-dir` repetível (dir **ou** arquivo); default mantém comportamento atual (`docs/` do repo). `ingest_file(path, source_dir, force)` continua existindo, agora usando `compute_source` internamente.

> Backward-compatible: com um único `--source-dir` apontando pra um diretório, o comportamento é idêntico ao atual (a unit `hermes-ingest.service` existente continua funcionando).

- [ ] **Step 1: Write the failing test**

```python
# hermes/ingestor/tests/test_ingest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest import collect_files, compute_source


def test_compute_source_relative(tmp_path):
    base = tmp_path
    f = base / "planets" / "zion.md"
    f.parent.mkdir(parents=True)
    f.write_text("x", encoding="utf-8")
    assert compute_source(f, base) == str(Path("planets/zion.md"))


def test_collect_files_directory(tmp_path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("y", encoding="utf-8")
    (tmp_path / "ignore.png").write_text("z", encoding="utf-8")
    got = sorted(p.name for p in collect_files(str(tmp_path)))
    assert got == ["a.md", "b.txt"]


def test_collect_files_single_file(tmp_path):
    f = tmp_path / "CHANGELOG.md"
    f.write_text("x", encoding="utf-8")
    got = collect_files(str(f))
    assert got == [f]


def test_collect_files_single_file_unsupported_ext(tmp_path):
    f = tmp_path / "image.png"
    f.write_text("x", encoding="utf-8")
    assert collect_files(str(f)) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes/ingestor && python -m pytest tests/test_ingest.py -v`
Expected: FAIL — `ImportError: cannot import name 'collect_files'`

- [ ] **Step 3: Implementar os helpers e religar o `main`**

Adicionar perto do topo de `ingest.py` (após as constantes), a constante de extensões e os dois helpers:

```python
EXTS = {".md", ".txt", ".pdf", ".docx"}


def compute_source(path: Path, base: Path) -> str:
    return str(path.relative_to(base))


def collect_files(source: str) -> list:
    p = Path(source)
    if p.is_file():
        return [p] if p.suffix.lower() in EXTS else []
    return [f for f in p.rglob("*") if f.suffix.lower() in EXTS and f.is_file()]
```

Trocar, dentro de `ingest_file`, a linha:

```python
    source = str(path.relative_to(source_dir))
```

por:

```python
    source = compute_source(path, source_dir)
```

Substituir o corpo de `main()` (da definição do `parser` até o fim) por:

```python
def main():
    parser = argparse.ArgumentParser(description="Ingestor RAG — docs/ → Qdrant")
    parser.add_argument("--force", action="store_true", help="Re-ingerir mesmo sem mudanças")
    parser.add_argument(
        "--source-dir",
        action="append",
        dest="sources",
        help="Diretório OU arquivo a indexar. Repetível. Default: docs/ do repo.",
    )
    args = parser.parse_args()

    default_dir = str(Path(__file__).parent.parent.parent / "docs")
    sources = args.sources or [default_dir]

    total = 0
    for src in sources:
        src_path = Path(src)
        if not src_path.exists():
            print(f"ERRO: source-dir não existe: {src}", file=sys.stderr)
            continue
        base = src_path if src_path.is_dir() else src_path.parent
        files = collect_files(src)
        print(f"Ingestão: {len(files)} arquivos em {src}")
        for f in sorted(files):
            try:
                total += ingest_file(f, base, force=args.force)
            except Exception as e:
                print(f"  ERRO em {f}: {e}", file=sys.stderr)

    info = qdrant.get_collection(COLLECTION)
    print(f"\nConcluído: {total} chunks novos. Total na coleção: {info.points_count}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes/ingestor && python -m pytest tests/test_ingest.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Atualizar a unit do ingestor pra incluir o theuniverse**

Modify: `hermes/systemd/hermes-ingest.service` — trocar a linha `ExecStart=` por (continuação com `\` é válida em systemd):

```ini
ExecStart=/opt/hermes-ingestor/venv/bin/python /opt/hermes-ingestor/ingest.py \
  --source-dir /opt/nexus-labsobral/docs \
  --source-dir /opt/theuniverse/planets \
  --source-dir /opt/theuniverse/docs/ecossistema \
  --source-dir /opt/theuniverse/CHANGELOG.md
```

- [ ] **Step 6: Commit**

```bash
git add hermes/ingestor/ingest.py hermes/ingestor/tests/test_ingest.py hermes/systemd/hermes-ingest.service
git commit -m "feat(hermes-ingest): multi-source — indexa fichas do theuniverse"
```

---

### Task 6: Deploy — espelhar theuniverse + subir o bot

**Files:**
- Modify: `hermes/deploy.sh`

**Interfaces:**
- Consumes: arquivos do bot (Tasks 1-4), ingestor atualizado (Task 5).
- Produces: bloco de deploy que (a) espelha o theuniverse em `/opt/theuniverse` na Polaris, (b) faz scp do bot pra `/opt/hermes-bot`, cria venv, e habilita `hermes-bot.service`.

> Sem ciclo de teste automatizado — é script de deploy, validado pela execução real contra a Polaris. Pré-requisitos `[PENDENTE SOL]` listados ao fim.

- [ ] **Step 1: Adicionar o espelhamento do theuniverse**

No `hermes/deploy.sh`, **antes** do `echo "=== Done ==="`, inserir:

```bash
echo "=== Mirroring theuniverse (fichas dos planetas) ==="
# [PENDENTE SOL] requer deploy token de leitura do repo privado theuniverse,
# gravado em /root/.git-credentials da Polaris (chmod 600), OU chave de deploy SSH.
ssh $SSH_OPTS "$ORACULO" "
  if [ -d /opt/theuniverse/.git ]; then
    cd /opt/theuniverse && git pull --ff-only
  else
    git clone https://github.com/paulinett1508-dev/theuniverse.git /opt/theuniverse
  fi
"
```

- [ ] **Step 2: Adicionar o bloco de deploy do bot**

Logo após o bloco do MCP server (antes do bloco `=== Deploying systemd units ===`), inserir:

```bash
echo "=== Deploying bot (Hermes-Oráculo) ==="
ssh $SSH_OPTS "$ORACULO" "mkdir -p /opt/hermes-bot"
scp $SCP_OPTS \
  "$REPO_ROOT/hermes/bot/bot.py" \
  "$REPO_ROOT/hermes/bot/rag.py" \
  "$REPO_ROOT/hermes/bot/config.py" \
  "$REPO_ROOT/hermes/bot/requirements.txt" \
  "$ORACULO:/opt/hermes-bot/"
```

- [ ] **Step 3: Incluir a unit do bot no scp de systemd**

Na lista de `scp` do bloco `=== Deploying systemd units ===`, adicionar a linha do bot:

```bash
scp $SCP_OPTS \
  "$REPO_ROOT/hermes/systemd/hermes-ingest.service" \
  "$REPO_ROOT/hermes/systemd/hermes-ingest.timer" \
  "$REPO_ROOT/hermes/systemd/hermes-bot.service" \
  "$ORACULO:/etc/systemd/system/"
```

- [ ] **Step 4: Instalar venv do bot e habilitar o serviço**

No bloco final `=== Installing dependencies & reloading systemd ===`, adicionar dentro do heredoc do `ssh`, após o `cd /opt/hermes-mcp ...`:

```bash
  cd /opt/hermes-bot && python3 -m venv venv && venv/bin/pip install -q -r requirements.txt
```

e após `systemctl start hermes-ingest.timer`:

```bash
  if [ -f /opt/hermes-bot/.env ]; then
    systemctl enable hermes-bot.service
    systemctl restart hermes-bot.service
    echo 'Bot status:'
    systemctl status hermes-bot.service --no-pager | head -10
  else
    echo 'AVISO: /opt/hermes-bot/.env ausente — bot NÃO iniciado. Criar .env (ver abaixo) e rodar: systemctl enable --now hermes-bot.service'
  fi
```

- [ ] **Step 5: Commit**

```bash
git add hermes/deploy.sh
git commit -m "feat(hermes): deploy do bot + espelhamento do theuniverse"
```

---

## Pré-requisitos do Sol antes do deploy (Task 6) — `[PENDENTE SOL]`

Criar `/opt/hermes-bot/.env` na Polaris (chmod 600, **nunca** no git):

```
TELEGRAM_TOKEN=<token do BotFather>
SOL_CHAT_ID=<chat_id do Sol>
OLLAMA_URL=http://localhost:11434
QDRANT_URL=http://localhost:6333
CHAT_MODEL=<modelo de chat instalado no Ollama>
```

1. **Token do BotFather** — criar o bot no Telegram, copiar o token.
2. **`SOL_CHAT_ID`** — descobrir mandando `/start` pro bot e lendo o log (`journalctl -u hermes-bot`, aparece o `chat_id não autorizado`), ou via `@userinfobot`.
3. **SSH a Polaris** — confirmar que a chave `~/.ssh/id_ed25519_nexus_vps01` existe na máquina que roda o deploy (deploy.sh usa porta `49222`, `root@2.25.163.125`).
4. **Modelo de chat no Ollama** — confirmar se há um instalado (`ollama list`). Se não, `ollama pull qwen2.5` (ou `llama3.1`) e ajustar `CHAT_MODEL`.
5. **Deploy token do theuniverse** — repo privado: gravar credencial de leitura em `/root/.git-credentials` na Polaris (ou usar deploy key SSH) pra o `git clone/pull` do mirror funcionar.

## Validação fim-a-fim (após deploy)

1. `journalctl -u hermes-bot -f` → ver "Hermes-Oráculo online".
2. Mandar pergunta de outro Telegram (não-Sol) → bot ignora; log mostra "Ignorado chat_id não autorizado".
3. Mandar pergunta do Sol sobre algo do Lab (ex.: um procedimento conhecido) → resposta com seção "📚 Fontes".
4. Mandar pergunta sobre o universo (ex.: "o que é a estrela Polaris?") → resposta citando ficha do theuniverse, confirmando a 2ª fonte de ingestão.
5. `journalctl -u hermes-ingest` após o timer das 3h (ou rodar manual) → confirmar ingestão das fontes do theuniverse.

## Dívida de segurança (registrar p/ subsistema C — Guardião da Galáxia)

`hermes-dashboard.service` roda `--insecure --host 0.0.0.0 --port 9119` — porta administrativa aberta sem TLS na Polaris. Fora do escopo deste plano; auditar no subsistema C.

---

## Self-Review

**Cobertura do spec:**
- Canal conversacional two-way → Tasks 1-3 ✓
- Allowlist de 1 `chat_id`, resto em silêncio → `is_authorized` (Task 3) ✓
- Conhecimento Universo + Lab → Task 5 (multi-source) ✓
- Casa do código `nexus-labsobral/hermes/bot/` → File Structure ✓
- Componentes `bot.py`/`rag.py`/`config.py`/`requirements.txt`/systemd → Tasks 1-4 ✓
- Arquitetura embed→search→chat, top-5/0.75/lab_knowledge → Task 2 ✓
- Long-polling, sem porta nova → Task 3 (`run_polling`) ✓
- Token em `.env` chmod 600, nunca no git → Task 4 + pré-requisitos ✓
- Ingestor ganha 2ª fonte no timer das 3h → Task 5 ✓
- Deploy estende `deploy.sh` → Task 6 ✓
- Credenciais do Sol → seção `[PENDENTE SOL]` ✓
- Dívida do dashboard → registrada ✓
- YAGNI (sem push/slash/multi-user/histórico/streaming) → respeitado ✓

**Consistência de tipos:** `Rag.answer -> (str, list[str])` consumido por `bot.on_message` e formatado por `format_reply(text, sources)` ✓. `Config.sol_chat_id: int` comparado com `update.effective_chat.id` (int) em `is_authorized` ✓.

**Placeholders:** nenhum "TODO/TBD" no código; todo trecho de código está completo. Os `[PENDENTE SOL]` são credenciais externas (decisão correta de fronteira), não buracos de implementação.
