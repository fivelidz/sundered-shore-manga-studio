// Phone Panel Reviewer — installable PWA front-end over the same editor API.
// Reuses GET/POST /api/episode/<id>. Optimised for one-thumb review:
//   pick best of 3 (swipe), big approve/reject buttons, reject-reason chips, autosave.
// The desktop editor (../index.html) is untouched and still works.

const $ = (s, el = document) => el.querySelector(s);
const FAULT = ['hands/fingers', 'face drift', 'wrong character', 'text artifact', 'palette off', 'anatomy', 'style drift', 'composition'];

let EP = null, EPID = null, FILTER = 'unreviewed', saveT = null;

async function api(p, o) { const r = await fetch(p, o); if (!r.ok) throw new Error(r.status); return r.json(); }

function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.classList.add('show');
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('show'), 1400);
}

function saveSoon() {
  clearTimeout(saveT);
  saveT = setTimeout(async () => {
    try { await api(`/api/episode/${EPID}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(EP) }); }
    catch (e) { toast('save failed'); }
    progress();
  }, 500);
}

function progress() {
  const ps = EP.panels;
  const rendered = ps.filter(p => p.variants.length).length;
  const ok = ps.filter(p => p.approved).length;
  const fl = ps.filter(p => p.flagged).length;
  $('#prog').textContent = `${ok}✓ ${fl}⚑ · ${rendered}/${ps.length} imgs`;
}

function el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }

function visible(p) {
  if (FILTER === 'all') return true;
  if (FILTER === 'approved') return p.approved;
  if (FILTER === 'flagged') return p.flagged;
  if (FILTER === 'unreviewed') return !p.approved && !p.flagged;
  return true;
}

function dialogueBlock(p) {
  const d = el('div', 'dlg');
  // legacy single caption support
  const lines = [];
  if (Array.isArray(p.dialogue) && p.dialogue.length) lines.push(...p.dialogue);
  if (p.caption) lines.push({ type: 'caption', speaker: p.caption_pov || '', text: p.caption });
  if (!lines.length) { d.appendChild(el('div', 'none', 'no dialogue scripted yet')); return d; }
  lines.forEach(l => {
    const row = el('div', 'dl ' + (l.type || 'speech'));
    const who = (l.speaker || (l.type === 'sfx' ? 'sfx' : l.type === 'caption' ? 'caption' : '')).toLowerCase();
    row.appendChild(el('div', 'who ' + who, (l.speaker || l.type || '').toUpperCase()));
    row.appendChild(el('div', 'tx', l.text || ''));
    d.appendChild(row);
  });
  return d;
}

function card(p) {
  const c = el('div', 'card' + (p.approved ? ' approved' : '') + (p.flagged ? ' flagged' : ''));
  const badge = p.approved ? '<span class="badge ok">approved</span>' : p.flagged ? '<span class="badge fl">flagged</span>' : '';
  c.appendChild(el('div', 'chead', `<span class="n">#${String(p.panel).padStart(2, '0')}</span><span class="beat">${p.scroll_beat || ''}</span>${badge}`));

  if (p.variants.length) {
    const wrap = el('div', 'vtag');
    const img = el('img', 'cimg'); img.loading = 'lazy';
    img.src = `/episodes/${EPID}/${p.variants[Math.min(p.selected_variant, p.variants.length - 1)].file}`;
    img.onclick = () => openVariants(p);
    wrap.appendChild(img);
    wrap.appendChild(el('div', 'count', `${p.variants.length} variants — tap to choose`));
    c.appendChild(wrap);
  } else {
    c.appendChild(el('div', 'cimg-ph', 'rendering… (pull to refresh)'));
  }

  c.appendChild(dialogueBlock(p));

  // approve / reject
  const act = el('div', 'act');
  const ap = el('button', 'approve' + (p.approved ? ' on' : ''), '✓ Approve');
  const rj = el('button', 'reject' + (p.flagged ? ' on' : ''), '⚑ Reject');
  const reason = el('div', 'reason' + (p.flagged ? ' show' : ''));
  ap.onclick = () => { p.approved = !p.approved; if (p.approved) p.flagged = false; sync(); };
  rj.onclick = () => { p.flagged = !p.flagged; if (p.flagged) p.approved = false; sync(); };
  function sync() { redraw(); saveSoon(); }
  act.append(ap, rj); c.appendChild(act);

  // reject reason: chips + free text
  const chips = el('div', 'chips');
  FAULT.forEach(f => {
    const ch = el('span', 'chip', f);
    ch.onclick = () => { p.note = (p.note ? p.note + '; ' : '') + f; p.flagged = true; p.approved = false; redraw(); saveSoon(); toast('reason: ' + f); };
    chips.appendChild(ch);
  });
  const inp = el('input'); inp.placeholder = 'why regenerate? (feeds the prompt fix)'; inp.value = p.note || '';
  inp.oninput = () => { p.note = inp.value; saveSoon(); };
  reason.append(chips, inp);
  c.appendChild(reason);
  return c;
}

function redraw() {
  const deck = $('#deck'); deck.innerHTML = '';
  const shown = EP.panels.filter(visible);
  if (!shown.length) { deck.appendChild(el('div', 'empty', FILTER === 'unreviewed' ? 'All reviewed 🎉' : 'Nothing here.')); progress(); return; }
  shown.forEach(p => deck.appendChild(card(p)));
  progress();
}

/* ---- variant chooser: swipeable full-screen ---- */
let OVP = null, OVI = 0;
function openVariants(p) {
  OVP = p; OVI = p.selected_variant || 0;
  $('#ov').classList.remove('hidden');
  $('#ov-title').textContent = `Panel ${p.panel} — swipe to compare ${p.variants.length}`;
  renderSlides();
}
function renderSlides() {
  const stage = $('#ov-stage'); stage.innerHTML = '';
  OVP.variants.forEach((v, i) => {
    const s = el('div', 'slide');
    s.style.transform = `translateX(${(i - OVI) * 100}%)`;
    s.innerHTML = `<img src="/episodes/${EPID}/${v.file}"><div class="vlabel">v${i + 1} · ${v.model.split('/').pop()}</div>`;
    stage.appendChild(s);
  });
  const dots = $('#ov-dots'); dots.innerHTML = '';
  OVP.variants.forEach((_, i) => dots.appendChild(el('div', 'dot' + (i === OVI ? ' on' : ''))));
}
function go(d) { OVI = Math.max(0, Math.min(OVP.variants.length - 1, OVI + d)); renderSlides(); }

function bindSwipe() {
  const stage = $('#ov-stage'); let x0 = null;
  stage.addEventListener('touchstart', e => x0 = e.touches[0].clientX, { passive: true });
  stage.addEventListener('touchend', e => {
    if (x0 == null) return; const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1); x0 = null;
  });
}

async function loadEpisode(id) { EPID = id; EP = await api('/api/episode/' + id); redraw(); }

async function boot() {
  bindSwipe();
  $('#ov-pick').onclick = () => { OVP.selected_variant = OVI; $('#ov').classList.add('hidden'); redraw(); saveSoon(); toast('variant v' + (OVI + 1) + ' selected'); };
  $('#ov-x').onclick = () => $('#ov').classList.add('hidden');

  $('#filters').querySelectorAll('button').forEach(b => b.onclick = () => {
    $('#filters .active')?.classList.remove('active'); b.classList.add('active');
    FILTER = b.dataset.f; redraw(); window.scrollTo(0, 0);
  });

  const { episodes } = await api('/api/episodes');
  const sel = $('#ep'); sel.innerHTML = '';
  episodes.forEach(e => sel.appendChild(new Option(`${e.title} (${e.rendered})`, e.id)));
  sel.onchange = () => loadEpisode(sel.value);
  if (episodes.length) loadEpisode(episodes[0].id);

  // pull-to-refresh (light): top overscroll re-fetches images
  let py = 0;
  document.addEventListener('touchstart', e => { if (window.scrollY === 0) py = e.touches[0].clientY; }, { passive: true });
  document.addEventListener('touchend', async e => {
    if (py && window.scrollY === 0 && e.changedTouches[0].clientY - py > 90) {
      const keep = {}; EP.panels.forEach(p => keep[p.panel] = { a: p.approved, f: p.flagged, n: p.note, s: p.selected_variant });
      const fresh = await api('/api/episode/' + EPID);
      fresh.panels.forEach(p => { const k = keep[p.panel]; if (k) { p.approved = k.a; p.flagged = k.f; p.note = k.n; p.selected_variant = k.s; } });
      EP = fresh; redraw(); toast('refreshed');
    }
    py = 0;
  });

  // PWA install
  let deferred = null;
  window.addEventListener('beforeinstallprompt', e => { e.preventDefault(); deferred = e; $('#install').hidden = false; });
  $('#install').onclick = async () => { if (deferred) { deferred.prompt(); deferred = null; $('#install').hidden = true; } };
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => { });
}
boot();
