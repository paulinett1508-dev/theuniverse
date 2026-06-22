#!/usr/bin/env python3
"""Testes do scan_text — travam a calibração de ruído (real vs falso-positivo)."""
import unittest
from secret_scan import scan_text, redact, _is_placeholder


class TestScanText(unittest.TestCase):
    def _labels(self, text, path="x.py"):
        return [f["label"] for f in scan_text("repo", path, text)]

    def test_detecta_senha_hardcoded_real(self):
        # valores fictícios neutros — só precisam casar o padrão (keyword + literal sem espaço)
        self.assertTrue(scan_text("r", "dvr.py", 'RTSP_PASS = "Kf8jZq2mra"'))
        self.assertTrue(scan_text("r", "dc.yml", 'WEBPASSWORD: "Wb3pXy9Qz1"'))
        self.assertTrue(scan_text("r", "x.ps1", "$UserPassword = 'Rd7sNk88vt'"))
        self.assertTrue(scan_text("r", "p.py", '{"username":"admin","password":"Pt6oRz42kx"}'))

    def test_detecta_token_telegram(self):
        tok = "1234567890:" + "A" * 35
        self.assertEqual(self._labels(f'TOKEN = "{tok}"'), ["Telegram bot token"])

    def test_ignora_declaracao_de_tipo(self):
        self.assertEqual(scan_text("r", "a.ts", "senha: string"), [])
        self.assertEqual(scan_text("r", "a.ts", "senha: z.string().min(1)"), [])
        self.assertEqual(scan_text("r", "a.ts", "const { senha } = req.body"), [])

    def test_ignora_placeholder_e_exemplo(self):
        self.assertEqual(scan_text("r", "d.md", 'password: "SUA_SENHA"'), [])
        self.assertEqual(scan_text("r", "d.md", 'senha: "qualquer"'), [])
        self.assertEqual(scan_text("r", "t.js", "pwd: 'errada'"), [])
        self.assertEqual(scan_text("r", "x.py", 'password: "${ENV_VAR}"'), [])

    def test_ignora_rotulo_de_ui(self):
        # ternário com label de UI não é segredo (valor tem espaço)
        self.assertEqual(scan_text("r", "ui.js", "showing ? 'Mostrar senha' : 'Ocultar senha'"), [])

    def test_ignora_caminhos_de_teste(self):
        self.assertEqual(scan_text("r", "src/__tests__/a.test.js", 'password = "realpass99"'), [])
        self.assertEqual(scan_text("r", "x.spec.ts", 'password = "realpass99"'), [])

    def test_redact_esconde_o_miolo(self):
        r = redact("RTSP_PASS = Kf8jZq2mra")
        self.assertNotIn("Kf8jZq2mra", r)
        self.assertIn("***", r)

    def test_is_placeholder(self):
        self.assertTrue(_is_placeholder("SUA_SENHA"))
        self.assertTrue(_is_placeholder("string"))
        self.assertTrue(_is_placeholder("${X}"))
        self.assertFalse(_is_placeholder("Kf8jZq2mra"))
        self.assertFalse(_is_placeholder("Mix7Case#9"))


if __name__ == "__main__":
    unittest.main()
