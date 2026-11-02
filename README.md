# zinezine

Berita band indie Indonesia dan dunia. Situs statis satu halaman (`index.html`), dilayani lewat GitHub Pages.

Foto memakai lisensi bebas dari Wikimedia Commons, kredit ada di bawah tiap foto. Ringkasan berita ditulis ulang redaksi dan menaut ke sumber aslinya.

## SEO

`python tools/seo.py` (dijalankan tiap update) membuat halaman statis per artikel (`/<id>/`), `sitemap.xml`, `feed.xml`, `robots.txt`, `404.html`, foto di `img/`, dan blok SEO beranda (judul, deskripsi, canonical, JSON-LD) di antara penanda `SEO-START` dan `SEO-END` di `index.html`. Jangan edit file hasilnya dengan tangan.
