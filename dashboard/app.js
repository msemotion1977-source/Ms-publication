// MS PUBLICATION — dashboard
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

let channels = [];
let selectedChannelId = null;

// ---------- Portail mot de passe ----------
const gate = document.getElementById('gate');
const app = document.getElementById('app');

if (sessionStorage.getItem('ms_pub_unlocked') === '1') {
  unlock();
}

document.getElementById('gate-submit').addEventListener('click', tryUnlock);
document.getElementById('gate-password').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') tryUnlock();
});

async function tryUnlock() {
  const password = document.getElementById('gate-password').value;
  const res = await fetch('/.netlify/functions/check-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  }).catch(() => null);

  if (res && res.ok) {
    sessionStorage.setItem('ms_pub_unlocked', '1');
    unlock();
  } else {
    document.getElementById('gate-password').style.borderColor = 'var(--danger)';
  }
}

function unlock() {
  gate.classList.add('hidden');
  app.classList.remove('hidden');
  boot();
}

// ---------- Boot ----------
async function boot() {
  await loadChannels();
  renderRail();
  setTicker(`${channels.length} chaîne(s) sous supervision`);
}

async function loadChannels() {
  const { data, error } = await supabaseClient.from('channels').select('*').order('created_at');
  if (error) { setTicker('Erreur de connexion à la base'); return; }
  channels = data || [];
}

function setTicker(text) {
  document.getElementById('ticker-text').textContent = text;
}

// ---------- Rail (liste des chaînes) ----------
function renderRail() {
  const yt = channels.filter(c => c.platform === 'youtube');
  const tt = channels.filter(c => c.platform === 'tiktok');
  renderRailGroup('rail-youtube', yt, '#FF3B3B');
  renderRailGroup('rail-tiktok', tt, '#25F4EE');
}

function renderRailGroup(elId, list, color) {
  const el = document.getElementById(elId);
  if (list.length === 0) {
    el.innerHTML = `<div class="rail-empty">Aucune chaîne connectée</div>`;
    return;
  }
  el.innerHTML = list.map(c => `
    <div class="rail-item ${c.id === selectedChannelId ? 'selected' : ''}" data-id="${c.id}">
      <span class="rail-status-dot" style="background:${c.active ? 'var(--success)' : 'var(--text-dim)'}"></span>
      ${escapeHtml(c.display_name)}
    </div>
  `).join('');
  el.querySelectorAll('.rail-item').forEach(item => {
    item.addEventListener('click', () => selectChannel(item.dataset.id));
  });
}

async function selectChannel(id) {
  selectedChannelId = id;
  renderRail();
  await renderChannelPanel(id);
}

// ---------- Fiche chaîne ----------
async function renderChannelPanel(id) {
  const c = channels.find(ch => ch.id === id);
  if (!c) return;
  const main = document.getElementById('main');
  document.getElementById('empty-state').classList.add('hidden');

  const [{ data: pubs }, { data: stats }, { data: music }, { data: images }] = await Promise.all([
    supabaseClient.from('publications').select('*').eq('channel_id', id).order('published_at', { ascending: false }).limit(10),
    supabaseClient.from('stats_weekly').select('*').eq('channel_id', id).order('week_start', { ascending: false }).limit(1),
    supabaseClient.from('music_tracks').select('*').eq('channel_id', id),
    supabaseClient.from('user_images').select('*').eq('channel_id', id)
  ]);

  const latestStat = (stats && stats[0]) || { subscribers: 0, subscribers_gained: 0, revenue_cents: 0 };
  const isConnected = !!c.oauth_refresh_token;
  const todayPub = (pubs || []).find(p => isToday(p.published_at));

  main.innerHTML = `
    <div class="channel-header">
      <div>
        <h1 class="channel-title">${escapeHtml(c.display_name)}</h1>
        <div class="channel-meta">${c.platform.toUpperCase()} · NICHE : ${escapeHtml(c.niche).toUpperCase()}</div>
      </div>
      <div style="display:flex; gap:10px;">
        <button class="btn-ghost" id="btn-publish-now">Publier maintenant</button>
        <button class="btn-ghost" id="btn-edit">Modifier la fiche</button>
      </div>
    </div>

    ${!isConnected ? `
      <div class="connect-banner">
        <p>Cette fiche n'est pas encore reliée à un compte ${c.platform === 'youtube' ? 'YouTube' : 'TikTok'}.</p>
        <button class="btn-accent" id="btn-oauth-connect">Connecter à ${c.platform === 'youtube' ? 'YouTube' : 'TikTok'}</button>
      </div>
    ` : ''}

    ${c.platform === 'tiktok' && !c.tiktok_audited ? `
      <div class="connect-banner" style="border-color:#7a2626;">
        <p>⚠️ App TikTok non auditée : les publications sortent en privé (visible par toi uniquement) jusqu'à validation manuelle ou audit passé.</p>
      </div>
    ` : ''}

    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-label">Abonnés</div>
        <div class="stat-value">${latestStat.subscribers.toLocaleString('fr-FR')}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Abonnés cette semaine</div>
        <div class="stat-value positive">+${latestStat.subscribers_gained.toLocaleString('fr-FR')}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Revenus cumulés cette semaine</div>
        <div class="stat-value positive">${(latestStat.revenue_cents / 100).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })}</div>
      </div>
    </div>

    <div class="pipeline">
      <p class="pipeline-title">Pipeline du jour</p>
      ${renderPipeline(todayPub, c)}
    </div>

    <div class="section-block">
      <h3>Configuration</h3>
      <div class="field-row">
        <div class="field"><div class="field-key">Niche</div><div class="field-val">${escapeHtml(c.niche)}</div></div>
        <div class="field"><div class="field-key">Mot-clé gameplay</div><div class="field-val">${escapeHtml(c.gameplay_query)}</div></div>
        <div class="field"><div class="field-key">Vidéo longue hebdo</div><div class="field-val">${c.weekly_long_video ? 'Activée' : 'Désactivée'}</div></div>
        <div class="field"><div class="field-key">Statut</div><div class="field-val">${c.active ? 'Active' : 'En pause'}</div></div>
      </div>
    </div>

    <div class="section-block">
      <h3>Musiques (${(music || []).length})</h3>
      <div class="file-drop" id="music-drop">Cliquer pour ajouter un fichier audio (mp3, wav)</div>
      <input type="file" id="music-input" accept="audio/*" class="hidden" />
      <div class="upload-list">
        ${(music || []).map(m => `<div class="upload-chip">🎵 ${escapeHtml(m.label || m.storage_path.split('/').pop())}</div>`).join('') || '<span style="color:var(--text-dim); font-size:12px;">Aucune musique ajoutée — le montage utilisera l\'audio de la bibliothèque libre de droits par défaut.</span>'}
      </div>
    </div>

    <div class="section-block">
      <h3>Images à insérer dans le montage (${(images || []).length})</h3>
      <div class="file-drop" id="image-drop">Cliquer pour ajouter une image (jpg, png)</div>
      <input type="file" id="image-input" accept="image/*" class="hidden" />
      <div class="upload-list">
        ${(images || []).map(i => `<div class="upload-chip">🖼️ ${escapeHtml(i.label || i.storage_path.split('/').pop())}</div>`).join('') || '<span style="color:var(--text-dim); font-size:12px;">Aucune image fournie.</span>'}
      </div>
    </div>

    <div class="section-block">
      <h3>Historique de publication</h3>
      <div class="pub-log">
        ${(pubs && pubs.length) ? pubs.map(p => `
          <div class="pub-log-row">
            <span class="status-dot" style="background:${statusColor(p.status)}"></span>
            <span class="date">${formatDate(p.published_at)}</span>
            <span style="flex:1;">${escapeHtml(p.title || '—')}</span>
            <span style="color:var(--text-dim); font-size:11px;">${statusLabel(p.status)}</span>
          </div>
        `).join('') : '<span style="color:var(--text-dim); font-size:13px;">Aucune publication pour le moment.</span>'}
      </div>
    </div>
  `;

  document.getElementById('btn-publish-now').addEventListener('click', () => publishNow(c.id));
  document.getElementById('btn-edit').addEventListener('click', () => openChannelModal(c));
  const connectBtn = document.getElementById('btn-oauth-connect');
  if (connectBtn) connectBtn.addEventListener('click', () => startOAuth(c));

  document.getElementById('music-drop').addEventListener('click', () => document.getElementById('music-input').click());
  document.getElementById('music-input').addEventListener('change', (e) => uploadFile(e, c.id, 'music'));
  document.getElementById('image-drop').addEventListener('click', () => document.getElementById('image-input').click());
  document.getElementById('image-input').addEventListener('change', (e) => uploadFile(e, c.id, 'images'));
}

function renderPipeline(todayPub, c) {
  const steps = [
    { key: 'script', label: 'Script écrit' },
    { key: 'voice', label: 'Voix générée' },
    { key: 'render', label: 'Montage' },
    { key: 'publish', label: c.platform === 'tiktok' && !c.tiktok_audited ? 'Publié (privé)' : 'Publié' },
  ];
  // Sans job en cours détectable en direct depuis le navigateur, on déduit l'état
  // à partir de la ligne "publications" du jour : soit rien (attente), soit terminé, soit échec.
  let stateIndex = -1;
  let blocked = false;
  if (todayPub) {
    if (todayPub.status === 'failed') { stateIndex = 3; blocked = true; }
    else { stateIndex = 3; }
  }
  return `
    <div class="pipeline-track">
      ${steps.map((s, i) => {
        let cls = '';
        if (blocked && i === stateIndex) cls = 'blocked';
        else if (i <= stateIndex) cls = 'done';
        else if (i === stateIndex + 1) cls = '';
        return `
          <div class="pipeline-node ${cls}">
            <div class="pipeline-line"></div>
            <div class="dot"></div>
            <div class="label">${s.label}</div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function statusColor(status) {
  if (status === 'published') return 'var(--success)';
  if (status === 'private_pending_tiktok_audit') return 'var(--accent)';
  return 'var(--danger)';
}
function statusLabel(status) {
  if (status === 'published') return 'Publié';
  if (status === 'private_pending_tiktok_audit') return 'Privé (audit TikTok requis)';
  return 'Échec';
}

// ---------- Actions ----------
async function publishNow(channelId) {
  setTicker('Déclenchement de la publication…');
  const res = await fetch('/.netlify/functions/trigger-publish', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ channel_id: channelId })
  }).catch(() => null);
  setTicker(res && res.ok ? 'Publication lancée — repasse dans quelques minutes' : 'Échec du déclenchement, vérifie les logs GitHub Actions');
}

