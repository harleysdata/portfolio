/**
 * GTA Women's Circle — Google Apps Script backend.
 * Data lives in the Google Sheet this script is attached to.
 * Run setup() once, then Deploy > New deployment > Web app.
 */

const SHEETS = {
  Members: ['id','tokenHash','nickname','showIg','ig','area','fsa','age','interests','eventTypes','availability','budget','visible','status','joinedAt','updatedAt'],
  Events: ['id','title','date','endDate','time','venue','area','type','price','priceNote','link','notes','submittedBy','createdAt'],
  Submissions: ['id','submitterId','title','date','endDate','time','venue','area','type','price','priceNote','link','notes','createdAt'],
  RSVPs: ['memberId','eventId','status','updatedAt'],
  Reports: ['id','reporterId','aboutId','reason','note','at','resolved']
};

/* ---------- setup (run once from the editor) ---------- */
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('Open this script from your Google Sheet (Extensions > Apps Script), not from script.google.com.');
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());
  Object.keys(SHEETS).forEach(name => {
    let s = ss.getSheetByName(name) || ss.insertSheet(name);
    s.getRange(1, 1, s.getMaxRows(), SHEETS[name].length).setNumberFormat('@'); // keep dates/handles as plain text
    s.getRange(1, 1, 1, SHEETS[name].length).setValues([SHEETS[name]]).setFontWeight('bold');
    s.setFrozenRows(1);
  });
  const def = ss.getSheetByName('Sheet1');
  if (def && def.getLastRow() === 0 && ss.getSheets().length > 1) ss.deleteSheet(def);

  const props = PropertiesService.getScriptProperties();
  if (!props.getProperty('JOIN_CODE')) props.setProperty('JOIN_CODE', 'CHANGE-ME'); // set your own in Project Settings > Script properties
  if (!props.getProperty('ADMIN_KEY')) props.setProperty('ADMIN_KEY', Utilities.getUuid().slice(0, 12));

  if (read_('Events').length === 0) {
    append_('Events', {
      id: 'distillery-2026', title: 'Distillery Winter Village (Toronto Christmas Market)',
      date: '2026-11-12', endDate: '2027-01-03', venue: 'Distillery Historic District, 55 Mill St',
      area: 'Toronto – Downtown', type: 'Holiday & seasonal', price: 'free',
      priceNote: 'Free before 4 pm daily, all day Mon–Wed until Dec 13, and Thursdays in November (not opening night). Tickets from $16 at other times, bought online in advance.',
      link: 'https://thedistillerywintervillage.com', notes: 'Easy first meetup: go on a free Mon–Wed evening as a group.',
      submittedBy: 'admin', createdAt: new Date().toISOString()
    });
  }
  Logger.log('Join code: ' + props.getProperty('JOIN_CODE'));
  Logger.log('Admin key: ' + props.getProperty('ADMIN_KEY'));
}

/* ---------- web app entry ---------- */
function doGet(e) {
  const t = HtmlService.createTemplateFromFile('Index');
  t.isAdmin = !!(e && e.parameter && e.parameter.admin === '1');
  return t.evaluate()
    .setTitle("GTA Women's Circle")
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL); // lets you embed it in Google Sites
}

/* ---------- sheet helpers ---------- */
function ss_() {
  const id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  return id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
}
function sh_(n) {
  const s = ss_().getSheetByName(n);
  if (!s) throw new Error('Setup has not been run yet: open Apps Script and run setup().');
  return s;
}
function read_(n) {
  const v = sh_(n).getDataRange().getValues(); const h = v.shift() || [];
  return v.map((r, i) => { const o = { _row: i + 2 }; h.forEach((k, j) => o[k] = r[j] === null ? '' : String(r[j])); return o; });
}
function cell_(x) { const s = x == null ? '' : String(x); return /^[=+\-@]/.test(s) ? "'" + s : s; } // block formula injection
function rowOf_(n, o) { return SHEETS[n].map(k => cell_(o[k])); }
function append_(n, o) { sh_(n).appendRow(rowOf_(n, o)); }
function write_(n, o) { sh_(n).getRange(o._row, 1, 1, SHEETS[n].length).setValues([rowOf_(n, o)]); }
function delWhere_(n, pred) { read_(n).filter(pred).sort((a, b) => b._row - a._row).forEach(r => sh_(n).deleteRow(r._row)); }
function withLock_(fn) { const l = LockService.getScriptLock(); l.waitLock(15000); try { return fn(); } finally { l.releaseLock(); } }
function hash_(t) { return Utilities.base64Encode(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, 'gtacircle:' + t)); }
function id_() { return Utilities.getUuid().replace(/-/g, '').slice(0, 10); }
function txt_(s, max) { return String(s == null ? '' : s).trim().slice(0, max || 200); }
function list_(a) { return (Array.isArray(a) ? a : []).slice(0, 40).map(x => txt_(x, 40)).filter(Boolean).join('; '); }
function split_(s) { return s ? s.split('; ').filter(Boolean) : []; }
function me_(token) { if (!token) return null; const h = hash_(token); return read_('Members').find(m => m.tokenHash === h) || null; }
function needMember_(token) { const m = me_(token); if (!m || m.status !== 'approved') throw new Error('Your profile is not approved yet.'); return m; }
function needAdmin_(key) { if (!key || key !== PropertiesService.getScriptProperties().getProperty('ADMIN_KEY')) throw new Error('That admin key is not right.'); }

