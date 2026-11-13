#!/usr/bin/env python3
"""Bangun aset SEO zinezine dari index.html.

Dijalankan dari akar repo setelah index.html diperbarui:
    python tools/seo.py

Menghasilkan:
  - /<id>/index.html   halaman statis per artikel (judul, deskripsi, canonical, OG, JSON-LD)
  - /img/<kunci>.jpg   foto beranda yang tadinya tertanam base64
  - /sitemap.xml, /robots.txt, /feed.xml, /404.html
  - blok <head> SEO di index.html (di antara penanda SEO-START dan SEO-END)
Aman dijalankan berulang kali.
"""
import base64, datetime, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://zinezine.online'
NAME = 'zinezine'
TODAY = datetime.date.today().isoformat()
HOME_TITLE = 'zinezine: Berita Band Indie Indonesia dan Dunia, Rilisan Baru, Kalender Festival'
HOME_DESC = ('Berita band indie Indonesia dan dunia: rilisan baru, band lama yang masih jalan, '
             'daftar dengar, dan kalender konser serta festival. Diperbarui tiap hari.')


def analytics_snippet():
    # kode GoatCounter (mis. 'zinezine' untuk zinezine.goatcounter.com) ada di tools/analytics.txt; kosong = tidak dipasang
    fp = os.path.join(ROOT, 'tools', 'analytics.txt')
    code = open(fp, encoding='utf-8').read().strip() if os.path.exists(fp) else ''
    if not re.fullmatch(r'[a-z0-9-]+', code):
        return ''
    return ('<script data-goatcounter="https://%s.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' % code)


ANALYTICS = analytics_snippet()


def rd(p):
    with open(os.path.join(ROOT, p), encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def text(h):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h))).strip()


def esc(s):
    return html.escape(s, quote=True)


def clip(s, n):
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n - 1].rsplit(' ', 1)[0].rstrip(',;:.') + '…'


def jld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


src = rd('index.html')
nl = '\r\n' if '\r\n' in src else '\n'
src = src.replace('\r\n', '\n')

# ---- CSS (semua blok style kecuali yang pertama, yang hanya reset awal) ----
styles = re.findall(r'<style>(.*?)</style>', src, re.S)
css = '\n'.join(styles)

# ---- gambar tertanam ----
m = re.search(r'var IMGS=', src)
imgs = {}
if m:
    imgs, _ = json.JSONDecoder().raw_decode(src, m.end())
for k, v in imgs.items():
    mm = re.match(r'data:image/(jpeg|png|webp);base64,(.*)$', v, re.S)
    if not mm:
        continue
    ext = {'jpeg': 'jpg', 'png': 'png', 'webp': 'webp'}[mm.group(1)]
    imgs[k] = f'/img/{k}.{ext}'
    p = os.path.join(ROOT, 'img', f'{k}.{ext}')
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(base64.b64decode(mm.group(2)))

# ---- artikel ----
posts = []
for pm in re.finditer(r'<article class="post" id="([^"]+)"[^>]*>(.*?)</article>', src, re.S):
    posts.append((pm.group(1), pm.group(2)))
ids = {pid for pid, _ in posts}

dates_path = os.path.join(ROOT, 'tools', 'seo-dates.json')
dates = json.load(open(dates_path, encoding='utf-8')) if os.path.exists(dates_path) else {}
for pid, _ in posts:
    dates.setdefault(pid, TODAY)
json.dump(dates, open(dates_path, 'w', encoding='utf-8'), indent=1, sort_keys=True)


def absimg(u):
    if u.startswith('/'):
        return SITE + u
    return u


def fix_links(h):
    def link(mm):
        t = mm.group(1)
        if t in ids:
            return f'href="/{t}/"'
        if t == 'atas':
            return 'href="/"'
        return f'href="/#{t}"'
    h = re.sub(r'href="#([^"]*)"', link, h)
    h = re.sub(r'data-img="([^"]+)"', lambda mm: f'src="{imgs.get(mm.group(1), "/og.png")}"', h)
    return h


