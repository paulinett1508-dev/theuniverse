const fs = require('fs');
const path = require('path');

module.exports = function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=120, stale-while-revalidate=300');

  try {
    const raw = fs.readFileSync(
      path.join(process.cwd(), 'state/posture-status.json'), 'utf8'
    );
    const posture = JSON.parse(raw);

    let criticals = 0, warnings = 0;
    for (const r of posture.repos) {
      for (const a of r.achados_abertos) {
        if (a.severidade === 'critico') criticals++;
        else warnings++;
      }
    }

    const status = criticals > 0 ? 'critical' : warnings > 0 ? 'warnings' : 'clean';
    res.status(200).json({ status, criticals, warnings, ts: posture.ts, resumo: posture.resumo });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
