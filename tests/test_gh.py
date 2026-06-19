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
        page = int(path.split("&page=")[1].split("&")[0])
        calls.append(page)
        return pages[page], {}

    repos = gh.list_repos("tok", _api=fake_api)
    names = [r["name"] for r in repos]
    assert names == ["alpha", "beta"]   # theuniverse excluído
    assert calls == [1, 2, 3]           # parou na página vazia
