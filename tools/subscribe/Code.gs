/**
 * zinezine: langganan email (double opt-in) dengan Google Sheet.
 * Dipasang sebagai Apps Script TERIKAT pada Google Sheet milik pemilik zinezine.
 * Deploy: Terapkan > Deployment baru > Aplikasi web; Jalankan sebagai: Saya; Akses: Siapa saja.
 * Sheet 'Pelanggan' dibuat otomatis. Kolom: email, status, token, dibuat, dikonfirmasi, berhenti, sumber.
 * status: pending | confirmed | unsubscribed
 * Tidak ada rahasia di file ini. Sheet tetap privat milik pemilik.
 */
var SHEET = 'Pelanggan';
var SHEET_ID = '';           // ID Google Sheet (wajib untuk skrip mandiri)
var SITE = 'https://zinezine.online/';
var MAX_PER_DAY = 300;      // batas pendaftaran baru per hari (pelindung spam)
var RESEND_MIN = 10;        // menit minimal sebelum konfirmasi boleh dikirim ulang

function sheet_() {
  var ss = SHEET_ID ? SpreadsheetApp.openById(SHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
  var s = ss.getSheetByName(SHEET);
  if (!s) {
    s = ss.insertSheet(SHEET);
    s.appendRow(['email', 'status', 'token', 'dibuat', 'dikonfirmasi', 'berhenti', 'sumber']);
    s.setFrozenRows(1);
  }
  return s;
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function page_(title, msg) {
  var h = '<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>' + title + '</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#15161C;color:#E8E9E3;font-family:system-ui,sans-serif;text-align:center;padding:24px}' +
    'h1{font-size:1.6rem}a{color:#FF3D7F;font-weight:700}</style></head><body><div><h1>' + title + '</h1><p>' + msg + '</p><p><a href="' + SITE + '">Kembali ke zinezine</a></p></div></body></html>';
  return HtmlService.createHtmlOutput(h).setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DENY);
}

function findRow_(s, col, value) {
  var last = s.getLastRow();
  if (last < 2) return -1;
  var vals = s.getRange(2, col, last - 1, 1).getValues();
  for (var i = 0; i < vals.length; i++) {
    if (String(vals[i][0]).toLowerCase() === value) return i + 2;
  }
  return -1;
}

function baseUrl_() {
  return ScriptApp.getService().getUrl();
}

function sendConfirm_(email, token) {
  var link = SITE + 'konfirmasi/?a=confirm&t=' + encodeURIComponent(token);
  var out = SITE + 'konfirmasi/?a=unsub&t=' + encodeURIComponent(token);
  var html = '<p>Halo,</p><p>Seseorang (semoga kamu) mendaftarkan email ini untuk kabar band indie dari <b>zinezine</b>.</p>' +
    '<p><a href="' + link + '" style="background:#FF3D7F;color:#15161C;padding:10px 16px;text-decoration:none;font-weight:700">Ya, konfirmasi langganan saya</a></p>' +
    '<p>Kalau bukan kamu, abaikan saja email ini; tidak akan ada email lanjutan. Berhenti kapan pun: <a href="' + out + '">berhenti berlangganan</a>.</p>' +
    '<p>zinezine, berita band indie Indonesia dan dunia. ' + SITE + '</p>';
  MailApp.sendEmail({
    to: email,
    subject: 'Konfirmasi langganan zinezine',
    htmlBody: html,
    name: 'zinezine',
    replyTo: 'rilis@zinezine.online'
  });
}

// Pendaftaran dari formulir di situs (POST form-urlencoded)
function doPost(e) {
  var p = (e && e.parameter) || {};
  var okResp = json_({ ok: true });            // jawaban selalu sama agar alamat tidak bisa ditebak
  if (p.website) return okResp;                // honeypot terisi = bot
  var email = String(p.email || '').trim().toLowerCase();
  if (email.length > 120 || !/^[^\s@,;<>()"]{1,64}@[^\s@,;<>()"]+\.[^\s@,;<>()"]{2,}$/.test(email)) {
    return json_({ ok: false, error: 'email' });
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    var cache = CacheService.getScriptCache();
    var key = 'n' + Utilities.formatDate(new Date(), 'Asia/Jakarta', 'yyyyMMdd');
    var n = Number(cache.get(key) || 0);
    if (n >= MAX_PER_DAY) return okResp;
    var s = sheet_();
    var row = findRow_(s, 1, email);
    var now = new Date();
    if (row < 0) {
      var token = Utilities.getUuid();
      s.appendRow([email, 'pending', token, now, '', '', String(p.src || 'situs').slice(0, 40)]);
      sendConfirm_(email, token);
      cache.put(key, String(n + 1), 86400);
    } else {
      var status = s.getRange(row, 2).getValue();
      var made = new Date(s.getRange(row, 4).getValue());
      var token2 = s.getRange(row, 3).getValue();
      if (status === 'unsubscribed') {
        token2 = Utilities.getUuid();
        s.getRange(row, 2, 1, 5).setValues([['pending', token2, now, '', '']]);
        sendConfirm_(email, token2);
        cache.put(key, String(n + 1), 86400);
      } else if (status === 'pending' && (now - made) > RESEND_MIN * 60000) {
        s.getRange(row, 4).setValue(now);
        sendConfirm_(email, token2);
        cache.put(key, String(n + 1), 86400);
      }
      // confirmed: tidak melakukan apa pun
    }
  } finally {
    lock.releaseLock();
  }
  return okResp;
}

// Tautan di email: konfirmasi atau berhenti
function doGet(e) {
  var p = (e && e.parameter) || {};
  if (p.json) return jsonGet_(p);
  var t = String(p.t || '').toLowerCase();
  if (!/^[0-9a-f-]{36}$/.test(t) || (p.a !== 'confirm' && p.a !== 'unsub')) {
    return page_('Tautan tidak valid', 'Tautan ini tidak dikenali atau sudah kedaluwarsa.');
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    var s = sheet_();
    var row = findRow_(s, 3, t);
    if (row < 0) return page_('Tautan tidak valid', 'Tautan ini tidak dikenali atau sudah kedaluwarsa.');
    var now = new Date();
    if (p.a === 'confirm') {
      if (s.getRange(row, 2).getValue() !== 'unsubscribed') {
        s.getRange(row, 2).setValue('confirmed');
        s.getRange(row, 5).setValue(now);
        s.getRange(row, 6).setValue('');
      }
      return page_('Langganan dikonfirmasi', 'Terima kasih! Kamu akan menerima kabar band indie dari zinezine.');
    }
    s.getRange(row, 2).setValue('unsubscribed');
    s.getRange(row, 6).setValue(now);
    return page_('Kamu sudah berhenti berlangganan', 'Email kamu tidak akan menerima kabar zinezine lagi.');
  } finally {
    lock.releaseLock();
  }
}

// Dipanggil dari halaman konfirmasi di situs (tanpa halaman Google, aman untuk banyak akun)
function jsonGet_(p) {
  var t = String(p.t || '').toLowerCase();
  if (!/^[0-9a-f-]{36}$/.test(t) || (p.a !== 'confirm' && p.a !== 'unsub')) return json_({ ok: false });
  var lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    var s = sheet_();
    var row = findRow_(s, 3, t);
    if (row < 0) return json_({ ok: false });
    var now = new Date();
    if (p.a === 'confirm') {
      if (s.getRange(row, 2).getValue() !== 'unsubscribed') {
        s.getRange(row, 2).setValue('confirmed');
        s.getRange(row, 5).setValue(now);
        s.getRange(row, 6).setValue('');
      }
    } else {
      s.getRange(row, 2).setValue('unsubscribed');
      s.getRange(row, 6).setValue(now);
    }
    return json_({ ok: true, a: p.a });
  } finally {
    lock.releaseLock();
  }
}
