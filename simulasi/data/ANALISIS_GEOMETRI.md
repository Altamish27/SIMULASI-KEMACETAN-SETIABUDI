# Analisis Geometri Lokasi — Jl. Dr. Setiabudi × Jl. Gegerkalong Girang (Gerlong)

Sistem koordinat lokal (meter): titik (0,0) = lat -6.8645, lon 107.5942. x = timur, y = utara.
Sumber: OpenStreetMap (diunduh 19-11-2026, `area.osm`), citra satelit Esri World Imagery z19,
Google Street View Des 2023 & Sep 2024, foto & video lapangan 19-11-2026, SRTM 30 m (`elevation.json`).

## Elemen utama
| Elemen | Posisi (y, m) | Bukti |
|---|---|---|
| Ujung utara median / **Bukaan B** (putar balik dari bawah → turun) | ≈ +72 | OSM: jalur terpisah mulai node 6627215624; Street View 2024 (No. 234): marka panah putar balik di lajur naik; dekat Pos Penjagaan UPI |
| **Mulut Gerlong** (Jl. Gegerkalong Girang, sisi BARAT) | ≈ −33 | OSM node 1676070938; Koramil 18-07 & Kel. Isola di jalan ini; papan "Koramil 1807" di foto/video. Median DITUTUP di depan mulut (Street View 2024: "untuk sementara jalan ditutup") |
| Zebra cross (tanpa APILL) | ≈ −32 di Gerlong | OSM node 13136294315 |
| **Bukaan A** (dari Lembang putar balik → belok kiri ke Gerlong) | ≈ −67 | OSM: jalur bergabung di node 13136294320 (simpang Jl. Kapten Abdul Hamid, timur); foto 14.29.41/44: rambu biru "putar balik" dekat baliho Tiramisusu; akhir video: setelah putar balik melewati ujung median kuning lalu papan Koramil |
| Halte "Gegerkalong Girang" (TfB) | ≈ −89, sisi barat | OSM node 12809046292 |

Jarak kritis: **Bukaan A → mulut Gerlong hanya ±35 m**. Kendaraan dari Lembang yang putar balik
di A harus memotong 2 lajur naik, lalu langsung pindah ke lajur kiri untuk belok ke Gerlong.

## Penampang jalan
- Setiabudi: 2 lajur per arah (video: dua kendaraan berdampingan + marka putus putih), lebar lajur ±3,0–3,25 m;
  total badan jalan ±13–15 m (diukur dari citra satelit).
- Median baru: kanstin hitam-putih + pagar stainless ±1,2 m; lebar ±0,8 m; garis tepi kuning di sisi median.
- Gegerkalong Girang: 2 lajur 2 arah (1 per arah), perkerasan beton, ±6 m.
- Jl. Kapten Abdul Hamid (timur, di bukaan A): jalan lingkungan ±3–4 m.

## Kelandaian (SRTM)
y −450 → +447: 877 → 930 m dpl ⇒ **±5–6% menanjak ke utara (arah UPI/Lembang)**.
Di sekitar simpang (y −150 → +150): 891 → 907 m ⇒ ±5,3%.

## Arah lalu lintas (lajur kiri / lefthand)
- Arah TURUN (dari Lembang, "dari atas"): jalur TIMUR.
- Arah NAIK (dari kota, "dari bawah"): jalur BARAT, berdampingan dengan mulut Gerlong.

## Pergerakan yang dimodelkan (S0 eksisting)
1. Turun → Gerlong: putar balik di A (memotong 2 lajur naik) → naik 35 m → belok kiri ke Gerlong.
2. Turun → putar balik ke atas: di A.
3. Naik → Gerlong: belok kiri langsung.
4. Naik → putar balik ke bawah: di B (memotong 2 lajur turun).
5. Keluar Gerlong → naik: belok kiri langsung.
6. Keluar Gerlong → turun: belok kiri, naik 105 m, putar balik di B.
7. Truk/bus putar balik: tidak muat (radius ≥12 m vs ±7 m tersedia) → manuver maju-mundur, memblokir dua arah.
8. Angkot ngetem di mulut Gerlong & halte.

## Asumsi yang perlu dikonfirmasi pengguna
- Posisi pasti bukaan A & B (perkiraan dari OSM + foto, toleransi ±10 m).
- Bukaan di depan mulut Gerlong tertutup (berdasarkan Street View 2024; foto 2026 konsisten).
