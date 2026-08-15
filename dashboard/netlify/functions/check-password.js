// Compare le mot de passe envoyé à la variable d'env Netlify DASHBOARD_PASSWORD.
// Définie dans Netlify > Site configuration > Environment variables (jamais dans le code).
exports.handler = async (event) => {
  try {
    const { password } = JSON.parse(event.body || '{}');
    const expected = process.env.DASHBOARD_PASSWORD;

    if (!expected) {
      return { statusCode: 500, body: JSON.stringify({ ok: false, error: 'DASHBOARD_PASSWORD non configuré côté Netlify' }) };
    }
    if (password === expected) {
      return { statusCode: 200, body: JSON.stringify({ ok: true }) };
    }
    return { statusCode: 401, body: JSON.stringify({ ok: false }) };
  } catch (e) {
    return { statusCode: 400, body: JSON.stringify({ ok: false, error: e.message }) };
  }
};
