#!/usr/bin/env python3
"""Tag genre/kota dan blok "Mirip dengan" untuk zinezine.

Jalankan dari akar repo, SETELAH tools/volume.py dan SEBELUM tools/seo.py:
    python tools/tags.py

Data ada di tools/tags.json: { "<id-artikel>": {"genre": ["Punk"], "kota": ["Bandung"], "keluarga": ["Rock"]} }
Isi hanya genre/kota yang memang disebut di artikelnya (jangan menebak).
- Menyisipkan blok <!--TAGS-START-->...<!--TAGS-END--> di tiap artikel ber-tag (sebelum div.related).
- Tag yang dipakai >= 2 artikel menjadi tautan ke /tag/<slug>/ (halaman statis dibuat di sini);
  tag yang dipakai 1 artikel hanya ditampilkan sebagai teks.
- "Mirip dengan": hingga 3 artikel ber-tag lain dengan tag terbanyak yang sama (kota=1, genre=2, keluarga=1).
Aman dijalankan berulang kali.
"""
import html, json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://zinezine.online'
NAME = 'zinezine'


def rd(p):
    with open(os.path.join(ROOT, p), encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def text(h):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h))).strip()


esc = lambda s: html.escape(s, quote=True)

tags = json.load(open(os.path.join(ROOT, 'tools', 'tags.json'), encoding='utf-8'))
src = rd('index.html')
nl = '\r\n' if '\r\n' in src else '\n'
src = src.replace('\r\n', '\n')

arts = {}
for m in re.finditer(r'<article class="post" id="([^"]+)"[^>]*>(.*?)</article>', src, re.S):
    pid, body = m.groups()
    h1 = re.search(r'<h1>(.*?)</h1>', body, re.S)
    lede = re.search(r'<p class="post-lede">(.*?)</p>', body, re.S)
    arts[pid] = (text(h1.group(1)) if h1 else pid, text(lede.group(1)) if lede else '')
tags = {k: v for k, v in tags.items() if k in arts}

# pemakaian tiap tag
use = {}
for pid, t in tags.items():
    for kind in ('genre', 'kota'):
        for name in t.get(kind, []):
            use.setdefault((kind, name), []).append(pid)
linked = {k for k, v in use.items() if len(v) >= 2}


def score(a, b):
    ta, tb = tags[a], tags[b]
    sc = 0
    sc += len(set(ta.get('kota', [])) & set(tb.get('kota', [])))
    sc += 2 * len(set(ta.get('genre', [])) & set(tb.get('genre', [])))
    sc += len(set(ta.get('keluarga', [])) & set(tb.get('keluarga', [])))
    return sc


def chip(kind, name):
    if (kind, name) in linked:
        return f'<a class="tg tg-{kind}" href="/tag/{slug(name)}/">{esc(name)}</a>'
    return f'<span class="tg tg-{kind}">{esc(name)}</span>'


def block(pid):
    t = tags[pid]
    chips = [chip('genre', g) for g in t.get('genre', [])] + [chip('kota', k) for k in t.get('kota', [])]
    out = '<!--TAGS-START--><div class="tagbox">'
    if chips:
        out += '<div class="tagrow"><span class="lbl">Tag</span>' + ''.join(chips) + '</div>'
    sim = sorted(((score(pid, o), o) for o in tags if o != pid), key=lambda x: (-x[0], x[1]))
    sim = [o for s, o in sim if s > 0][:3]
    if sim:
        out += ('<div class="similar"><span class="lbl">Mirip dengan</span><ul>' +
                ''.join(f'<li><a href="#{o}">{esc(arts[o][0])}</a></li>' for o in sim) + '</ul></div>')
    return out + '</div><!--TAGS-END-->'


def patch(m):
    head, pid, body, tail = m.group(1), m.group(2), m.group(3), m.group(4)
    body = re.sub(r'<!--TAGS-START-->.*?<!--TAGS-END-->', '', body, flags=re.S)
    if pid in tags:
        b = block(pid)
        k = body.find('<div class="related">')
        if k < 0:
            k = body.rfind('<p><a class="back"')
        body = (body[:k] + b + body[k:]) if k >= 0 else (body + b)
    return head + body + tail


