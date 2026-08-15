// ⚠️ À remplir avec TES valeurs (voir README, étape "Supabase").
// SUPABASE_ANON_KEY est une clé PUBLIQUE (elle est visible dans le navigateur, c'est normal),
// jamais la "service_role key" ici — celle-là ne doit vivre que côté GitHub Actions.

const SUPABASE_URL = "https://jbwqzxorpldfoykjdaaw.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impid3F6eG9ycGxkZm95a2pkYWF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY3NzU2NTYsImV4cCI6MjEwMjM1MTY1Nn0.WHOBo-KVwKR6ngZ8nInH8nzOxIyeCLxmWNBlhKykl78";

// Ces deux fonctions Netlify gèrent l'échange OAuth (voir dashboard/netlify/functions/).
const YOUTUBE_OAUTH_START = "/.netlify/functions/youtube-oauth-start";
const TIKTOK_OAUTH_START = "/.netlify/functions/tiktok-oauth-start";
