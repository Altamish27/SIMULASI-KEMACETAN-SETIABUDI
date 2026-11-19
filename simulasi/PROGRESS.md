# PROGRESS — Simulasi Puteran Jl. Dr. Setiabudi 226 (Gerlong)

Catatan progres bertahap. Kalau sesi terputus, lanjutkan dari tahap pertama yang belum [x].

## Tahapan
- [x] T1 Setup: instal SUMO (pip eclipse-sumo 1.28.0), struktur folder
- [x] T2 Peta: unduh OSM area, cek geometri Setiabudi + mulut Gerlong → lihat data/ANALISIS_GEOMETRI.md
- [x] T3 Jaringan SUMO S0 (kondisi eksisting: median pagar, bukaan A & B)
- [x] T4 Demand jam puncak (asumsi PKJI 2023) + tipe kendaraan (motor, mobil, angkot, truk, bus)
- [x] T5 Skenario S1 (APILL + lajur khusus belok kanan + tutup B + larang truk/bus belok + larang ngetem)
- [x] T6 Skenario S2 (U-turn layang)
- [x] T7 Jalankan analisis headless, grafik & tabel hasil
- [x] T8 Bridge Python (TraCI <-> WebSocket) untuk 3D live + kendaraan ego
- [x] T9 Three.js 3D: jalan, median pagar, gedung OSM, rambu, kendaraan, flyover
- [x] T10 Mode kemudi (motor/mobil/angkot/truk)
- [x] T11 README cara menjalankan + ringkasan hasil untuk LKM

## Log
- 2026-11-19 T1: SUMO 1.28.0 via pip (SUMO_HOME = python -c "import sumo;print(sumo.SUMO_HOME)").
- 2026-11-19 T2: data/area.osm (bbox -6.8700,107.5880,-6.8590,107.6000), data/sat_z19.jpg (Esri), data/elevation.json (SRTM).
  Temuan: Gerlong = Jl. Gegerkalong Girang (barat). Bukaan A y≈-67 (selatan Gerlong 35 m), Gerlong y≈-33, Bukaan B y≈+72. Tanjakan ±5-6% ke utara.
- 2026-11-19 T3: tools/geo.py + tools/build_net.py -> net/S0|S1|S2/net.net.xml (lefthand, koordinat lokal, z dari regresi SRTM 4,86%).
  Koneksi diverifikasi = sesuai desain. Jaringan S1 (APILL di G, lajur khusus belok y+28..G) & S2 (flyover FO 480 m, loop R13 di y≈-220, deck ≤5%, clearance 7,5 m) sudah terbangun; program lampu S1 dibuat di T5.
- 2026-11-19 T4: tools/make_scenario.py (volume asumsi 8.080 kend/jam, 7 vType, halte/ngetem, APILL S1), tools/control.py (manuver putar balik, ngetem, ukur antrean), tools/run.py (libsumo, step 0,5 s), tools/diag.py.
  Perbaikan: kuncian permanen -> tambah 'impatience' (time-to-impatience 45 s), ngetem dipindah ke sudut J&T (utara mulut Gerlong).
  VALIDASI (25 menit sim): kontrol semua-lurus tundaan 37 s, antrean turun 0 m; S0 tundaan 274 s, antrean turun rata 385 m -> macet disebabkan puteran.
- 2026-11-19 T5/T6: S1 v1 (APILL 3 fase) TERBUKTI memperburuk (arah naik lumpuh, tundaan 423 s) -> S1 v2: APILL 2 fase ACTUATED (fase belok kanan 5-14 s), bukaan B tetap utk kendaraan kecil, A ditutup.
  Tambah varian S0_tahap1 (larang truk/bus putar balik + tertib ngetem). S2 juga pakai tertib ngetem. Metrik antrean diganti: total panjang tersendat per koridor.
  Uji 25 mnt (1 seed): tundaan S0 274 | tahap1 167 | S1 196 | S2 99 s. Lembang->Gerlong: 427 | 521 | 267 | 269 s.
- 2026-11-19 T7: batch penuh dijalankan: `python tools/batch.py` (12 run, log results/logs/batch.log) -> otomatis panggil tools/report.py (ringkasan.md + grafik PNG). Jika terputus: jalankan ulang batch (run yang sudah ada summary.json bisa di-skip manual).
- 2026-11-19 T7 SELESAI: results/ringkasan.md + grafik_*.png. Tundaan S0 750 | Tahap1 416 | S1 426 | S2 229 s. Lembang->Gerlong: S1 -76%, S2 -72%, Tahap1 -24%.
  Sensitivitas kepadatan 80%: folder scenarios/*_x08, batch log results/logs/batch_sens.log (jalan di latar).
- 2026-11-19 T8-T10 SELESAI: bridge/server.py (libsumo + websockets, http :8000, ws :8765), web/ (Three.js r160 lokal di web/vendor),
  tools/export_scene.py -> web/data/*.json, tools/shot.py (screenshot CDP, GPU d3d11), tools/test_bridge.py. Mode kemudi diuji (spawn, gas, tabrakan terdeteksi).
  URL: http://localhost:8000/?mulai=S2&kamera=Flyover%20(S2)&cepat=10
- 2026-11-19 T11 SELESAI: README.md, LKM2_DRAF_ISIAN.md, JALANKAN_SIMULASI_3D.bat / JALANKAN_ANALISIS.bat / INSTAL_PAKET.bat, requirements.txt,
  tools/plan.py -> results/gambar/denah_S0|S1|S2.png, gambar 3D di results/gambar/. Sensitivitas 80%: urutan sama (S1 Lembang->Gerlong -80%, S2 tundaan 33 s).
  Perbaikan akhir: server tahan error per-langkah; URL pakai 127.0.0.1 (localhost/IPv6 bisa menggantung di Windows).
STATUS: SEMUA TAHAP SELESAI. Ide lanjutan: hitung volume lapangan (video diam) -> ganti VOLUMES di tools/make_scenario.py -> jalankan ulang batch.
