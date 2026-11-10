/**
 * Halloween Weekend Picker – Google Apps Script web app.
 * Two pages share one Google Sheet:
 *   /exec          → Weekend Picker (Fri–Sun Oct 16–18): which day, where, what kind of event
 *   /exec?p=night  → Night Picker (Fri Oct 30 + Sat Oct 31): going or not, when, where, vibe, which events
 * Votes go to the "Votes" / "Night Votes" tabs; the "Summary" / "Night Summary" tabs total them with formulas.
 * Set SHEET_ID below, then Deploy > New deployment > Web app (Execute as: Me, Access: Anyone).
 */
const SHEET_ID = 'YOUR_SHEET_ID';

const DAYS = ['fri', 'sat', 'sun'];
const DAY_NAMES = { fri: 'Fri', sat: 'Sat', sun: 'Sun' };
const HEAD = ['Updated', 'Name'];
DAYS.forEach(d => HEAD.push(DAY_NAMES[d] + ': when free', DAY_NAMES[d] + ': areas', DAY_NAMES[d] + ': kinds of event', DAY_NAMES[d] + ': picked events'));
HEAD.push('Comment', 'Voter key (do not edit)');
const KEY_COL = HEAD.length;          // last column
const SEP = ' | ';

const FREE = ['Daytime', 'Evening', 'Any time', "Can't make it"];
const AREAS = ['Downtown Toronto', 'Rest of Toronto', 'GTA', 'Day trip', 'Further afield'];
const KINDS = ['Scream park', 'Haunted house', 'Haunted trail', 'Farm, maze & pumpkins', 'Show, film or museum', 'Festival or market', 'Party', 'Escape room'];

function ss_() { return SpreadsheetApp.openById(SHEET_ID); }

