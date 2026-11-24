# Draf Isian LKM-2 Transportasi — Designing Solution

**Topik:** Kemacetan akibat puteran di Jl. Dr. Setiabudi ±No. 226 × Jl. Gegerkalong Girang (Gerlong), Bandung

> Angka berasal dari simulasi SUMO di folder ini (`results/ringkasan.md`). Belum ada hitungan volume lapangan; volume jam puncak
> **dikalibrasi** (70% asumsi awal = 5.656 kend/jam) agar tundaan kondisi sekarang cocok dengan pengamatan lapangan
> ("macet biasa, kurang dari 10 menit"). Tulis angka sebagai hasil simulasi, bukan hasil pengukuran.
> Hasil lama dengan volume awal (8.080 kend/jam, tundaan ±27 menit, terlalu tinggi) diarsipkan di `results/arsip_volume_awal/`.

---

## Halaman 2 — Rencana Strategi Penyelesaian Masalah

**Masalah**
Setelah median Jl. Dr. Setiabudi di depan Gerlong dipermanenkan dengan kanstin dan pagar stainless, kendaraan dari arah
Lembang yang menuju Gerlong harus putar balik di bukaan ±35 m sebelum mulut Gerlong (bukaan A), lalu belok kiri. Kendaraan dari
arah kota yang ingin kembali ke bawah putar balik di bukaan dekat gerbang UPI (bukaan B). Jalan hanya 2 lajur per arah (±7 m),
sehingga setiap kendaraan yang putar balik, terutama truk dan bus, memotong dan menutup kedua arah. Akibatnya terjadi macet
panjang pada jam sibuk.

**Aspek yang diteliti:** sosial-ekonomi (waktu tempuh dan produktivitas warga/mahasiswa, biaya BBM, angkutan barang),
dengan dampak lingkungan (emisi dari arus berhenti-jalan) dan keselamatan (manuver memotong arus, pejalan kaki).

**Identifikasi akar masalah**
1. **Di mana?** Jl. Dr. Setiabudi ±No. 226 (−6,8648; 107,5941), simpang dengan Jl. Gegerkalong Girang, depan kampus UPI.
   Titik konflik: bukaan A (±35 m selatan mulut Gerlong), mulut Gerlong (median tertutup), dan bukaan B (±105 m utara).
2. **Kapan?** Jam sibuk pagi (berangkat kerja/kuliah) dan sore (pulang), ditambah akhir pekan saat arus wisata ke/dari Lembang.
3. **Berapa lama?** Berulang setiap jam sibuk. Puteran ini sudah dibatasi water barrier sejak ≥ Des 2023 (Google Street View),
   lalu dipermanenkan dengan pagar stainless baru. Dalam simulasi jam puncak, kendaraan dari arah Lembang tertahan rata-rata
   ±7,5 menit sebelum bisa masuk Gerlong, dan antrean arah turun rata-rata ±310 m.
4. **Bagaimana timbul?**
   - Kendaraan yang menunggu celah untuk putar balik berhenti di lajur kanan, sehingga arah turun tinggal 1 lajur.
   - Saat putar balik, kendaraan memotong 2 lajur arah naik, sehingga arah naik berhenti.
   - Truk dan bus tidak cukup radius (butuh ±25 m, tersedia ±7 m), jadi harus maju-mundur dan menutup kedua arah.
   - Angkot ngetem di sudut Gerlong.
   - Tanjakan 4,9% membuat kendaraan berat lambat mulai jalan.
5. **Apa penyebabnya?**
   - (a) Geometri: lebar jalan lebih kecil dari kebutuhan radius putar.
   - (b) Gerakan "belok kanan ke Gerlong" dipaksa menjadi putar balik yang terlalu dekat dengan simpang.
   - (c) Arus tinggi dengan banyak kendaraan berat.
   - (d) Angkot ngetem.
   - (e) Tidak ada pengaturan (APILL/petugas) di titik konflik.

   Bukti simulasi: dengan volume yang sama tetapi semua kendaraan lurus, tundaan hanya 15 s dan antrean arah turun 0 m.
   Dengan puteran, tundaan naik menjadi 116 s dan antrean ±310 m. Jadi **penyebab macet adalah puterannya, bukan semata-mata volume**.

