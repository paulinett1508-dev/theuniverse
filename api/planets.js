const OWNER = 'paulinett1508-dev';

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
        openIssues: issues(states: OPEN) { totalCount }
        defaultBranchRef {
          target {
            ... on Commit {
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

        let health = 'healthy';
        if (repo.isArchived || daysSincePush > 120) health = 'dormant';
        else if (ci === 'FAILURE' || ci === 'ERROR') health = 'alert';
        else if (daysSincePush > 30 || issues > 3) health = 'warning';

        planets.push({ name: repo.name, pushedAt: repo.pushedAt, daysSincePush, ci, issues, health });
      }

      after = repos.pageInfo.hasNextPage ? repos.pageInfo.endCursor : null;
    } while (after);

    res.status(200).json({ planets, updatedAt: new Date().toISOString() });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
