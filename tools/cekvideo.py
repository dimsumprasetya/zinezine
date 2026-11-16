"""Cek bahwa video YouTube di tiap artikel cocok dengan band/artisnya.
Jalankan dari akar repo: python tools/cekvideo.py
Keluar dengan kode 1 jika ada yang janggal (jangan commit sebelum beres).
"""
import glob, html, json, re, sys, urllib.parse, urllib.request

rows = []
for f in sorted(glob.glob('dd-*/index.html') + glob.glob('a-*/index.html')):
    s = open(f, encoding='utf-8').read()
    m = re.search(r'<figure class="ph"><img src="https://i\.ytimg\.com/vi/([\w-]{11})/[^"]*" alt="([^"]*)"', s)
    if m:
        rows.append((f.replace('\\', '/').split('/')[0], m.group(1), html.unescape(m.group(2))))

cache = {}


def judul(i):
    if i not in cache:
        u = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote('https://www.youtube.com/watch?v=' + i)
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read())
            cache[i] = (d['title'], d['author_name'])
        except Exception as e:
            cache[i] = ('ERR ' + str(e)[:40], '')
    return cache[i]


norm = lambda x: re.sub(r'[^a-z0-9]', '', x.lower())
bad = 0
pakai = {}
for slug, i, alt in rows:
    pakai.setdefault(i, []).append((slug, alt))
    t, a = judul(i)
    band = alt.split(',')[0].split(' - ')[0]
    lagu = re.sub(r'\s*\(.*', '', alt.split(',', 1)[1]) if ',' in alt else ''
    ok = (norm(band)[:6] in norm(t + a) or norm(band.split()[0]) in norm(t + a)
          or (len(norm(lagu)) >= 5 and norm(lagu) in norm(t)))
    if not ok:
        bad += 1
        print('CEK', slug, i, '| alt:', alt[:50], '| yt:', t[:60], '/', a)
for i, v in pakai.items():
    bands = {a.split(',')[0] for _, a in v}
    if len(bands) > 1:
        bad += 1
        print('ID SAMA dipakai band berbeda:', i, v)
print(len(rows), 'artikel dicek,', bad, 'janggal')
sys.exit(1 if bad else 0)
