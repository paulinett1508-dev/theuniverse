import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from artoo_voice import _era, format_rota, format_chegou, format_perdido


def test_era_novice():
    assert _era(0) == "novice"
    assert _era(9) == "novice"


def test_era_journeyman():
    assert _era(10) == "journeyman"
    assert _era(49) == "journeyman"


def test_era_veteran():
    assert _era(50) == "veteran"
    assert _era(200) == "veteran"


def test_format_rota_contains_repo():
    msg = format_rota("sbrgestao", "CI falhou", seed=0)
    assert "sbrgestao" in msg


def test_format_rota_contains_reason():
    msg = format_rota("sbrgestao", "CI falhou", seed=0)
    assert "CI falhou" in msg


def test_format_rota_includes_detail():
    msg = format_rota("sbrgestao", "CI falhou", detail="tests", seed=0)
    assert "tests" in msg


def test_format_rota_no_detail_no_label():
    msg = format_rota("sbrgestao", "CI falhou", seed=0)
    assert "detalhe:" not in msg


def test_format_rota_varies_by_seed():
    msgs = {format_rota("sbrgestao", "CI falhou", seed=i, mission_count=0) for i in range(3)}
    assert len(msgs) > 1


def test_format_rota_veteran_is_terser():
    novice = format_rota("sbrgestao", "CI falhou", seed=0, mission_count=0)
    veteran = format_rota("sbrgestao", "CI falhou", seed=0, mission_count=50)
    assert len(veteran) < len(novice)


def test_format_chegou_contains_repo():
    msg = format_chegou("sbrgestao", 42, "https://github.com/x/y/issues/42", seed=0)
    assert "sbrgestao" in msg


def test_format_chegou_contains_issue_number():
    msg = format_chegou("sbrgestao", 42, "https://github.com/x/y/issues/42", seed=0)
    assert "42" in msg


def test_format_chegou_contains_url():
    url = "https://github.com/x/y/issues/42"
    msg = format_chegou("sbrgestao", 42, url, seed=0)
    assert url in msg


def test_format_chegou_varies_by_seed():
    url = "https://github.com/x/y/issues/1"
    msgs = {format_chegou("sbrgestao", 1, url, seed=i, mission_count=10) for i in range(3)}
    assert len(msgs) > 1


def test_format_perdido_contains_repo():
    msg = format_perdido("sbrgestao", "HTTP 422", seed=0)
    assert "sbrgestao" in msg


def test_format_perdido_contains_error():
    msg = format_perdido("sbrgestao", "HTTP 422", seed=0)
    assert "HTTP 422" in msg


def test_format_perdido_truncates_long_error():
    long_err = "x" * 300
    msg = format_perdido("sbrgestao", long_err, seed=0)
    assert "x" * 201 not in msg