function startOAuth(c) {
  const startUrl = c.platform === 'youtube' ? YOUTUBE_OAUTH_START : TIKTOK_OAUTH_START;
  window.location.href = `${startUrl}?channel_id=${c.id}`;
}

async function uploadFile(e, channelId, kind) {
  const file = e.target.files[0];
  if (!file) return;
  const path = `${channelId}/${Date.now()}_${file.name}`;
  const bucket = kind === 'music' ? 'music' : 'images';
  const { error } = await supabaseClient.storage.from(bucket).upload(path, file);
  if (error) { alert("Échec de l'upload : " + error.message); return; }
  const table = kind === 'music' ? 'music_tracks' : 'user_images';
  await supabaseClient.from(table).insert({ channel_id: channelId, storage_path: path, label: file.name });
  renderChannelPanel(channelId);
}

// ---------- Modale nouvelle chaîne / édition ----------
const modal = document.getElementById('channel-modal');
let editingChannel = null;
let modalPlatform = 'youtube';

document.getElementById('add-channel-btn').addEventListener('click', () => openChannelModal(null));
document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-cancel').addEventListener('click', closeModal);

document.querySelectorAll('.seg-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    modalPlatform = btn.dataset.platform;
    document.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('youtube-connect-block').classList.toggle('hidden', modalPlatform !== 'youtube');
    document.getElementById('tiktok-connect-block').classList.toggle('hidden', modalPlatform !== 'tiktok');
  });
});

