// Redirige vers l'écran de consentement Google. channel_id est renvoyé tel quel
// via "state" pour qu'on sache quelle fiche mettre à jour au retour.
exports.handler = async (event) => {
  const channelId = event.queryStringParameters.channel_id;
  const clientId = process.env.YOUTUBE_CLIENT_ID;
  const redirectUri = `${process.env.URL}/.netlify/functions/youtube-oauth-callback`;

  const scope = encodeURIComponent('https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly');
  const authUrl =
    `https://accounts.google.com/o/oauth2/v2/auth` +
    `?client_id=${clientId}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&response_type=code` +
    `&access_type=offline` +
    `&prompt=consent` +
    `&scope=${scope}` +
    `&state=${channelId}`;

  return { statusCode: 302, headers: { Location: authUrl }, body: '' };
};