**Rencana strategi penyelesaian**
Memodelkan kondisi nyata dalam mikro-simulasi (SUMO, peta OpenStreetMap, kelandaian SRTM), lalu membandingkan tiga solusi:
- Tahap 1, rekayasa murah: larangan putar balik truk/bus dan penertiban ngetem.
- S1: median dibuka di mulut Gerlong, ditambah APILL 2 fase adaptif dan lajur khusus belok kanan.
- S2: U-turn layang.

Solusi dipilih berdasarkan tundaan per pergerakan dan panjang antrean, kemudian diterapkan bertahap.

---

## Halaman 3 — Langkah-langkah Pencapaian (isi bagan)

- **Masalah:** macet akibat puteran di Jl. Setiabudi × Gerlong.
- **Rencana solusi:** penataan simpang bertahap: **tertib putar balik & ngetem (Tahap 1)** → **APILL adaptif + lajur khusus
  belok kanan (S1)** bila arus naik → jangka panjang **U-turn layang (S2)**.
- **Target capaian:**
  - Tundaan Lembang → Gerlong turun ≥ 80% (dari ±7,5 menit menjadi < 1,5 menit).
  - Antrean di Jl. Gegerkalong Girang < 10 m.
  - Tidak ada kendaraan berat yang putar balik di jalan 2 lajur.
- **Pembuat kebijakan** (Dishub, Satlantas, pengelola jalan sesuai status jalan):
  - Langkah 1: larangan putar balik truk/bus (rambu + petugas jam sibuk), penertiban ngetem angkot, dan halte yang jelas.
  - Langkah 2 (bila arus naik / Tahap 1 tidak cukup): membuka median di mulut Gerlong, memasang APILL adaptif dengan fase belok kanan 5–14 s, marka lajur khusus 60 m,
    dan menutup bukaan A.
  - Langkah 3 (jangka panjang): kajian kelayakan dan pengadaan lahan untuk U-turn layang.
- **Pengguna jalan:**
  - Langkah 1: mematuhi rambu dan lajur khusus, serta tidak berhenti atau ngetem di mulut simpang.
  - Langkah 2: truk/bus memakai titik putar yang lebar atau rute alternatif; penumpang naik-turun angkot di halte.

---

## Halaman 4 — Rancangan Pemodelan dan Simulasi

Software: **SUMO 1.28** (Eclipse, mikro-simulasi lalu lintas, gratis) untuk perhitungan, ditambah **tampilan 3D Three.js**
(peran setara Unity) yang tersambung langsung ke SUMO, dilengkapi **mode kemudi**.

Alur pemodelan:
1. Peta dan geometri: OpenStreetMap, citra satelit, Street View, serta foto/video lapangan. Hasilnya: 2 lajur × 3,1 m per arah,
   median 0,8 m, posisi bukaan A/B, dan mulut Gerlong.
2. Kelandaian: SRTM → 4,86% menanjak ke arah UPI.
3. Kendaraan: motor (menyelip), mobil, angkot, dump truck, dan bus, dengan perilaku lalu lintas lajur kiri.
4. Perilaku lokal: manuver putar balik truk/bus 18–35 s, angkot ngetem, dan pengemudi "maksa" setelah lama menunggu.
5. Arus jam puncak 5.656 kend/jam, dikalibrasi terhadap pengamatan lapangan (tundaan kondisi sekarang < 10 menit), ditambah
   uji kontrol (semua lurus) dan uji sensitivitas arus +15%.
6. Skenario S0, Tahap 1, S1, dan S2 × 3 seed acak. Keluaran: tundaan per pergerakan, waktu tempuh, dan panjang antrean.

---

## Halaman 5 — Bagan Unsur Utama Rancangan Solusi

```
 INPUT                         MODEL (SUMO)                         OUTPUT
 ─────                         ────────────                         ──────
 Geometri jalan (OSM, foto) ─┐  Jaringan jalan + median + bukaan ─┐  Tundaan rata-rata
 Kelandaian (SRTM)           ├─▶ Agen kendaraan (5 jenis)          ├─▶ Tundaan per pergerakan
 Volume & komposisi (kalibr.)│  Pengendali: putar balik, ngetem   │  Panjang antrean per koridor
 Perilaku pengemudi          ┘  Skenario: S0 / Tahap1 / S1 / S2  ┘  Visual 3D + mode kemudi
                                     ▲            │
                                     └── evaluasi & pilih solusi ◀┘
```