function openChannelModal(c) {
  editingChannel = c;
  document.getElementById('modal-title').textContent = c ? 'Modifier la fiche' : 'Connecter une chaîne';
  document.getElementById('f-display_name').value = c ? c.display_name : '';
  document.getElementById('f-niche').value = c ? c.niche : '';
  document.getElementById('f-gameplay_query').value = c ? c.gameplay_query : '';
  document.getElementById('f-weekly_long_video').checked = c ? c.weekly_long_video : false;
  modalPlatform = c ? c.platform : 'youtube';
  document.querySelectorAll('.seg-btn').forEach(b => b.classList.toggle('active', b.dataset.platform === modalPlatform));
  document.getElementById('youtube-connect-block').classList.toggle('hidden', modalPlatform !== 'youtube');
  document.getElementById('tiktok-connect-block').classList.toggle('hidden', modalPlatform !== 'tiktok');
  modal.classList.remove('hidden');
}
function closeModal() { modal.classList.add('hidden'); }

document.getElementById('modal-save').addEventListener('click', async () => {
  const payload = {
    platform: modalPlatform,
    display_name: document.getElementById('f-display_name').value.trim(),
    niche: document.getElementById('f-niche').value.trim(),
    gameplay_query: document.getElementById('f-gameplay_query').value.trim(),
    weekly_long_video: document.getElementById('f-weekly_long_video').checked,
  };
  if (!payload.display_name || !payload.niche || !payload.gameplay_query) {
    alert('Merci de remplir au moins le nom, la niche et le mot-clé gameplay.');
    return;
  }
  if (editingChannel) {
    await supabaseClient.from('channels').update(payload).eq('id', editingChannel.id);
  } else {
    await supabaseClient.from('channels').insert(payload);
  }
  closeModal();
  await loadChannels();
  renderRail();
  setTicker('Fiche enregistrée');
});

// ---------- Utils ----------
function escapeHtml(str) {
  return (str || '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m]));
}
function isToday(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
}
