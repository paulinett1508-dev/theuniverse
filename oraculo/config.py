"""Configuração do Oráculo do Universo a partir do ambiente."""
import os


class Config:
    def __init__(self, env=None):
        env = env if env is not None else os.environ
        self.telegram_token = self._require(env, "TELEGRAM_TOKEN")
        self.sol_chat_id = int(self._require(env, "SOL_CHAT_ID"))
        self.groq_api_key = self._require(env, "GROQ_API_KEY")
        self.groq_model = env.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    @staticmethod
    def _require(env, key):
        val = env.get(key)
        if not val:
            raise ValueError(f"Variável de ambiente obrigatória ausente: {key}")
        return val
