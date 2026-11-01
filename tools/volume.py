#!/usr/bin/env python3
"""Kelola volume dan arsip zinezine, dan periksa gambar.

Pemakaian: python tools/volume.py index.html --date YYYY-MM-DD

- Volume terbit tiap minggu mulai Minggu 1 November 2026 (Vol. 01).
- Tiap artikel punya atribut data-vol. Artikel baru tanpa atribut itu masuk ke
  volume pada tanggal --date.
- Halaman #arsip dan #vol-NN dibangun ulang dari atribut itu (di antara penanda
  ARSIP-START/END), meta sampul diperbarui, tautan Arsip di menu dan footer
  dipastikan ada.
- Terakhir memeriksa gambar. Keluar dengan kode 1 jika ada artikel, kartu, atau
  slide tanpa gambar, dan hasil itu tidak boleh dipublikasikan.
"""
import re, sys, datetime

START = datetime.date(2026, 11, 1)
BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus',
         'September', 'Oktober', 'November', 'Desember']


def vol_of(d):
    return (d - START).days // 7 + 1


def rng(n):
    a = START + datetime.timedelta(days=7 * (n - 1))
    b = a + datetime.timedelta(days=6)
    if a.month == b.month:
        return '%d&ndash;%d %s %d' % (a.day, b.day, BULAN[a.month - 1], a.year)
    if a.year == b.year:
        return '%d %s&ndash;%d %s %d' % (a.day, BULAN[a.month - 1], b.day, BULAN[b.month - 1], a.year)
    return '%d %s %d&ndash;%d %s %d' % (a.day, BULAN[a.month - 1], a.year, b.day, BULAN[b.month - 1], b.year)


def main():
    path = sys.argv[1]
    d = datetime.date.fromisoformat(sys.argv[sys.argv.index('--date') + 1])
    cur = vol_of(d)
    s = open(path, encoding='utf-8').read()

    # buang halaman arsip lama
    s = re.sub(r'<!--ARSIP-START-->.*?<!--ARSIP-END-->', '', s, flags=re.S)

    # beri data-vol pada artikel yang belum punya
    def tag(m):
        if 'data-vol=' in m.group(0):
            return m.group(0)
        return '<article class="post" id="%s" data-vol="%02d" hidden>' % (m.group(1), cur)
    s = re.sub(r'<article class="post" id="([^"]+)"[^>]*>', tag, s)

    vols = {}
    missing = []
    for m in re.finditer(r'<article class="post" id="([^"]+)" data-vol="(\d+)" hidden>(.*?)</article>', s, re.S):
        sid, v, body = m.group(1), int(m.group(2)), m.group(3)
        lbl = re.search(r'<span class="lbl">(.*?)</span>', body, re.S)
        h1 = re.search(r'<h1>(.*?)</h1>', body, re.S)
        fig = re.search(r'<figure class="ph">.*?<img([^>]*)>', body, re.S)
        if not fig:
            missing.append('artikel ' + sid)
            continue
        at = fig.group(1)
        k = re.search(r'data-img="([^"]+)"', at)
        u = re.search(r'src="([^"]+)"', at)
        a = re.search(r'alt="([^"]*)"', at)
        img = '<img class="dph" %s alt="%s" loading="lazy">' % (
            ('data-img="%s"' % k.group(1)) if k else ('src="%s"' % u.group(1) if u else ''),
            a.group(1) if a else '')
        card = ('<li><a class="dd" href="#%s">%s<span class="dd-meta">%s</span>'
                '<strong class="dd-name">%s</strong><span class="dd-go">Baca &rarr;</span></a></li>'
                % (sid, img, lbl.group(1) if lbl else '', h1.group(1) if h1 else sid))
        vols.setdefault(v, []).append((card, img))

    pages = []
    idx = []
    for v in sorted(vols, reverse=True):
        cards = vols[v]
        n = len(cards)
        pages.append(
            '<article class="post" id="vol-%02d" hidden><nav class="nav" aria-label="Navigasi artikel">'
            '<a class="logo" href="#atas">zine<i>zine</i></a><a class="back" href="#arsip">&larr; Arsip</a></nav>'
            '<header class="post-head"><span class="lbl">Arsip &middot; Vol. %02d</span><h1>Vol. %02d</h1>'
            '<p class="post-lede">%s. %d artikel terbit pada volume ini.</p></header>'
            '<ul class="ddlist" style="margin:26px 0">%s</ul></article>'
            % (v, v, v, rng(v), n, ''.join(c[0] for c in cards)))
        idx.append('<li><a class="dd" href="#vol-%02d">%s<span class="dd-meta">%s</span>'
                   '<strong class="dd-name">Vol. %02d</strong><em class="dd-title">%d artikel</em>'
                   '<span class="dd-go">Buka &rarr;</span></a></li>' % (v, cards[0][1], rng(v), v, n))
    pages.append(
        '<article class="post" id="arsip" hidden><nav class="nav" aria-label="Navigasi artikel">'
        '<a class="logo" href="#atas">zine<i>zine</i></a><a class="back" href="#atas">&larr; Beranda</a></nav>'
        '<header class="post-head"><span class="lbl">Arsip</span><h1>Arsip Volume</h1>'
        '<p class="post-lede">Semua volume zinezine yang pernah terbit. Volume baru terbit tiap Minggu.</p></header>'
        '<ul class="ddlist" style="margin:26px 0">%s</ul></article>' % ''.join(idx))
    block = '<!--ARSIP-START-->' + ''.join(pages) + '<!--ARSIP-END-->'
    s = s.replace('<div id="reader" class="wrap">', '<div id="reader" class="wrap">' + block, 1)

    # meta sampul
    s = re.sub(r'<div class="meta lbl">.*?</div>',
               '<div class="meta lbl"><span>Vol. %02d</span><span>%s</span><span>Diperbarui tiap hari</span></div>' % (cur, rng(cur)),
               s, count=1, flags=re.S)
    # menu dan footer
    if 'href="#arsip">Arsip</a></li>' not in s:
        s = s.replace('<li><a href="#gigs">Kalender</a></li>',
                      '<li><a href="#gigs">Kalender</a></li>\n      <li><a href="#arsip">Arsip</a></li>', 1)
    if 'class="foot-arsip"' not in s:
        s = s.replace('</footer>', '<p class="foot-arsip"><a href="#arsip">Arsip semua volume</a></p>\n  </footer>', 1)

    # periksa gambar kartu dan slide
    for m in re.finditer(r'<a class="dd" href="#([^"]+)">(?!<img)', s):
        missing.append('kartu daftar dengar ' + m.group(1))
    for m in re.finditer(r'<article class="story">(?!<img)(.*?)</article>', s, re.S):
        h = re.search(r'href="#([^"]+)"', m.group(1))
        missing.append('kartu kabar ' + (h.group(1) if h else '?'))
    for m in re.finditer(r'<div class="slide (s-(?:ink|pink|sun|paper))">.*?href="#([^"]+)"', s, re.S):
        missing.append('slide ' + m.group(2))

    open(path, 'w', encoding='utf-8', newline='').write(s)
    print('Vol. %02d (%s), %d volume di arsip' % (cur, rng(cur).replace('&ndash;', '-'), len(vols)))
    if missing:
        print('TANPA GAMBAR (wajib diperbaiki sebelum publikasi):')
        for x in missing:
            print(' -', x)
        sys.exit(1)
    print('Semua artikel, kartu, dan slide punya gambar.')


if __name__ == '__main__':
    main()