function doGet(e) {
  if (e && e.parameter && e.parameter.p === 'night') return nightPage_();
  setup_();
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Halloween Weekend Picker')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** Runs automatically on first visit: creates the Votes tab and the Summary tab. */
function setup_() {
  const ss = ss_();
  let v = ss.getSheetByName('Votes');
  if (!v) {
    v = ss.getSheets()[0];
    v.setName('Votes');
  }
  if (v.getRange(1, 1).getValue() !== 'Updated') {
    v.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight('bold').setBackground('#2B2B2B').setFontColor('#FFFFFF').setWrap(true);
    v.setFrozenRows(1);
    v.setColumnWidths(1, HEAD.length, 150);
    v.setColumnWidth(2, 130);
    v.hideColumns(KEY_COL);
  }
  if (!ss.getSheetByName('Summary')) buildSummary_(ss);
}

/** A Summary tab built from COUNTIF formulas, so organisers can read totals straight from the sheet. */
function buildSummary_(ss) {
  const s = ss.insertSheet('Summary');
  const rows = [['Halloween weekend: group totals (updates automatically)', '', '', ''], ['', 'Friday Oct 16', 'Saturday Oct 17', 'Sunday Oct 18']];
  const col = (d, k) => { // column letter in Votes for day d, field k (0 free, 1 areas, 2 kinds, 3 events)
    const idx = 3 + DAYS.indexOf(d) * 4 + k; // 1-based
    return String.fromCharCode(64 + idx);
  };
  const line = (label, fn) => rows.push([label].concat(DAYS.map(fn)));
  line('People who voted for this day', d => `=COUNTA(Votes!${col(d, 0)}2:${col(d, 0)})`);
  line('Free that day', d => `=COUNTA(Votes!${col(d, 0)}2:${col(d, 0)})-COUNTIF(Votes!${col(d, 0)}2:${col(d, 0)},"Can't make it")`);
  rows.push(['', '', '', ''], ['When are people free?', '', '', '']);
  FREE.forEach(f => line(f, d => `=COUNTIF(Votes!${col(d, 0)}2:${col(d, 0)},"${f}")`));
  rows.push(['', '', '', ''], ['Which area?', '', '', '']);
  AREAS.forEach(a => line(a, d => `=COUNTIF(Votes!${col(d, 1)}2:${col(d, 1)},"*${a}*")`));
  rows.push(['', '', '', ''], ['What kind of event?', '', '', '']);
  KINDS.forEach(k => line(k, d => `=COUNTIF(Votes!${col(d, 2)}2:${col(d, 2)},"*${k}*")`));
  s.getRange(1, 1, rows.length, 4).setValues(rows);
  s.getRange(1, 1).setFontWeight('bold').setFontSize(14);
  s.getRange(2, 1, 1, 4).setFontWeight('bold').setBackground('#2B2B2B').setFontColor('#FFFFFF');
  rows.forEach((r, i) => { if (/\?$/.test(r[0])) s.getRange(i + 1, 1).setFontWeight('bold').setFontColor('#B9461A'); });
  s.setColumnWidth(1, 260);
  s.setColumnWidths(2, 3, 140);
  s.getRange(3, 2, rows.length - 2, 3).setHorizontalAlignment('center');
}

/** Strips line breaks and leading = + - @ so nothing a voter types can run as a spreadsheet formula. */
function clean_(s, max) { return String(s == null ? '' : s).replace(/[\r\n\t]+/g, ' ').replace(/^[=+\-@]+/, '').trim().slice(0, max || 200); }
/** Keeps only values from the allowed list. */
function pick_(arr, allowed) { return (Array.isArray(arr) ? arr : []).map(String).filter(x => allowed.indexOf(x) >= 0); }

/** Called from the page. Saves (or updates) one person's vote, then returns everyone's votes. */
function saveVote(vote) {
  const name = clean_(vote && vote.name, 40);
  const key = clean_(vote && vote.key, 60);
  if (!name) throw new Error('Please add your name first.');
  if (!/^[a-z0-9]{8,60}$/i.test(key)) throw new Error('Something went wrong. Reload the page and try again.');
  const row = [new Date(), name];
  DAYS.forEach(d => {
    const x = (vote.days && vote.days[d]) || {};
    const free = FREE.indexOf(x.free) >= 0 ? x.free : '';
    const off = free === "Can't make it";
    row.push(free,
      off ? '' : pick_(x.areas, AREAS).join(SEP),
      off ? '' : pick_(x.kinds, KINDS).join(SEP),
      off ? '' : (Array.isArray(x.events) ? x.events : []).slice(0, 3).map(e => clean_(e, 120)).join(SEP));
  });
  row.push(clean_(vote.comment, 300), key);

  const lock = LockService.getScriptLock();   // many people vote at once; one write at a time
  lock.waitLock(10000);
  try {
    setup_();
    const sh = ss_().getSheetByName('Votes');
    const last = sh.getLastRow();
    let target = 0;
    if (last >= 2) {
      const keys = sh.getRange(2, KEY_COL, last - 1, 1).getValues();
      for (let i = 0; i < keys.length; i++) if (keys[i][0] === key) { target = i + 2; break; }
    }
    if (!target) target = last + 1;            // new voter → new row; returning voter → overwrite their row
    sh.getRange(target, 1, 1, row.length).setValues([row]);
  } finally {
    lock.releaseLock();
  }
  return getVotes(key);
}

/** Called from the page. Returns everyone's votes (without anyone's private key). */
function getVotes(myKey) {
  const sh = ss_().getSheetByName('Votes');
  if (!sh || sh.getLastRow() < 2) return [];
  const data = sh.getRange(2, 1, sh.getLastRow() - 1, HEAD.length).getValues();
  const split = s => String(s || '').split(SEP).map(x => x.trim()).filter(Boolean);
  return data.filter(r => r[1]).map(r => {
    const out = { name: String(r[1]), me: !!myKey && r[KEY_COL - 1] === myKey, days: {}, comment: String(r[KEY_COL - 2] || '') };
    DAYS.forEach((d, i) => {
      const c = 2 + i * 4;
      out.days[d] = { free: String(r[c] || ''), areas: split(r[c + 1]), kinds: split(r[c + 2]), events: split(r[c + 3]) };
    });
    return out;
  });
}


/* ===================== Halloween Night Picker (Oct 30–31) ===================== */
const N_NIGHTS = ['fri', 'sat'];
const N_NAMES = { fri: 'Fri Oct 30', sat: 'Sat Oct 31' };
const N_HEAD = ['Updated', 'Name'];
N_NIGHTS.forEach(d => N_HEAD.push(N_NAMES[d] + ': when out', N_NAMES[d] + ': where', N_NAMES[d] + ': vibe', N_NAMES[d] + ': events'));
N_HEAD.push('Comment', 'Voter key (do not edit)');
const N_KEY_COL = N_HEAD.length;
const N_TIMES = ['Going', 'Maybe', "Can't make it", 'Early evening', 'Prime time', 'Late night', 'After hours'];
const N_AREAS = ['Downtown', 'Rest of Toronto', 'Happy to travel'];
const N_VIBES = ['Goth', 'Alt', 'Mainstream', 'Queer-friendly'];
// Event names must match the EVENTS list in Night.html (the server only accepts names from this list).
const N_EVENTS = { fri: ["Goth Zombie Prom: Devil's Night", "The Black Parade: Halloween Emo Night", "Rocky Horror Picture Show (live shadowcast)", "AGO Halloween Drag Bingo", "INFERNO Halloween Festival", "ASNM Halloween: Kanyon (NYC), Tony Price", "Classmatic (open till 4 AM)", "Damian Lazarus", "Cosmic Gate", "MORTEM", "Toronto Halloween Boat Party", "ROM After Dark: All Hallow's Eve (19+)", "The Seance @ 44 Toronto", "The Blood Moon Ball"], sat: ["Server Halloween Party", "Dungeon Dance: Halloween in the Grotto", "SPACETIME: A Trickster Halloween", "Rocky Horror Picture Show (live shadowcast)", "Halloween on Church", "Cafeteria Halloween: Invisible City x LYRIX", "The Blood Ball", "Haunted Halloween Rave (4 rooms)", "The Freaks Come Out (open till 4 AM)", "PRISM SCREAM: Halloween Circuit Party", "INFERNO Halloween Festival", "Ozmozis Halloween", "Steve Lawler: Halloween (21+)", "Kaskade", "Afterlife", "Halloween Dprtmnt 2026", "King Street Halloween Club Crawl", "Halloween Boat Party Cruise", "The Haunted Theatre", "ROM After Dark: Trick or Treat (19+)"] };

function nightPage_() {
  nightSetup_();
  return HtmlService.createHtmlOutputFromFile('Night')
    .setTitle('Halloween Night Picker')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function nightSetup_() {
  const ss = ss_();
  let v = ss.getSheetByName('Night Votes');
  if (!v) {
    v = ss.insertSheet('Night Votes');
    v.getRange(1, 1, 1, N_HEAD.length).setValues([N_HEAD]).setFontWeight('bold').setBackground('#2B2B2B').setFontColor('#FFFFFF').setWrap(true);
    v.setFrozenRows(1);
    v.setColumnWidths(1, N_HEAD.length, 170);
    v.setColumnWidth(6, 320); v.setColumnWidth(10, 320);
    v.hideColumns(N_KEY_COL);
  }
  const old = ss.getSheetByName('Night Summary');
  if (old && old.getRange(7, 1).getValue() !== 'Going') ss.deleteSheet(old);   // rebuild if the layout changed
  if (!ss.getSheetByName('Night Summary')) nightSummary_(ss);
}

function nightSummary_(ss) {
  const s = ss.insertSheet('Night Summary');
  const col = (d, k) => String.fromCharCode(64 + 3 + N_NIGHTS.indexOf(d) * 4 + k);
  const rows = [['Halloween weekend nights: group totals (updates automatically)', '', ''], ['', 'Fri Oct 30', 'Sat Oct 31']];
  const line = (label, fn) => rows.push([label].concat(N_NIGHTS.map(fn)));
  line('People who answered', d => `=COUNTA('Night Votes'!${col(d, 0)}2:${col(d, 0)})`);
  line('Going out', d => `=COUNTA('Night Votes'!${col(d, 0)}2:${col(d, 0)})-COUNTIF('Night Votes'!${col(d, 0)}2:${col(d, 0)},"Can't make it")`);
  rows.push(['', '', ''], ['When are people out?', '', '']);
  N_TIMES.forEach(t => line(t, d => `=COUNTIF('Night Votes'!${col(d, 0)}2:${col(d, 0)},"*${t}*")`));
  rows.push(['', '', ''], ['Where?', '', '']);
  N_AREAS.forEach(a => line(a, d => `=COUNTIF('Night Votes'!${col(d, 1)}2:${col(d, 1)},"*${a}*")`));
  rows.push(['', '', ''], ['Vibe?', '', '']);
  N_VIBES.forEach(a => line(a, d => `=COUNTIF('Night Votes'!${col(d, 2)}2:${col(d, 2)},"*${a}*")`));
  N_NIGHTS.forEach(d => {
    rows.push(['', '', ''], [N_NAMES[d] + ' events: people in', '', '']);
    N_EVENTS[d].forEach(n => {
      const r = ['  ' + n, '', ''];
      r[1 + N_NIGHTS.indexOf(d)] = `=COUNTIF('Night Votes'!${col(d, 3)}2:${col(d, 3)},"*${n.replace(/"/g, '""')}*")`;
      rows.push(r);
    });
  });
  s.getRange(1, 1, rows.length, 3).setValues(rows);
  s.getRange(1, 1).setFontWeight('bold').setFontSize(14);
  s.getRange(2, 1, 1, 3).setFontWeight('bold').setBackground('#2B2B2B').setFontColor('#FFFFFF');
  rows.forEach((r, i) => { if (/\?$|people in$/.test(r[0])) s.getRange(i + 1, 1).setFontWeight('bold').setFontColor('#B9461A'); });
  s.setColumnWidth(1, 340);
  s.setColumnWidths(2, 2, 130);
  s.getRange(3, 2, rows.length - 2, 2).setHorizontalAlignment('center');
}

/** Called from the night page. Saves (or updates) one person's picks, then returns everyone's. */
function saveNightVote(vote) {
  const name = clean_(vote && vote.name, 40);
  const key = clean_(vote && vote.key, 60);
  if (!name) throw new Error('Add your name at the top first.');
  if (!/^[a-z0-9]{8,60}$/i.test(key)) throw new Error('Something went wrong. Reload the page and try again.');
  const row = [new Date(), name];
  N_NIGHTS.forEach(d => {
    const x = (vote.nights && vote.nights[d]) || {};
    let times = pick_(x.times, N_TIMES);
    if (times.indexOf("Can't make it") >= 0) times = ["Can't make it"];
    const off = times[0] === "Can't make it";
    row.push(times.join(SEP),
      off ? '' : pick_(x.areas, N_AREAS).join(SEP),
      off ? '' : pick_(x.vibes, N_VIBES).join(SEP),
      off ? '' : pick_(x.events, N_EVENTS[d]).join(SEP));
  });
  row.push(clean_(vote.comment, 300), key);
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    nightSetup_();
    const sh = ss_().getSheetByName('Night Votes');
    const last = sh.getLastRow();
    let target = 0;
    if (last >= 2) {
      const keys = sh.getRange(2, N_KEY_COL, last - 1, 1).getValues();
      for (let i = 0; i < keys.length; i++) if (keys[i][0] === key) { target = i + 2; break; }
    }
    if (!target) target = last + 1;
    sh.getRange(target, 1, 1, row.length).setValues([row]);
  } finally {
    lock.releaseLock();
  }
  return getNightVotes(key);
}

/** Called from the night page. Returns everyone's picks (without anyone's private key). */
function getNightVotes(myKey) {
  const sh = ss_().getSheetByName('Night Votes');
  if (!sh || sh.getLastRow() < 2) return [];
  const data = sh.getRange(2, 1, sh.getLastRow() - 1, N_HEAD.length).getValues();
  const split = s => String(s || '').split(SEP).map(x => x.trim()).filter(Boolean);
  return data.filter(r => r[1]).map(r => {
    const out = { name: String(r[1]), me: !!myKey && r[N_KEY_COL - 1] === myKey, nights: {}, comment: String(r[N_KEY_COL - 2] || '') };
    N_NIGHTS.forEach((d, i) => {
      const c = 2 + i * 4;
      out.nights[d] = { times: split(r[c]), areas: split(r[c + 1]), vibes: split(r[c + 2]), events: split(r[c + 3]) };
    });
    return out;
  });
}
