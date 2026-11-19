# Draf Isian LKM-2 Transportasi — Designing Solution

**Topik:** Kemacetan akibat puteran di Jl. Dr. Setiabudi ±No. 226 × Jl. Gegerkalong Girang (Gerlong), Bandung

> Angka berasal dari simulasi SUMO di folder ini (`results/ringkasan.md`). Volume lalu lintas adalah **asumsi jam puncak**
> (belum ada hitungan lapangan), jadi tulis angka sebagai hasil simulasi, bukan hasil pengukuran.

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
   lalu dipermanenkan dengan pagar stainless baru. Dalam simulasi jam puncak, waktu tempuh Lembang → Gerlong mencapai ±28 menit.
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

   Bukti simulasi: dengan volume yang sama tetapi semua kendaraan lurus, tundaan hanya 37 s dan antrean arah turun 0 m.
   Dengan puteran, tundaan naik menjadi 274 s. Jadi **penyebab macet adalah puterannya, bukan semata-mata volume**.

**Rencana strategi penyelesaian**
Memodelkan kondisi nyata dalam mikro-simulasi (SUMO, peta OpenStreetMap, kelandaian SRTM), lalu membandingkan tiga solusi:
- Tahap 1, rekayasa murah: larangan putar balik truk/bus dan penertiban ngetem.
- S1: median dibuka di mulut Gerlong, ditambah APILL 2 fase adaptif dan lajur khusus belok kanan.
- S2: U-turn layang.

Solusi dipilih berdasarkan waktu tempuh, tundaan, dan panjang antrean, kemudian diterapkan bertahap.

---

## Halaman 3 — Langkah-langkah Pencapaian (isi bagan)

- **Masalah:** macet akibat puteran di Jl. Setiabudi × Gerlong.
- **Rencana solusi:** penataan simpang bertahap: rekayasa lalu lintas → **APILL adaptif + lajur khusus belok kanan (S1)**
  → jangka panjang **U-turn layang (S2)** bila arus terus naik.
- **Target capaian:**
  - Waktu tempuh Lembang → Gerlong turun ≥ 70%.
  - Antrean di Jl. Gegerkalong Girang < 20 m.
  - Tidak ada kendaraan berat yang putar balik di jalan 2 lajur.
- **Pembuat kebijakan** (Dishub, Satlantas, pengelola jalan sesuai status jalan):
  - Langkah 1: larangan putar balik truk/bus (rambu + petugas jam sibuk), penertiban ngetem angkot, dan halte yang jelas.
  - Langkah 2: membuka median di mulut Gerlong, memasang APILL adaptif dengan fase belok kanan 5–14 s, marka lajur khusus 60 m,
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
5. Arus jam puncak (asumsi) 8.080 kend/jam, ditambah uji sensitivitas 80%.
6. Skenario S0, Tahap 1, S1, dan S2 × 3 seed acak. Keluaran: waktu tempuh, tundaan, dan panjang antrean.

---

## Halaman 5 — Bagan Unsur Utama Rancangan Solusi

```
 INPUT                         MODEL (SUMO)                         OUTPUT
 ─────                         ────────────                         ──────
 Geometri jalan (OSM, foto) ─┐  Jaringan jalan + median + bukaan ─┐  Waktu tempuh per pergerakan
 Kelandaian (SRTM)           ├─▶ Agen kendaraan (5 jenis)          ├─▶ Tundaan rata-rata
 Volume & komposisi (asumsi) │  Pengendali: putar balik, ngetem   │  Panjang antrean per koridor
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

| Indikator (jam puncak) | S0 Eksisting | Tahap 1 | S1 APILL | S2 Flyover |
|---|---|---|---|---|
| Lembang → Gerlong | 28,3 menit | −24% | **−76%** | −72% |
| Lurus turun | 781 s | +21% | +15% | **−79%** |
| Lurus naik | 818 s | −69% | −54% | −36% |
| Tundaan rata-rata | 750 s | 416 s | 426 s | **229 s** |
| Antrean Jl. Gegerkalong Girang | 332 m | 70 m | **10 m** | **10 m** |

Uji sensitivitas (kepadatan 80%): urutan tetap sama. S1 memangkas Lembang → Gerlong −80%, dan arah lurus turun pun membaik
(−44%). S2 tetap terbaik secara keseluruhan.

**Kesimpulan/rekomendasi:**
- Untuk masalah utama (Lembang → Gerlong), **S1 (APILL adaptif + lajur khusus belok kanan)** memberi perbaikan terbesar
  (−76%) dengan biaya rendah dan tanpa pembebasan lahan. Konsekuensinya, arah lurus turun sedikit lebih lambat (+15%) pada
  puncak tertinggi.
- **Tahap 1 saja tidak cukup.** Arus naik membaik, tetapi kendaraan dari Lembang justru makin sulit mendapat celah untuk putar
  balik.
- **S2 (U-turn layang)** paling baik secara keseluruhan (tundaan −69%), tetapi mahal dan butuh pelebaran jalan serta lahan.
  Ini cocok sebagai rencana jangka panjang.

**Keterbatasan:** volume asumsi (perlu hitungan lapangan), parameter manuver perkiraan, pejalan kaki tidak dimodelkan, dan
desain flyover masih pra-rancangan geometrik.
