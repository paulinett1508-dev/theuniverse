const OWNER = 'paulinett1508-dev';

const SPECIAL_BODIES = {
  'agnostic-core':  'station',
  'mcp-eventos':    'satellite',
  'luna-base':      'observatory',
  'bolaocopa2026':  'supernova',
  'f1-pulse':       'supernova',
  'vibegaminghub':  'toys',
};

const EXCLUDE = new Set([
  'the-matrix', 'matrix-core',
  'baileys-whatsapp-server', 'bitrix-buddy-chat',
  'agnvendas-painelsbr', 'pedidomobile',
  'theuniverse',
]);

const QUERY = `
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 100, after: $after, orderBy: {field: PUSHED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        pushedAt
        isArchived
        diskUsage
        primaryLanguage { name color }
        mentionableUsers(first: 0) { totalCount }
        openIssues: issues(states: OPEN) { totalCount }
        pullRequests(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes { title state mergedAt createdAt }
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history { totalCount }
              statusCheckRollup { state }
            }
          }
        }
      }
    }
  }
}`;

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=120, stale-while-revalidate');

  const token = process.env.GITHUB_TOKEN;
  if (!token) return res.status(500).json({ error: 'GITHUB_TOKEN not set' });

  try {
    const planets = [];
    let after = null;

    do {
      const r = await fetch('https://api.github.com/graphql', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          'User-Agent': 'theuniverse-dashboard',
        },
        body: JSON.stringify({ query: QUERY, variables: { login: OWNER, after } }),
      });

      const data = await r.json();
      const repos = data.data?.user?.repositories;
      if (!repos) break;

      for (const repo of repos.nodes) {
        if (EXCLUDE.has(repo.name)) continue;

        const daysSincePush = repo.pushedAt
          ? Math.floor((Date.now() - new Date(repo.pushedAt)) / 86400000)
          : 999;

        const ci = repo.defaultBranchRef?.target?.statusCheckRollup?.state ?? null;
        const issues = repo.openIssues?.totalCount ?? 0;
        const commits = repo.defaultBranchRef?.target?.history?.totalCount ?? 0;
        const diskKB = repo.diskUsage ?? 0;

        let health = 'healthy';
        if (repo.isArchived || daysSincePush > 120) health = 'dormant';
        else if (ci === 'FAILURE' || ci === 'ERROR') health = 'alert';
        else if (daysSincePush > 30 || issues > 3) health = 'warning';

        // raw magnitude score (log scale — commit counts vary wildly)
        const rawScore = Math.log10(1 + commits) * 0.65 + Math.log10(1 + diskKB) * 0.35;

        const lang = repo.primaryLanguage
          ? { name: repo.primaryLanguage.name, color: repo.primaryLanguage.color || '#8b949e' }
          : null;
        const contributors = repo.mentionableUsers?.totalCount ?? 0;
        const lastPR = repo.pullRequests?.nodes?.[0] ?? null;

        const bodyType = SPECIAL_BODIES[repo.name] || 'planet';

        planets.push({ name: repo.name, pushedAt: repo.pushedAt, daysSincePush, ci, issues, health, commits, diskKB, rawScore, lang, contributors, lastPR, bodyType });
      }

      after = repos.pageInfo.hasNextPage ? repos.pageInfo.endCursor : null;
    } while (after);

    // Normalize rawScore → magnitude 1–5
    const scores = planets.map(p => p.rawScore);
    const minS = Math.min(...scores), maxS = Math.max(...scores);
    const range = maxS - minS || 1;
    for (const p of planets) {
      p.magnitude = Math.round(1 + ((p.rawScore - minS) / range) * 4); // 1–5
      delete p.rawScore;
    }

    res.status(200).json({ planets, updatedAt: new Date().toISOString() });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
