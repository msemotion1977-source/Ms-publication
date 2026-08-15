// Appelle l'API GitHub pour lancer le workflow daily-publish.yml immédiatement,
// limité à une seule chaîne (bouton "Publier maintenant" du dashboard).
exports.handler = async (event) => {
  try {
    const { channel_id } = JSON.parse(event.body || '{}');
    const [owner, repo] = process.env.GITHUB_REPO.split('/'); // ex: "tonpseudo/ms-publication"

    const res = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/actions/workflows/daily-publish.yml/dispatches`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${process.env.GITHUB_PAT}`,
          Accept: 'application/vnd.github+json',
        },
        body: JSON.stringify({ ref: 'main', inputs: { channel_id: channel_id || '' } }),
      }
    );

    if (!res.ok) {
      const text = await res.text();
      return { statusCode: 500, body: text };
    }
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  } catch (e) {
    return { statusCode: 500, body: e.message };
  }
};