function publicMember_(m) {
  return { id: m.id, nickname: m.nickname, area: m.area, fsa: m.fsa, age: m.age,
    interests: split_(m.interests), eventTypes: split_(m.eventTypes), availability: split_(m.availability),
    budget: m.budget, ig: m.showIg === 'true' ? m.ig : '' };
}
function ownMember_(m) { const p = publicMember_(m); p.ig = m.ig; p.showIg = m.showIg === 'true'; p.visible = m.visible !== 'false'; p.status = m.status; return p; }
function event_(e) { const o = {}; SHEETS.Events.forEach(k => o[k] = e[k]); return o; }

/* ---------- member API ---------- */
function getState(token) {
  const me = me_(token);
  const out = { me: me && me.status !== 'removed' ? ownMember_(me) : null, removed: !!(me && me.status === 'removed'),
    members: [], events: [], rsvps: {}, myRsvps: {}, mySubs: [] };
  if (!me || me.status !== 'approved') {
    if (me) out.mySubs = read_('Submissions').filter(s => s.submitterId === me.id).map(s => ({ title: s.title, date: s.date }));
    return out;
  }
  const members = read_('Members').filter(m => m.status === 'approved');
  const ok = {}; members.forEach(m => ok[m.id] = true);
  out.members = members.filter(m => m.id !== me.id && m.visible !== 'false').map(publicMember_);
  out.events = read_('Events').map(event_);
  read_('RSVPs').forEach(r => {
    if (!ok[r.memberId]) return;
    if (r.memberId === me.id) out.myRsvps[r.eventId] = r.status;
    (out.rsvps[r.eventId] = out.rsvps[r.eventId] || []).push({ memberId: r.memberId, status: r.status });
  });
  out.mySubs = read_('Submissions').filter(s => s.submitterId === me.id).map(s => ({ title: s.title, date: s.date }));
  return out;
}

function saveProfile(token, joinCode, p) {
  return withLock_(() => {
    const ig = txt_(p.ig, 31).replace(/^@/, ''), fsa = txt_(p.fsa, 3).toUpperCase();
    if (!txt_(p.nickname, 40)) throw new Error('Add a nickname.');
    if (p.showIg && !/^[A-Za-z0-9._]{1,30}$/.test(ig)) throw new Error('Instagram handles use letters, numbers, dots and underscores only.');
    if (fsa && !/^[A-Z]\d[A-Z]$/.test(fsa)) throw new Error('Postal code area should look like L5B.');
    if (!p.consent) throw new Error('Please agree to the group rules.');
    const now = new Date().toISOString();
    const fields = { nickname: txt_(p.nickname, 40), showIg: p.showIg ? 'true' : 'false', ig: p.showIg ? ig : '',
      area: txt_(p.area, 60), fsa: fsa, age: txt_(p.age, 10), interests: list_(p.interests), eventTypes: list_(p.eventTypes),
      availability: list_(p.availability), budget: txt_(p.budget, 10), visible: p.visible === false ? 'false' : 'true', updatedAt: now };
    let me = me_(token);
    if (me) {
      if (me.status === 'removed') throw new Error('This profile was removed by the admin.');
      Object.assign(me, fields); write_('Members', me);
      return { token: token };
    }
    const code = PropertiesService.getScriptProperties().getProperty('JOIN_CODE') || '';
    if (txt_(joinCode, 40).toUpperCase() !== code.toUpperCase()) throw new Error('That join code is not right. Ask the group admin for it.');
    const newToken = Utilities.getUuid() + Utilities.getUuid();
    append_('Members', Object.assign({ id: id_(), tokenHash: hash_(newToken), status: 'pending', joinedAt: now }, fields));
    return { token: newToken };
  });
}

function deleteProfile(token) {
  return withLock_(() => {
    const me = me_(token); if (!me) return true;
    delWhere_('RSVPs', r => r.memberId === me.id);
    delWhere_('Members', m => m.id === me.id);
    return true;
  });
}

