# Simulasi Puteran Jl. Dr. Setiabudi × Gerlong (Bandung)

Mikro-simulasi lalu lintas (**SUMO**) + tampilan **3D interaktif (Three.js)** dengan **mode kemudi**, untuk
LKM-2 Transportasi MSTR. Proyek ini menganalisis kemacetan akibat puteran di median baru (pagar stainless)
di mulut Jl. Gegerkalong Girang, lalu membandingkan solusinya.

## Cara menjalankan

| Langkah | Cara |
|---|---|
| 1. Instal paket (sekali saja) | klik dua kali `INSTAL_PAKET.bat` (atau `pip install -r requirements.txt`) |
| 2. Simulasi 3D + mode kemudi | klik dua kali `JALANKAN_SIMULASI_3D.bat` → browser membuka http://127.0.0.1:8000 |
| 3. Analisis angka (semua skenario) | klik dua kali `JALANKAN_ANALISIS.bat` → hasil di `results/ringkasan.md` + grafik PNG |

Di tampilan 3D: pilih skenario → **▶ Mulai**. Kamera: tombol preset atau seret mouse (klik kanan = geser, roda = zoom).
**Mode kemudi**: pilih jenis kendaraan & titik muncul → **Mulai kemudi**. Tombol: `W/↑` gas, `S/↓` rem/mundur,
`A D/← →` setir, `Spasi` rem tangan, `C` ganti kamera. Kendaraan Anda dimasukkan ke SUMO sehingga kendaraan lain
benar-benar bereaksi (mengerem, menunggu, tertahan).

Tautan langsung untuk presentasi, misalnya:
`http://127.0.0.1:8000/?mulai=S0&kamera=Bukaan%20A&cepat=5` atau `...?mulai=S2&kamera=Flyover%20(S2)`.
Halaman hasil: `http://127.0.0.1:8000/hasil.html`.

## Skenario

| Kode | Isi |
|---|---|
| **S0** Eksisting | Median pagar baru. Dari Lembang ke Gerlong harus putar balik di **bukaan A** (±35 m selatan mulut Gerlong) lalu belok kiri; median di depan Gerlong tertutup. Dari bawah putar balik di **bukaan B** (±105 m utara, dekat gerbang UPI). Truk/bus maju-mundur saat putar balik, angkot ngetem. |
| **Tahap 1** (murah) | S0 + larangan truk/bus putar balik + penertiban ngetem angkot. |
| **S1** APILL | Median dibuka di mulut Gerlong, **APILL 2 fase adaptif** (fase belok kanan 5–14 s sesuai antrean), lajur kanan arah turun 60 m jadi **lajur khusus belok kanan**, bukaan A ditutup, bukaan B tetap untuk kendaraan kecil, tertib ngetem. |
| **S2** U-turn layang | Putaran balik layang 480 m (dek ±7,5 m di atas jalan, kemiringan ≤5%, loop R 13 m ±200 m di selatan), mendarat 70 m sebelum Gerlong lalu belok kiri. Butuh pelebaran jalan di zona oprit & pembebasan lahan di loop. |

## Data & dasar realisme

- **Geometri**: OpenStreetMap (diunduh 19-11-2026; median baru sudah terpetakan), citra satelit Esri z19, Google Street View
  Des 2023 & Sep 2024, foto & video lapangan 19-11-2026 → `data/ANALISIS_GEOMETRI.md`.
- **Kelandaian**: SRTM 30 m, diregresi sepanjang jalan → **4,86% menanjak ke arah UPI/Lembang**.
- **Lajur**: 2 lajur per arah × 3,1 m, median 0,8 m, lalu lintas lajur kiri (lefthand).
- **Kendaraan**: motor (model *sublane*, menyelip), mobil, angkot, dump truck, bus; kendaraan berat lebih lambat saat menanjak.
- **Perilaku lokal** (`tools/control.py`): putar balik truk/bus 18–35 s maju-mundur sambil menutup lajur luar,
  mobil/angkot +2–6 s; angkot ngetem dengan durasi acak; pengemudi "maksa" masuk setelah menunggu (*impatience*).
- **Volume**: tidak ada hitungan lapangan → asumsi awal 8.080 kend/jam (`VOLUMES` di `tools/make_scenario.py`) lalu
  **dikalibrasi** (`KALIBRASI = 0.70` → 5.656 kend/jam) agar tundaan S0 dari Lembang → Gerlong cocok dengan pengamatan
  lapangan ("macet biasa, < 10 menit"); hasil S0: 7,5 menit. Uji S0 pada 50/60/70/80/100% → 0,5/0,9/8,2/16/27 menit.
  Uji sensitivitas arus +15% disertakan. Hasil volume awal diarsipkan di `results/arsip_volume_awal/`.
- **Validasi logika**: uji kontrol (volume sama, semua lurus tanpa belok/putar balik) → tundaan 15 s, antrean arah turun
  0 m; dengan puteran (S0) → tundaan 116 s, antrean 311 m. Artinya kemacetan memang berasal dari puteran, bukan dari volume.

## Keterbatasan (wajib disebut di laporan)

1. Volume & komposisi kendaraan adalah asumsi yang dikalibrasi dari pengalaman lapangan (belum hitungan resmi); angka absolut (detik) bersifat indikatif, **perbandingan antar skenario** yang utama.
2. Durasi manuver putar balik truk/bus dan perilaku ngetem berupa parameter perkiraan (dapat diubah di `tools/control.py`).
3. Pejalan kaki tidak dimodelkan dalam SUMO.
4. Desain flyover S2 adalah pra-rancangan geometrik (kemiringan, ruang bebas, radius), bukan desain struktur.
5. Tampilan 3D bersifat *low-poly*; geometri jalan (lebar, posisi bukaan, panjang pagar) yang dibuat akurat.

## Struktur folder

```
data/        OSM, citra satelit, elevasi, ANALISIS_GEOMETRI.md
net/S0|S1|S2 jaringan SUMO (plain XML + net.net.xml)
scenarios/   demand, halte, APILL, konfigurasi per skenario (+ varian _tahap1, _x08)
tools/       geo.py, build_net.py, make_scenario.py, control.py, run.py, batch.py, report.py,
             export_scene.py, diag.py, shot.py, test_bridge.py
bridge/      server.py  (SUMO ↔ browser, WebSocket)
web/         index.html (3D), hasil.html, js/, data/ (adegan 3D), vendor/ (Three.js lokal)
results/     ringkasan.md / .json, grafik_*.png, runs/ (tiap run), logs/
PROGRESS.md  catatan progres bertahap
```

## Membangun ulang dari awal

```
python tools/build_net.py          # jaringan S0/S1/S2 dari OSM
python tools/make_scenario.py      # demand & APILL
python tools/export_scene.py       # adegan 3D
python tools/batch.py              # 12 run + laporan
python tools/run.py S1 --gui       # lihat satu skenario di sumo-gui
```
