const OWNER = 'paulinett1508-dev';

const EXCLUDE = new Set([
  'the-matrix', 'matrix-core',
  'baileys-whatsapp-server', 'bitrix-buddy-chat',
  'agnvendas-painelsbr', 'pedidomobile',
  'theuniverse',
]);

const WINDOW_MS = 90_000; // events within last 90s

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=10');

  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(500).json({ error: 'no token' });

  try {
    const r = await fetch(
      `https://api.github.com/users/${OWNER}/events?per_page=60`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'User-Agent': 'theuniverse-dashboard',
        },
      }
    );

    if (!r.ok) return res.status(r.status).json({ error: r.statusText });

    const raw = await r.json();
    const now = Date.now();
    const events = [];

    for (const ev of raw) {
      const repoName = ev.repo?.name?.split('/')[1];
      if (!repoName || EXCLUDE.has(repoName)) continue;

      const age = now - new Date(ev.created_at).getTime();
      if (age > WINDOW_MS) continue;

      let type = null;
      if (ev.type === 'PushEvent') type = 'push';
      else if (ev.type === 'PullRequestEvent')
        type = ev.payload?.pull_request?.merged ? 'pr_merged' : 'pr';
      else if (ev.type === 'IssuesEvent') type = 'issue';
      else if (ev.type === 'CreateEvent') type = 'create';

      if (type) events.push({ id: ev.id, repo: repoName, type, ts: ev.created_at });
    }

    res.status(200).json({ events });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
