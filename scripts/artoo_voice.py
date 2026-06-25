"""Artoo · voz — personalidade e mensagens do mensageiro cósmico.

Três eras baseadas em missões acumuladas:
  novice     (0–9)   — entusiasta, um pouco cerimonioso
  journeyman (10–49) — confiante, direto, já viu de tudo
  veteran    (50+)   — lacônico, seco, cada palavra pesa
"""

_ROTA = {
    "novice": [
        "🛸 <b>Artoo</b> em rota\n\ndestino: <b>{repo}</b>\nameaça: {reason}",
        "🛸 <b>Artoo</b> saindo do observatório\n\nrumando para <b>{repo}</b>\nameaça: {reason}",
        "🛸 <b>Artoo</b> foi lançado\n\ncoordenadas: <b>{repo}</b>\nameaça: {reason}",
    ],
    "journeyman": [
        "🛸 <b>Artoo</b> partiu · missão #{n}\n\n<b>{repo}</b> precisa ser alertado\nameaça: {reason}",
        "🛸 <b>Artoo</b> atravessa a órbita\n\ndestino: <b>{repo}</b>\nameaça: {reason}",
        "🛸 <b>Artoo</b> em rota\n\n<b>{repo}</b> · ameaça detectada: {reason}",
    ],
    "veteran": [
        "🛸 <b>Artoo</b>\n\n<b>{repo}</b> · {reason}",
        "🛸 missão #{n} · <b>{repo}</b>\n{reason}",
        "🛸 <b>{repo}</b> · alerta em rota\n{reason}",
    ],
}

_CHEGOU = {
    "novice": [
        "✅ <b>Artoo chegou</b>\n\n<b>{repo}</b> · issue #{issue_number} aberta\no mundo deles foi alertado",
        "✅ <b>Missão concluída</b>\n\n<b>{repo}</b> recebeu o alerta · issue #{issue_number}\naguardando resposta",
    ],
    "journeyman": [
        "✅ <b>Artoo chegou</b>\n\n<b>{repo}</b> · issue #{issue_number}\nalerta entregue",
        "✅ <b>Entrega confirmada</b>\n\n<b>{repo}</b> · issue #{issue_number}\no planeta foi avisado",
        "✅ <b>Artoo voltou</b> · missão #{n}\n\n<b>{repo}</b> alertado · issue #{issue_number}",
    ],
    "veteran": [
        "✅ <b>{repo}</b> · #{issue_number}\nalerta entregue",
        "✅ missão #{n} · <b>{repo}</b> alertado",
        "✅ <b>{repo}</b> · issue #{issue_number} · feito",
    ],
}

_PERDIDO = {
    "novice": [
        "❌ <b>Artoo perdido na órbita</b>\n\ndestino: <b>{repo}</b>\nerro: <code>{err}</code>",
        "❌ <b>Artoo não conseguiu chegar</b>\n\n<b>{repo}</b> não foi alertado\nerro: <code>{err}</code>",
    ],
    "journeyman": [
        "❌ <b>Artoo não chegou</b>\n\n<b>{repo}</b> · sem contato\nerro: <code>{err}</code>",
        "❌ <b>Falha na missão #{n}</b>\n\n<b>{repo}</b> não recebeu o alerta\nerro: <code>{err}</code>",
    ],
    "veteran": [
        "❌ <b>{repo}</b> · sem contato\n<code>{err}</code>",
        "❌ missão #{n} falhou · <b>{repo}</b>\n<code>{err}</code>",
    ],
}


def _era(mission_count):
    if mission_count < 10:
        return "novice"
    if mission_count < 50:
        return "journeyman"
    return "veteran"


def format_rota(repo, reason, detail="", mission_count=0, seed=None):
    era = _era(mission_count)
    pool = _ROTA[era]
    if seed is None:
        seed = abs(hash(repo + reason)) % 97
    msg = pool[seed % len(pool)]
    result = msg.format(repo=repo, reason=reason, n=mission_count + 1)
    if detail:
        result += f"\ndetalhe: <i>{detail}</i>"
    return result


def format_chegou(repo, issue_number, issue_url, mission_count=0, seed=None):
    era = _era(mission_count)
    pool = _CHEGOU[era]
    if seed is None:
        seed = abs(hash(repo + str(issue_number))) % 97
    msg = pool[seed % len(pool)]
    result = msg.format(repo=repo, issue_number=issue_number, n=mission_count + 1)
    return result + f'\n\n<a href="{issue_url}">↗ ver issue</a>'


def format_perdido(repo, err, mission_count=0, seed=None):
    era = _era(mission_count)
    pool = _PERDIDO[era]
    if seed is None:
        seed = abs(hash(repo + str(err))) % 97
    msg = pool[seed % len(pool)]
    return msg.format(repo=repo, err=str(err)[:200], n=mission_count + 1)