src = re.sub(r'(?s)(<article class="post" id="([^"]+)"[^>]*>)(.*?)(</article>)',
             patch, src)

# CSS satu kali
css_add = ('/* tag dan mirip dengan */\n'
           '.tagbox{margin:26px 0 0}\n'
           '.tagrow,.similar{margin:0 0 14px}\n'
           '.tagrow .lbl,.similar .lbl{display:block;margin-bottom:6px}\n'
           '.tg{display:inline-block;margin:0 6px 6px 0;padding:3px 10px;border:2px solid currentColor;font-family:var(--f-type);font-size:.78rem;text-decoration:none;color:inherit}\n'
           'a.tg:hover{background:var(--sun);color:#15161C}\n'
           '.similar ul{margin:0;padding-left:1.1em}\n'
           '.similar li{margin:0 0 4px}\n')
if '/* tag dan mirip dengan */' not in src:
    k = src.rfind('</style>')
    src = src[:k] + css_add + src[k:]
wr('index.html', src.replace('\n', nl) if nl == '\r\n' else src)

# halaman tag statis
styles = re.findall(r'<style>(.*?)</style>', src, re.S)
css = '\n'.join(styles)
ap = os.path.join(ROOT, 'tools', 'analytics.txt')
code = open(ap, encoding='utf-8').read().strip() if os.path.exists(ap) else ''
analytics = ('<script data-goatcounter="https://%s.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' % code
             if re.fullmatch(r'[a-z0-9-]+', code) else '')
import shutil
shutil.rmtree(os.path.join(ROOT, 'tag'), ignore_errors=True)
made = 0
for (kind, name), pids in sorted(use.items()):
    if (kind, name) not in linked:
        continue
    s = slug(name)
    url = f'{SITE}/tag/{s}/'
    label = ('Kota ' if kind == 'kota' else 'Genre ') + name
    title = f'{label}: band dan rilisan di {NAME}'
    desc = f'Artikel zinezine bertag {name}: ' + ', '.join(arts[p][0] for p in pids[:3]) + '.'
    desc = desc[:158]
    items = ''.join(f'<li><a href="/{p}/"><strong>{esc(arts[p][0])}</strong></a><br><span>{esc(arts[p][1])}</span></li>' for p in sorted(pids))
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', '@id': url, 'url': url, 'name': title, 'inLanguage': 'id-ID',
         'isPartOf': {'@type': 'WebSite', 'url': SITE + '/', 'name': NAME}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': NAME, 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': label, 'item': url}]}]}
    page = f'''<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta name="theme-color" content="#15161C">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False).replace('</', '<\\/')}</script>
{analytics}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Special+Elite&family=Work+Sans:wght@400;500;700&display=swap">
<style>
{css}
.tagpage{{max-width:760px;margin:0 auto;padding:28px 16px 48px}}
.tagpage ul{{list-style:none;padding:0}}
.tagpage li{{margin:0 0 16px;padding-bottom:14px;border-bottom:2px solid currentColor}}
</style>
</head>
<body>
<main class="tagpage"><p><a class="logo" href="/">zine<i>zine</i></a></p>
<h1>{esc(label)}</h1>
<p>{len(pids)} artikel zinezine dengan tag ini.</p>
<ul>{items}</ul>
<p><a href="/">&larr; Kembali ke beranda</a></p></main>
<footer><p>zinezine, berita band indie Indonesia dan dunia. <a href="/">Beranda</a> &middot; <a href="/#arsip">Arsip</a> &middot; <a href="mailto:rilis@zinezine.online">rilis@zinezine.online</a></p></footer>
</body>
</html>
'''
    wr(f'tag/{s}/index.html', page)
    made += 1
print(f'tags.py: {len(tags)} artikel ber-tag, {made} halaman tag')
