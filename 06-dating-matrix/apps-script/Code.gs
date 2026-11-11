/**
 * The Dating Matrix: Google Apps Script backend.
 * Serves the quiz as a web app and stores every finished quiz in a Google Sheet.
 * Run setup() once from the editor to authorize and create the Sheet.
 */
var SHEET_NAME = 'Responses';
var HEADERS = ['id', 'finished', 'name', 'into', 'type', 'hearts_pick', 'most_compatible', 'source', 'json'];

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('The Dating Matrix')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** Run once from the editor: authorizes the script and creates the responses Sheet. */
function setup() {
  var sh = sheet_();
  Logger.log('Responses Sheet: ' + sh.getParent().getUrl());
}

function sheet_() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('SHEET_ID');
  var ss = null;
  if (id) { try { ss = SpreadsheetApp.openById(id); } catch (e) { ss = null; } }
  if (!ss) {
    ss = SpreadsheetApp.create('Dating Matrix Responses');
    props.setProperty('SHEET_ID', ss.getId());
  }
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.getSheets()[0];
    sh.setName(SHEET_NAME);
  }
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
  }
  return sh;
}

function isOwner_() {
  var active = Session.getActiveUser().getEmail();
  var owner = Session.getEffectiveUser().getEmail();
  return !!active && active === owner;
}

function cell_(v, n) {
  v = String(v == null ? '' : v).slice(0, n || 200);
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

/** Called by the page on load. */
function getSession() {
  return { isOwner: isOwner_() };
}

/** Saves (or replaces) one response. Anyone can save their own quiz; only the owner can add answer codes. */
function saveResponse(id, json) {
  if (!/^[A-Za-z0-9_-]{6,64}$/.test(String(id))) throw new Error('Bad id');
  if (typeof json !== 'string' || json.length > 60000) throw new Error('Response too large');
  var d = JSON.parse(json);
  if (!d || typeof d !== 'object' || !Array.isArray(d.w) || typeof d.p !== 'object') throw new Error('Bad response');
  if (d.source === 'code' && !isOwner_()) throw new Error('Only the quiz owner can add answer codes');
  if (d.source !== 'code') d.source = 'quiz';
  var row = [id, cell_(d.at || new Date().toISOString(), 40), cell_(d.n, 40), cell_(d.into, 8), cell_(d.type, 60),
    cell_(d.heart, 40), cell_(d.algo, 40), d.source, JSON.stringify(d)];
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sh = sheet_();
    var last = sh.getLastRow();
    if (last > 1) {
      var ids = sh.getRange(2, 1, last - 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) {
        if (String(ids[i][0]) === id) { sh.getRange(i + 2, 1, 1, row.length).setValues([row]); return true; }
      }
    }
    sh.appendRow(row);
    return true;
  } finally {
    lock.releaseLock();
  }
}

/** Owner only: every saved response, for the dashboard. */
function listResponses() {
  if (!isOwner_()) throw new Error('Only the quiz owner can see responses.');
  var sh = sheet_();
  var last = sh.getLastRow();
  if (last < 2) return [];
  return sh.getRange(2, 1, last - 1, HEADERS.length).getValues()
    .filter(function (r) { return r[0]; })
    .map(function (r) { return { id: String(r[0]), json: String(r[8]) }; });
}
