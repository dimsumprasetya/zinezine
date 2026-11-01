#!/usr/bin/env python3
"""Cari video YouTube dan verifikasi lewat oEmbed.

Pemakaian: python tools/ytsearch.py "Nama Band Judul Lagu" ["kueri lain" ...]
Mencetak ID | judul | kanal untuk lima hasil teratas tiap kueri. Pilih hanya video
dari kanal artis, label resmi, VEVO, atau kanal "- Topic" resmi; jangan pakai
cover, remix, atau upload penggemar. Tiap ID yang dipilih harus lolos oEmbed
(dicetak "oembed OK").
"""
import re, sys, json, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding='utf-8')
UA = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.9'}


def search(q):
    u = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(q)
    h = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read().decode('utf-8', 'ignore')
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', h, re.S)
    out = []
    if not m:
        return out

    def walk(o):
        if isinstance(o, dict):
            v = o.get('videoRenderer')
            if v and len(out) < 5:
                t = ''.join(r.get('text', '') for r in v['title']['runs'])
                ch = ''.join(r.get('text', '') for r in v.get('ownerText', {}).get('runs', []))
                out.append((v['videoId'], t, ch))
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(json.loads(m.group(1)))
    return out


def oembed(i):
    u = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote('https://www.youtube.com/watch?v=' + i, safe='')
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25))
        return 'oembed OK: %s | %s' % (d.get('title'), d.get('author_name'))
    except Exception as e:
        return 'oembed GAGAL: %s' % e


for q in sys.argv[1:]:
    print('##', q)
    for i, t, ch in search(q):
        print(' ', i, '|', t, '|', ch, '|', oembed(i))
