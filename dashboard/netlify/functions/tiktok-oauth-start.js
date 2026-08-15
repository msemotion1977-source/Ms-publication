exports.handler = async (event) => {
  const channelId = event.queryStringParameters.channel_id;
  const clientKey = process.env.TIKTOK_CLIENT_KEY;
  const redirectUri = `${process.env.URL}/.netlify/functions/tiktok-oauth-callback`;

  const scope = encodeURIComponent('video.publish,video.upload,user.info.basic');
  const authUrl =
    `https://www.tiktok.com/v2/auth/authorize/` +
    `?client_key=${clientKey}` +
    `&response_type=code` +
    `&scope=${scope}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&state=${channelId}`;

  return { statusCode: 302, headers: { Location: authUrl }, body: '' };
};