def drop_embeds(h):
    i = h.find('<div class="embeds">')
    if i < 0:
        return h
    depth, j = 0, i
    for t in re.finditer(r'<(/?)div\b', h[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            j = i + t.end()
            j = h.find('>', j) + 1
            break
    block = h[i:j]
    items = []
    for em in re.finditer(r'data-kind="(yt|sp)" data-id="([^"]+)".*?<strong>(.*?)</strong>', block, re.S):
        kind, eid, title = em.groups()
        url = (f'https://www.youtube.com/watch?v={eid}' if kind == 'yt' else f'https://open.spotify.com/{eid}')
        items.append(f'<li><strong>{title}</strong><a href="{url}" target="_blank" rel="noopener">{"YouTube" if kind == "yt" else "Spotify"}</a></li>')
    new = ('<div class="listen"><span class="lbl">Putar</span><ul>' + ''.join(items) + '</ul></div>') if items else ''
    return h[:i] + new + h[j:]


FOOT = ('<footer><p>zinezine, berita band indie Indonesia dan dunia. '
        '<a href="/">Beranda</a> &middot; <a href="/#arsip">Arsip</a> &middot; '
        '<a href="mailto:rilis@zinezine.online">rilis@zinezine.online</a></p></footer>')

pages = []  # (id, title, desc, date, image)
for pid, body in posts:
    if pid == 'arsip':
        continue
    h1 = re.search(r'<h1>(.*?)</h1>', body, re.S)
    title = text(h1.group(1)) if h1 else pid
    lede = re.search(r'<p class="post-lede">(.*?)</p>', body, re.S)
    if lede:
        desc = text(lede.group(1))
    else:
        pb = re.search(r'<div class="post-body"><p>(.*?)</p>', body, re.S)
        desc = text(pb.group(1)) if pb else HOME_DESC
    desc = clip(desc, 158)
    fig = re.search(r'<figure class="ph">.*?<img ([^>]*)>', body, re.S)
    img = absimg('/og.png')
    if fig:
        a = fig.group(1)
        di = re.search(r'data-img="([^"]+)"', a)
        si = re.search(r'\bsrc="([^"]+)"', a)
        if di and di.group(1) in imgs:
            img = absimg(imgs[di.group(1)])
        elif si and si.group(1).startswith('http'):
            img = si.group(1)
    is_vol = pid.startswith('vol-')
    url = f'{SITE}/{pid}/'
    date = dates[pid]
    page_title = clip(f'{title} | {NAME}', 70) if not is_vol else f'{title} | Arsip {NAME}'
    art = body
    art = drop_embeds(art)
    art = fix_links(art)
    graph = {
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'CollectionPage' if is_vol else 'NewsArticle',
                '@id': url + '#artikel',
                'mainEntityOfPage': {'@type': 'WebPage', '@id': url},
                'headline': clip(title, 110),
                'description': desc,
                'image': [img],
                'datePublished': date,
                'dateModified': TODAY if date != TODAY else date,
                'inLanguage': 'id-ID',
                'author': {'@type': 'Organization', 'name': 'Redaksi zinezine', 'url': SITE + '/'},
                'publisher': {'@type': 'Organization', 'name': NAME, 'url': SITE + '/',
                              'logo': {'@type': 'ImageObject', 'url': SITE + '/og.png'}},
            },
            {
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': NAME, 'item': SITE + '/'},
                    {'@type': 'ListItem', 'position': 2, 'name': title, 'item': url},
                ],
            },
        ],
    }
    page = f'''<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/favicon.svg">
<link rel="alternate" type="application/rss+xml" title="zinezine" href="/feed.xml">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{NAME}">
<meta property="og:locale" content="id_ID">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(clip(title, 90))}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(img)}">
<meta property="article:published_time" content="{date}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(clip(title, 70))}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(img)}">
<meta name="theme-color" content="#15161C">
{jld(graph)}
{ANALYTICS}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Special+Elite&family=Work+Sans:wght@400;500;700&display=swap">
<style>
{css}
.post[hidden]{{display:block!important}}
</style>
</head>
<body>
<div id="reader" class="wrap"><article class="post" id="{pid}">{art}</article></div>
{FOOT}
</body>
</html>
'''
    page = page.replace(' hidden>', '>')
    wr(f'{pid}/index.html', page)
    pages.append((pid, title, desc, date, img, is_vol))

