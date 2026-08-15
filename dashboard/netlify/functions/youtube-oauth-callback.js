const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event) => {
  const { code, state: channelId } = event.queryStringParameters;
  const redirectUri = `${process.env.URL}/.netlify/functions/youtube-oauth-callback`;

  try {
    const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        code,
        client_id: process.env.YOUTUBE_CLIENT_ID,
        client_secret: process.env.YOUTUBE_CLIENT_SECRET,
        redirect_uri: redirectUri,
        grant_type: 'authorization_code',
      }),
    });
    const tokens = await tokenRes.json();
    if (!tokens.access_token) throw new Error(JSON.stringify(tokens));

    // Récupère l'ID de chaîne YouTube réel du compte qui vient de se connecter
    const chanRes = await fetch('https://www.googleapis.com/youtube/v3/channels?part=id&mine=true', {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });
    const chanData = await chanRes.json();
    const externalChannelId = chanData.items?.[0]?.id || null;

    // service_role key : uniquement dans les env vars serveur, jamais exposée au navigateur
    const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
    await supabase.from('channels').update({
      oauth_access_token: tokens.access_token,
      oauth_refresh_token: tokens.refresh_token,
      oauth_expires_at: new Date(Date.now() + tokens.expires_in * 1000).toISOString(),
      external_channel_id: externalChannelId,
    }).eq('id', channelId);

    return {
      statusCode: 302,
      headers: { Location: `${process.env.URL}/?connected=youtube` },
      body: '',
    };
  } catch (e) {
    return { statusCode: 500, body: `Erreur OAuth YouTube : ${e.message}` };
  }
};
