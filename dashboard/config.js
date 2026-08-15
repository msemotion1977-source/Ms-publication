// ⚠️ À remplir avec TES valeurs (voir README, étape "Supabase").
// SUPABASE_ANON_KEY est une clé PUBLIQUE (elle est visible dans le navigateur, c'est normal),
// jamais la "service_role key" ici — celle-là ne doit vivre que côté GitHub Actions.

const SUPABASE_URL = "https://TON-PROJET.supabase.co";
const SUPABASE_ANON_KEY = "TON_ANON_KEY_ICI";

// Ces deux fonctions Netlify gèrent l'échange OAuth (voir dashboard/netlify/functions/).
const YOUTUBE_OAUTH_START = "/.netlify/functions/youtube-oauth-start";
const TIKTOK_OAUTH_START = "/.netlify/functions/tiktok-oauth-start";
