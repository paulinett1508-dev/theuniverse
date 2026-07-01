import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from model_router import classify_query, select_model, route, DEFAULT_STATE


def test_classify_short_is_fast():
    assert classify_query("o que é o sbrgestao?") == "fast"


def test_classify_long_is_balanced():
    q = "analisa a arquitetura do ecossistema e explica como os sentinelas se integram com o Artoo e o Obi-Wan em detalhes"
    assert classify_query(q) == "balanced"


def test_classify_complex_keywords_is_balanced():
    for kw in ["explica", "analisa", "compara", "arquitetura", "detalha"]:
        assert classify_query(f"{kw} o universo") == "balanced"


def test_classify_medium_is_balanced():
    q = "como funciona o sistema de webhooks e qual o fluxo completo?"
    assert classify_query(q) == "balanced"


def test_select_model_returns_from_state():
    state = {
        "tiers": {"fast": "llama-fast", "balanced": "llama-big"},
    }
    assert select_model("fast", state) == "llama-fast"
    assert select_model("balanced", state) == "llama-big"


def test_select_model_fallback_to_balanced():
    state = {"tiers": {"balanced": "llama-big"}}
    assert select_model("fast", state) == "llama-big"


def test_select_model_fallback_to_hardcoded():
    assert select_model("fast", {}) == "openai/gpt-oss-120b"


def test_route_returns_string():
    result = route("status do sbrgestao?")
    assert isinstance(result, str)
    assert len(result) > 0


def test_route_uses_default_state_when_no_file():
    result = route("o que é o universo?", state=DEFAULT_STATE)
    assert isinstance(result, str)


def test_default_state_has_tiers():
    assert "tiers" in DEFAULT_STATE
    assert "balanced" in DEFAULT_STATE["tiers"]
    assert "fast" in DEFAULT_STATE["tiers"]


def test_parse_groq_response_extracts_tiers():
    from model_router import _classify_groq_model, _score_model
    # modelos grandes devem ir para balanced
    assert _classify_groq_model("llama-3.3-70b-versatile") == "balanced"
    # modelos pequenos/instant vão para fast
    assert _classify_groq_model("llama-3.1-8b-instant") == "fast"


def test_score_model_prefers_larger_context():
    from model_router import _score_model
    big = {"context_window": 131072, "tier": "balanced"}
    small = {"context_window": 8192, "tier": "balanced"}
    assert _score_model(big) > _score_model(small)
