const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event) => {
  const { code, state: channelId } = event.queryStringParameters;
  const redirectUri = `${process.env.URL}/.netlify/functions/tiktok-oauth-callback`;

  try {
    const tokenRes = await fetch('https://open.tiktokapis.com/v2/oauth/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_key: process.env.TIKTOK_CLIENT_KEY,
        client_secret: process.env.TIKTOK_CLIENT_SECRET,
        code,
        grant_type: 'authorization_code',
        redirect_uri: redirectUri,
      }),
    });
    const tokens = await tokenRes.json();
    if (!tokens.access_token) throw new Error(JSON.stringify(tokens));

    const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
    await supabase.from('channels').update({
      oauth_access_token: tokens.access_token,
      oauth_refresh_token: tokens.refresh_token,
      oauth_expires_at: new Date(Date.now() + tokens.expires_in * 1000).toISOString(),
      external_channel_id: tokens.open_id,
    }).eq('id', channelId);

    return {
      statusCode: 302,
      headers: { Location: `${process.env.URL}/?connected=tiktok` },
      body: '',
    };
  } catch (e) {
    return { statusCode: 500, body: `Erreur OAuth TikTok : ${e.message}` };
  }
};
