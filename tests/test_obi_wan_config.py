import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "obi-wan"))

import pytest
from config import Config


def test_requires_groq_key():
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        Config(env={"TELEGRAM_TOKEN": "t", "SOL_CHAT_ID": "1"})


def test_parses_and_defaults():
    cfg = Config(env={"TELEGRAM_TOKEN": "t", "SOL_CHAT_ID": "1030157568", "GROQ_API_KEY": "gsk_x"})
    assert cfg.sol_chat_id == 1030157568
    assert cfg.groq_model == "openai/gpt-oss-120b"