# ---- sitemap, robots, feed, 404 ----
urls = [f'<url><loc>{SITE}/</loc><lastmod>{TODAY}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>']
for pid, title, desc, date, img, is_vol in sorted(pages, key=lambda x: x[3], reverse=True):
    pr = '0.5' if is_vol else '0.8'
    urls.append(f'<url><loc>{SITE}/{pid}/</loc><lastmod>{date}</lastmod><changefreq>{"weekly" if is_vol else "monthly"}</changefreq><priority>{pr}</priority></url>')
tag_dir = os.path.join(ROOT, 'tag')
if os.path.isdir(tag_dir):
    for tg in sorted(os.listdir(tag_dir)):
        if os.path.exists(os.path.join(tag_dir, tg, 'index.html')):
            urls.append(f'<url><loc>{SITE}/tag/{tg}/</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.4</priority></url>')
wr('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>\n')
wr('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')

items = []
for pid, title, desc, date, img, is_vol in sorted([p for p in pages if not p[5]], key=lambda x: x[3], reverse=True)[:30]:
    pub = datetime.datetime.fromisoformat(date).strftime('%a, %d %b %Y 00:00:00 +0700')
    items.append(f'<item><title>{esc(title)}</title><link>{SITE}/{pid}/</link><guid isPermaLink="true">{SITE}/{pid}/</guid>'
                 f'<pubDate>{pub}</pubDate><description>{esc(desc)}</description></item>')
wr('feed.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>zinezine</title>'
   f'<link>{SITE}/</link><description>{esc(HOME_DESC)}</description><language>id-id</language>\n' + '\n'.join(items) + '\n</channel></rss>\n')

wr('404.html', f'''<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Halaman tidak ditemukan | {NAME}</title><meta name="robots" content="noindex">
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#15161C;color:#E8E9E3;font-family:system-ui,sans-serif;text-align:center}}a{{color:#FF3D7F;font-weight:700}}</style></head>
<body><div><h1>Halaman tidak ditemukan</h1><p><a href="/">Kembali ke zinezine</a></p></div></body></html>
''')

# ---- blok SEO beranda ----
home_items = [p for p in sorted(pages, key=lambda x: x[3], reverse=True) if not p[5]][:20]
home_graph = {
    '@context': 'https://schema.org',
    '@graph': [
        {'@type': 'WebSite', '@id': SITE + '/#situs', 'url': SITE + '/', 'name': NAME, 'inLanguage': 'id-ID',
         'description': HOME_DESC, 'publisher': {'@id': SITE + '/#org'}},
        {'@type': ['Organization', 'NewsMediaOrganization'], '@id': SITE + '/#org', 'name': NAME, 'url': SITE + '/',
         'logo': {'@type': 'ImageObject', 'url': SITE + '/og.png'},
         'email': 'rilis@zinezine.online', 'description': HOME_DESC},
        {'@type': 'ItemList', 'name': 'Kabar terbaru zinezine',
         'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/{p[0]}/', 'name': p[1]}
                             for i, p in enumerate(home_items)]},
    ],
}
block = f'''<!--SEO-START-->
<title>{esc(HOME_TITLE)}</title>
<meta name="description" content="{esc(HOME_DESC)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<link rel="canonical" href="{SITE}/">
<link rel="alternate" type="application/rss+xml" title="zinezine" href="/feed.xml">
<meta property="og:locale" content="id_ID">
<meta name="theme-color" content="#15161C">
{jld(home_graph)}
{ANALYTICS}
<!--SEO-END-->'''
if '<!--SEO-START-->' in src:
    src = re.sub(r'<!--SEO-START-->.*?<!--SEO-END-->', lambda _: block, src, flags=re.S)
else:
    src = src.replace('<title>zinezine</title>', '', 1)
    src = re.sub(r'<meta name="description" content="[^"]*">\n', '', src, count=1)
    src = src.replace('<link rel="icon"', block + '\n<link rel="icon"', 1)
src = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(HOME_TITLE)}">', src, count=1)
src = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(HOME_DESC)}">', src, count=1)
wr('index.html', src.replace('\n', nl) if nl == '\r\n' else src)
print(f'seo.py: {len(pages)} halaman, sitemap {len(urls)} url, {len(items)} item feed, {len(imgs)} gambar')
