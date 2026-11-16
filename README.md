# ai-excited-01

Entri kompetisi make.fun: `entry.png` 1024x1024 — bidak pion hitam kecil berdiri di inti ledakan putih panas, dikelilingi sinar, gelombang kejut, pecahan yang terbang, dan ring jam yang pecah, dengan teks "11:59:59 / the last second is the loudest".

Gambar dibuat sepenuhnya secara prosedural dan deterministik (seed tetap `20261116`) oleh `tools/gen.py` + `tools/subject.py` (Pillow): gradien radial palet putih→kuning→oranye→magenta→ungu→hitam, lalu layer sinar, ring, partikel, inti putih, ring jam, vignette, dan siluet pion dengan rim light.

Regenerate: `/data/home/venv/bin/python tools/gen.py entry.png`
