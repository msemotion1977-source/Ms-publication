-- MS PUBLICATION — schéma Supabase
-- À exécuter dans Supabase > SQL Editor (une seule fois, à la création du projet)

create extension if not exists "uuid-ossp";

-- Une ligne = une chaîne YouTube OU un compte TikTok connecté
create table channels (
  id uuid primary key default uuid_generate_v4(),
  platform text not null check (platform in ('youtube', 'tiktok')),
  display_name text not null,               -- nom affiché dans le dashboard
  niche text not null,                      -- ex: "faits divers insolites", "horreur courte", "quiz culture générale"
  gameplay_query text not null,             -- mot-clé Pixabay pour choisir le fond gameplay (ex: "minecraft parkour")
  active boolean default true,              -- coupe la publication auto si false
  weekly_long_video boolean default false,  -- vidéo longue hebdo (YouTube uniquement)
  long_video_day int default 1,             -- 1=lundi ... 7=dimanche

  -- OAuth
  oauth_access_token text,
  oauth_refresh_token text,
  oauth_expires_at timestamptz,
  external_channel_id text,                 -- channelId YouTube ou open_id TikTok

  -- TikTok uniquement : passe à true une fois l'audit TikTok validé
  tiktok_audited boolean default false,

  created_at timestamptz default now()
);

-- Une ligne = une musique uploadée par l'utilisateur, réutilisable sur plusieurs vidéos
create table music_tracks (
  id uuid primary key default uuid_generate_v4(),
  channel_id uuid references channels(id) on delete cascade,
  storage_path text not null,   -- chemin dans le bucket Supabase Storage "music"
  label text,
  created_at timestamptz default now()
);

-- Une ligne = une image fournie par l'utilisateur à insérer dans le montage (facultatif)
create table user_images (
  id uuid primary key default uuid_generate_v4(),
  channel_id uuid references channels(id) on delete cascade,
  storage_path text not null,
  label text,
  created_at timestamptz default now()
);

-- Historique des publications (alimente les stats du dashboard)
create table publications (
  id uuid primary key default uuid_generate_v4(),
  channel_id uuid references channels(id) on delete cascade,
  published_at timestamptz default now(),
  status text not null check (status in ('published', 'private_pending_tiktok_audit', 'failed')),
  title text,
  video_url text,
  is_long_video boolean default false,
  error_message text
);

-- Snapshot hebdomadaire abonnés / revenus par chaîne (rempli par le job GitHub Actions)
create table stats_weekly (
  id uuid primary key default uuid_generate_v4(),
  channel_id uuid references channels(id) on delete cascade,
  week_start date not null,
  subscribers int default 0,
  subscribers_gained int default 0,
  revenue_cents int default 0,
  updated_at timestamptz default now(),
  unique (channel_id, week_start)
);

alter table channels enable row level security;
alter table music_tracks enable row level security;
alter table user_images enable row level security;
alter table publications enable row level security;
alter table stats_weekly enable row level security;

-- Projet mono-utilisateur (toi) : le dashboard utilise la clé "anon" avec un mot de passe
-- d'accès simple côté Netlify (voir README). On autorise donc anon en lecture/écriture ici.
-- Si tu comptes ouvrir le site à d'autres personnes plus tard, il faudra remplacer ces
-- policies par une vraie auth Supabase (auth.uid()).
create policy "anon full access channels" on channels for all using (true) with check (true);
create policy "anon full access music" on music_tracks for all using (true) with check (true);
create policy "anon full access images" on user_images for all using (true) with check (true);
create policy "anon full access publications" on publications for all using (true) with check (true);
create policy "anon full access stats" on stats_weekly for all using (true) with check (true);

-- Buckets de stockage (à créer aussi depuis l'interface Supabase Storage, publics en lecture)
-- "music"  : fichiers audio uploadés par l'utilisateur
-- "images" : images fournies par l'utilisateur pour le montage
-- "renders": vidéos rendues temporairement, le temps d'être poussées sur YouTube/TikTok
