#!/usr/bin/env python3
"""Testes do scan_text — travam a calibração de ruído (real vs falso-positivo)."""
import unittest
from secret_scan import scan_text, redact, _is_placeholder, build_posture


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

    def test_ignora_arquivo_example(self):
        # .env.example / settings.json.example são templates — placeholder por definição
        self.assertEqual(scan_text("r", ".env.example", 'PASSWORD="Kf8jZq2mra"'), [])
        self.assertEqual(scan_text("r", "settings.json.example", 'PASSWORD="Kf8jZq2mra"'), [])

    def test_ignora_linha_ja_redigida(self):
        # não re-alertar conteúdo já mascarado (evita o scanner flagrar o próprio doc de achados)
        self.assertEqual(scan_text("r", "AUDIT.md", "ADMIN_PASSWORD='Sen***26'"), [])

    def test_pem_exige_corpo_real(self):
        # placeholder de chave privada não alerta
        self.assertEqual(
            scan_text("r", "README.md", 'KEY="-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----"'),
            [])
        # chave com corpo base64 real alerta
        body = "MIIBVAIBADANBgkqhkiG9w0BAQEFAASCAT4wggE6AgEAAkEAZk9pLmQ2Rw8Tn4Vb1Yc3Xs6Dh0Gf7Jp"
        self.assertTrue(
            scan_text("r", "leaked.pem", f'KEY="-----BEGIN PRIVATE KEY-----\\n{body}\\n-----END"'))

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


class TestBuildPosture(unittest.TestCase):
    def _finding(self, repo="r", path="a.py", line=1, key="k1"):
        return {"repo": repo, "path": path, "line": line, "label": "Senha/secret hardcoded",
                "redacted": "PASS = ***", "key": key}

    def test_schema_e_entity(self):
        p = build_posture([], {"r": "private"}, 1718800000)
        self.assertEqual(p["schema"], "entity-exchange/posture-status@1")
        self.assertEqual(p["entity"], "sentinel")

    def test_repo_limpo_score_100(self):
        p = build_posture([], {"limpo": "private"}, 1)
        r = p["repos"][0]
        self.assertEqual(r["score"], 100)
        self.assertEqual(r["achados_abertos"], [])

    def test_publico_com_segredo_e_critico(self):
        p = build_posture([self._finding(repo="pub")], {"pub": "public"}, 1)
        r = p["repos"][0]
        self.assertEqual(r["achados_abertos"][0]["kind"], "repo_publico_com_segredo")
        self.assertEqual(r["achados_abertos"][0]["severidade"], "critico")
        self.assertEqual(r["score"], 75)  # 100 - 25
        self.assertIn("crítico", p["resumo"])

    def test_privado_e_aviso(self):
        p = build_posture([self._finding(repo="priv")], {"priv": "private"}, 1)
        a = p["repos"][0]["achados_abertos"][0]
        self.assertEqual(a["severidade"], "avisos")
        self.assertEqual(p["repos"][0]["score"], 90)  # 100 - 10

    def test_detalhe_redigido_nunca_cru(self):
        p = build_posture([self._finding()], {"r": "private"}, 1)
        self.assertNotIn("PASS = sobral", json_dump(p))  # nada de valor cru
        self.assertIn("***", p["repos"][0]["achados_abertos"][0]["detalhe"])


def json_dump(o):
    import json
    return json.dumps(o)


if __name__ == "__main__":
    unittest.main()
