#!/usr/bin/env python3
"""Model Scout — varre modelos disponíveis no Groq e atualiza state/model-state.json.

Cron semanal. Notifica Telegram se houver novidades (novos modelos ou trocas de tier).
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_router import _classify_groq_model, _score_model, DEFAULT_STATE
from sentinel import send_telegram, TOPICS

_STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "model-state.json"
_GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
_TOPIC = TOPICS["heartbeat"]

# Modelos a ignorar (deprecated, preview instável, vision-only)
_EXCLUDE_PATTERNS = ["whisper", "guard", "tool-use-preview"]


def _fetch_models(api_key: str) -> list:
    req = urllib.request.Request(
        _GROQ_MODELS_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode()).get("data", [])


def _filter(models: list) -> list:
    out = []
    for m in models:
        mid = m.get("id", "")
        if any(p in mid for p in _EXCLUDE_PATTERNS):
            continue
        out.append({
            "id": mid,
            "context_window": m.get("context_window", 8192),
            "tier": _classify_groq_model(mid),
        })
    return out


def _best_per_tier(models: list) -> dict:
    tiers: dict = {}
    for m in models:
        tier = m["tier"]
        if tier not in tiers or _score_model(m) > _score_model(tiers[tier]):
            tiers[tier] = m
    return {tier: m["id"] for tier, m in tiers.items()}


def _load_prev() -> dict:
    try:
        if _STATE_FILE.exists():
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return DEFAULT_STATE


def _detect_changes(prev: dict, new_tiers: dict, new_models: list) -> list:
    events = []
    prev_tiers = prev.get("tiers", {})
    prev_ids = {m["id"] for m in prev.get("models", [])}
    new_ids = {m["id"] for m in new_models}

    for m in new_models:
        if m["id"] not in prev_ids:
            events.append(f"🆕 novo modelo: <code>{m['id']}</code> [{m['tier']}]")

    for tier, model_id in new_tiers.items():
        if prev_tiers.get(tier) != model_id:
            events.append(
                f"🔄 tier <b>{tier}</b>: "
                f"<code>{prev_tiers.get(tier, '—')}</code> → <code>{model_id}</code>"
            )

    for mid in prev_ids - new_ids:
        events.append(f"🗑 removido: <code>{mid}</code>")

    return events


def run(api_key: str | None = None) -> dict:
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        sys.exit("GROQ_API_KEY ausente")

    raw = _fetch_models(api_key)
    models = _filter(raw)
    tiers = _best_per_tier(models)
    prev = _load_prev()
    changes = _detect_changes(prev, tiers, models)

    state = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tiers": tiers,
        "models": sorted(models, key=lambda m: m["id"]),
    }

    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    brt = datetime.now(timezone.utc) - timedelta(hours=3)
    ts = brt.strftime("%d/%m · %H:%M BRT")
    header = f"🔭 <b>Model Scout · theuniverse</b>\n{ts}"

    if changes:
        send_telegram(f"{header}\n\n" + "\n".join(changes), thread_id=_TOPIC)
    else:
        tier_lines = "\n".join(
            f"   └ <b>{tier}</b>: <code>{mid}</code>"
            for tier, mid in sorted(tiers.items())
        )
        send_telegram(
            f"{header} · {len(models)} modelos\n\n✅ sem mudanças\n\n{tier_lines}",
            thread_id=_TOPIC,
        )

    return state


if __name__ == "__main__":
    state = run()
    print(json.dumps(state, indent=2, ensure_ascii=False))