function rsvp(token, eventId, status) {
  return withLock_(() => {
    const me = needMember_(token);
    const existing = read_('RSVPs').find(r => r.memberId === me.id && r.eventId === eventId);
    if (existing && existing.status === status) { delWhere_('RSVPs', r => r._row === existing._row); return true; }
    if (existing) { existing.status = status; existing.updatedAt = new Date().toISOString(); write_('RSVPs', existing); return true; }
    if (['interested', 'going'].indexOf(status) < 0) throw new Error('Unknown RSVP.');
    append_('RSVPs', { memberId: me.id, eventId: txt_(eventId, 40), status: status, updatedAt: new Date().toISOString() });
    return true;
  });
}

function cleanEvent_(e) {
  const link = txt_(e.link, 300);
  if (link && !/^https?:\/\//.test(link)) throw new Error('Links need to start with https://');
  if (!txt_(e.title, 100) || !/^\d{4}-\d{2}-\d{2}$/.test(txt_(e.date, 10))) throw new Error('Add an event name and date.');
  return { title: txt_(e.title, 100), date: txt_(e.date, 10), endDate: txt_(e.endDate, 10), time: txt_(e.time, 30),
    venue: txt_(e.venue, 100), area: txt_(e.area, 60), type: txt_(e.type, 40), price: e.price === 'paid' ? 'paid' : 'free',
    priceNote: txt_(e.priceNote, 120), link: link, notes: txt_(e.notes, 400), createdAt: new Date().toISOString() };
}
function submitEvent(token, e) {
  return withLock_(() => {
    const me = needMember_(token);
    append_('Submissions', Object.assign({ id: id_(), submitterId: me.id }, cleanEvent_(e)));
    return true;
  });
}

function report(token, aboutId, reason, note) {
  return withLock_(() => {
    const me = needMember_(token);
    append_('Reports', { id: id_(), reporterId: me.id, aboutId: txt_(aboutId, 20), reason: txt_(reason, 60), note: txt_(note, 300), at: new Date().toISOString(), resolved: 'false' });
    return true;
  });
}

/* ---------- admin API ---------- */
function adminState(key) {
  needAdmin_(key);
  const members = read_('Members').filter(m => m.status !== 'removed');
  const names = {}; read_('Members').forEach(m => names[m.id] = m.nickname || 'member');
  const counts = {}; read_('RSVPs').forEach(r => counts[r.eventId] = (counts[r.eventId] || 0) + 1);
  return {
    members: members.map(m => Object.assign(ownMember_(m), { joinedAt: m.joinedAt })),
    submissions: read_('Submissions').map(s => Object.assign(event_(s), { id: s.id, from: names[s.submitterId] || 'member' })),
    reports: read_('Reports').map(r => ({ id: r.id, about: names[r.aboutId] || 'removed member', aboutId: r.aboutId, from: names[r.reporterId] || 'member', reason: r.reason, note: r.note, at: r.at, resolved: r.resolved === 'true' })),
    events: read_('Events').map(e => Object.assign(event_(e), { count: counts[e.id] || 0 }))
  };
}

function adminAction(key, action, arg) {
  needAdmin_(key);
  return withLock_(() => {
    if (action === 'approve' || action === 'remove') {
      const m = read_('Members').find(x => x.id === arg); if (!m) return true;
      if (action === 'approve') { m.status = 'approved'; write_('Members', m); return true; }
      delWhere_('RSVPs', r => r.memberId === m.id);
      // keep only a stub so the same device can't rejoin; personal details are wiped
      SHEETS.Members.forEach(k => { if (['id', 'tokenHash', 'joinedAt'].indexOf(k) < 0) m[k] = ''; });
      m.status = 'removed'; m.updatedAt = new Date().toISOString(); write_('Members', m);
      return true;
    }
    if (action === 'approveSub') {
      const s = read_('Submissions').find(x => x.id === arg); if (!s) return true;
      append_('Events', Object.assign(event_(s), { id: s.id, submittedBy: s.submitterId }));
      delWhere_('Submissions', x => x.id === arg); return true;
    }
    if (action === 'rejectSub') { delWhere_('Submissions', x => x.id === arg); return true; }
    if (action === 'resolveReport') { const r = read_('Reports').find(x => x.id === arg); if (r) { r.resolved = 'true'; write_('Reports', r); } return true; }
    if (action === 'deleteEvent') { delWhere_('Events', x => x.id === arg); delWhere_('RSVPs', r => r.eventId === arg); return true; }
    if (action === 'addEvent') { append_('Events', Object.assign({ id: id_(), submittedBy: 'admin' }, cleanEvent_(arg))); return true; }
    throw new Error('Unknown action.');
  });
}