Unsur solusi S1:
- Pembukaan median di mulut Gerlong.
- APILL 2 fase adaptif (fase 1: arus lurus + belok kiri; fase 2: dari atas belok kanan/putar balik).
- Lajur khusus belok kanan 60 m.
- Penutupan bukaan A.
- Larangan putar balik truk/bus.
- Penertiban ngetem.

---

## Halaman 6 — Skema Rancangan (draft gambar)

Tempel gambar berikut (folder `results/gambar/`):
- `denah_S0.png`: kondisi sekarang (bukaan A, B, median tertutup di depan Gerlong).
- `denah_S1.png`: rancangan solusi utama (APILL + lajur khusus belok kanan).
- `denah_S2.png`: rancangan jangka panjang (U-turn layang, loop R 13 m, pilar, titik mendarat).
- `3d_S0_bukaan_A.png`, `3d_S1_mulut_gerlong.png`: tampilan 3D simulasi.
- Grafik hasil: `results/grafik_waktu_tempuh.png`, `results/grafik_antrean_turun_waktu.png`.

---

## Ringkasan hasil simulasi (untuk pembahasan)

**Tundaan** = tambahan waktu dibanding jalan lancar, termasuk menunggu di antrean akibat puteran/simpang (konsep tundaan
simpang PKJI). Model mencakup ±450 m ke utara dan selatan dari mulut Gerlong.

| Indikator (jam puncak, dikalibrasi) | S0 Eksisting | Tahap 1 | S1 APILL | S2 Flyover |
|---|---|---|---|---|
| **Tundaan Lembang → Gerlong** | **449 s (7,5 menit)** | 55 s (**−88%**) | 76 s (−83%) | 52 s (−88%) |
| Tundaan lurus turun | 157 s | 23 s | 54 s | 14 s |
| Tundaan lurus naik | 52 s | 18 s | 24 s | 21 s |
| Tundaan keluar Gerlong ke atas | 70 s | 19 s | 21 s | 20 s |
| Tundaan rata-rata semua kendaraan | 116 s | 23 s | 38 s | 20 s |
| Antrean arah turun (rata-rata) | 311 m | 24 m | 39 m | 3 m |
| Antrean Jl. Gegerkalong Girang | 25 m | 3 m | 4 m | 3 m |

**Uji sensitivitas, arus +15%** (mis. akhir pekan/musim libur atau pertumbuhan lalu lintas):

| Tundaan Lembang → Gerlong | S0 | Tahap 1 | S1 | S2 |
|---|---|---|---|---|
| Arus +15% | 1.002 s (16,7 menit) | 314 s (5,2 menit, tidak stabil ±179 s) | 161 s (2,7 menit) | 85 s (1,4 menit) |

**Uji kontrol:** volume sama, semua lurus → tundaan 15 s, antrean 0 m; dengan puteran (S0) → 116 s, antrean 311 m.

**Kesimpulan/rekomendasi:**
- Penyebab utama macet adalah **puteran, terutama truk/bus yang putar balik maju-mundur dan angkot ngetem**, bukan volume.
- **Tahap 1 (larangan putar balik truk/bus + tertib ngetem) paling layak diterapkan segera.** Pada kondisi sekarang tundaan
  Lembang → Gerlong turun 88% (7,5 menit → ±1 menit) dengan biaya sangat murah (rambu + petugas).
- **Tahap 1 rapuh bila arus naik.** Pada arus +15%, hasilnya goyah (5,2 menit, sangat bervariasi). **S1 (APILL adaptif + lajur
  khusus belok kanan)** tetap stabil (2,7 menit) tanpa pembebasan lahan, tetapi arus lurus turun ikut tertahan lampu merah.
  Jadi S1 adalah langkah 2 bila Tahap 1 tidak lagi cukup.
- **S2 (U-turn layang)** paling baik di semua kondisi, tetapi mahal dan butuh pelebaran jalan serta lahan. Ini cocok sebagai
  rencana jangka panjang.

**Keterbatasan:** volume dikalibrasi dari pengalaman lapangan (belum hitungan resmi), parameter manuver perkiraan, pejalan
kaki tidak dimodelkan, dampak truk/bus yang dialihkan ke titik putar lain di luar area tidak dihitung, dan desain flyover masih
pra-rancangan geometrik.
