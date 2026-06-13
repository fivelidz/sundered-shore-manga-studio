// Manga Studio Editor — phone-scrollable manhwa review + edit.
// Per panel: click image -> variant chooser (3 generations, pick one) · approve ✓ ·
// flag for regen ⚑ with note (quick fault chips) · dialogue/lettering entries shown
// UNDER the image (content kept OUT of the image — FLUX letters badly; a second-pass
// system composites the text). Autosaves to the server after every change.

const $ = (s, el = document) => el.querySelector(s);
const FAULT_CHIPS = ['hands/fingers', 'face drift', 'wrong character look', 'text artifact', 'palette off', 'anatomy', 'style drift', 'composition'];
const DLG_TYPES = ['speech', 'thought', 'caption', 'sfx'];

let EP = null;        // episode json
let EPID = null;
let saveTimer = null;

async function api(path, opts) { const r = await fetch(path, opts); if (!r.ok) throw new Error(r.status); return r.json(); }

function saveSoon() {
  clearTimeout(saveTimer);
  setSaveState('…');
  saveTimer = setTimeout(async () => {
    try { await api(`/api/episode/${EPID}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(EP) }); setSaveState('saved'); }
    catch (e) { setSaveState('SAVE FAILED'); }
    renderProgress();
  }, 600);
}
function setSaveState(t) { let el = $('.savestate') || document.body.appendChild(Object.assign(document.createElement('div'), { className: 'savestate' })); el.textContent = t; }

function renderProgress() {
  const ps = EP.panels;
  const rendered = ps.filter(p => p.variants.length).length;
  const approved = ps.filter(p => p.approved).length;
  const flagged = ps.filter(p => p.flagged).length;
  $('#progress').textContent = `${EP.title} — ${rendered}/${ps.length} rendered · ${approved} approved · ${flagged} flagged`;
}

function el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }

function panelCard(p) {
  const card = el('div', 'panel' + (p.approved ? ' approved' : '') + (p.flagged ? ' flagged' : ''));
  card.appendChild(el('div', 'phead',
    `<span>#${String(p.panel).padStart(2, '0')}</span><span class="beat">${p.scroll_beat || ''}</span>` +
    `<span>${p.shot || ''} · ${p.aspect}</span><span class="vcount">${p.variants.length} var</span>`));

  // image (selected variant) — click opens variant chooser
  if (p.variants.length) {
    const img = el('img', 'pimg');
    img.loading = 'lazy';
    img.src = '/episodes/' + EPID + '/' + (p.variants[Math.min(p.selected_variant, p.variants.length - 1)].file);
    img.onclick = () => openOverlay(p);
    card.appendChild(img);
  } else {
    card.appendChild(el('div', 'pimg-placeholder', 'rendering… (auto-appears on reload)'));
  }

  // caption (the prose line) — POV colour-coded
  if (p.caption) {
    const cap = el('div', 'caption ' + (p.caption_pov || ''));
    cap.innerHTML = `<span class="who">${p.caption_pov || 'narration'}</span>${p.caption}`;
    card.appendChild(cap);
  }

  // dialogue/lettering list (second-pass content; shown UNDER the image)
  const dlg = el('div', 'dialogue');
  dlg.appendChild(el('div', 'dl-title', 'Lettering (second pass — kept out of the image)'));
  p.dialogue.forEach((d, i) => {
    const row = el('div', 'dl-entry');
    const type = el('select'); DLG_TYPES.forEach(t => type.appendChild(new Option(t, t, false, d.type === t)));
    type.onchange = () => { d.type = type.value; saveSoon(); };
    const spk = el('input', 'dl-speaker'); spk.placeholder = 'speaker'; spk.value = d.speaker || '';
    spk.oninput = () => { d.speaker = spk.value; saveSoon(); };
    const txt = el('input', 'dl-text'); txt.placeholder = 'text…'; txt.value = d.text || '';
    txt.oninput = () => { d.text = txt.value; saveSoon(); };
    const del = el('button', null, '✕'); del.onclick = () => { p.dialogue.splice(i, 1); redraw(); saveSoon(); };
    row.append(type, spk, txt, del); dlg.appendChild(row);
  });
  const add = el('button', 'dl-add', '+ add speech / thought / caption');
  add.onclick = () => { p.dialogue.push({ type: 'speech', speaker: '', text: '', anchor: 'auto' }); redraw(); saveSoon(); };
  dlg.appendChild(add);
  card.appendChild(dlg);

  // controls: approve / flag / note
  const ctr = el('div', 'controls');
  const ok = el('label', null, `<input type="checkbox" ${p.approved ? 'checked' : ''}> approve`);
  ok.querySelector('input').onchange = (e) => { p.approved = e.target.checked; if (p.approved) p.flagged = false; redraw(); saveSoon(); };
  const fl = el('label', null, `<input type="checkbox" class="flagbox" ${p.flagged ? 'checked' : ''}> flag for regen`);
  fl.querySelector('input').onchange = (e) => { p.flagged = e.target.checked; if (p.flagged) p.approved = false; redraw(); saveSoon(); };
  const note = el('input', 'note'); note.placeholder = 'note (what is wrong / what to change)'; note.value = p.note || '';
  note.oninput = () => { p.note = note.value; saveSoon(); };
  ctr.append(ok, fl, note);
  card.appendChild(ctr);

  // quick fault chips (append to note + auto-flag)
  const chips = el('div', 'chips');
  FAULT_CHIPS.forEach(c => {
    const ch = el('span', 'chip', c);
    ch.onclick = () => { p.note = (p.note ? p.note + '; ' : '') + c; p.flagged = true; p.approved = false; redraw(); saveSoon(); };
    chips.appendChild(ch);
  });
  card.appendChild(chips);
  return card;
}

function openOverlay(p) {
  const ov = $('#overlay'); ov.classList.remove('hidden');
  $('#overlay-title').textContent = `Panel ${p.panel} — pick the best generation (${p.variants.length} available)`;
  const row = $('#variant-row'); row.innerHTML = '';
  p.variants.forEach((v, i) => {
    const c = el('div', 'vcard' + (i === p.selected_variant ? ' selected' : ''));
    c.innerHTML = `<img src="/episodes/${EPID}/${v.file}"><div class="vlabel">v${i + 1} · ${v.model.split('/').pop()}</div>`;
    c.onclick = () => { p.selected_variant = i; ov.classList.add('hidden'); redraw(); saveSoon(); };
    row.appendChild(c);
  });
}

function redraw() {
  const strip = $('#strip'); strip.innerHTML = '';
  EP.panels.forEach(p => strip.appendChild(panelCard(p)));
  renderProgress();
}

async function loadEpisode(id) {
  EPID = id; EP = await api('/api/episode/' + id); redraw();
}

async function boot() {
  const { episodes } = await api('/api/episodes');
  const sel = $('#episode-select'); sel.innerHTML = '';
  episodes.forEach(e => sel.appendChild(new Option(`${e.title} (${e.rendered} imgs)`, e.id)));
  sel.onchange = () => loadEpisode(sel.value);
  $('#export-btn').onclick = () => {
    const blob = new Blob([JSON.stringify(EP, null, 2)], { type: 'application/json' });
    const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: EPID + '_episode.json' });
    a.click();
  };
  $('#overlay-close').onclick = () => $('#overlay').classList.add('hidden');
  if (episodes.length) loadEpisode(episodes[0].id);
  // auto-refresh images while the renderer is running
  setInterval(async () => { if (EP) { const fresh = await api('/api/episode/' + EPID); let changed = fresh.panels.reduce((n, p, i) => n + (p.variants.length !== EP.panels[i].variants.length ? 1 : 0), 0); if (changed) { const scroll = window.scrollY; fresh.panels.forEach((p, i) => { p.approved = EP.panels[i].approved; p.flagged = EP.panels[i].flagged; p.note = EP.panels[i].note; p.dialogue = EP.panels[i].dialogue; p.selected_variant = EP.panels[i].selected_variant; }); EP = fresh; redraw(); window.scrollTo(0, scroll); } } }, 30000);
}
boot();
