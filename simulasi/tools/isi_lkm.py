"""Isi template LKM-2 (PDF tanpa form field) dengan menimpa teks/gambar tepat di kotak-kotaknya.

Keluaran: MSTR/LKM-2_Transportasi_TERISI.pdf  (+ pratinjau PNG di results/gambar/lkm_hal*.png)
Koordinat kotak diukur dengan pdfplumber (top dari atas halaman); reportlab memakai y dari bawah.
"""
import io
import os

import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MSTR = os.path.dirname(ROOT)
SRC = os.path.join(MSTR, "DESIGNING SOLUTION-LKM-2-Transportasi.pdf")
OUT = os.path.join(MSTR, "LKM-2_Transportasi_TERISI.pdf")
IMG = os.path.join(ROOT, "results", "gambar")
W, H = 595.29, 841.89
RED = colors.Color(0.6, 0, 0)

F = "C:/Windows/Fonts/"
pdfmetrics.registerFont(TTFont("Cal", F + "calibri.ttf"))
pdfmetrics.registerFont(TTFont("CalB", F + "calibrib.ttf"))
pdfmetrics.registerFont(TTFont("CalI", F + "calibrii.ttf"))
pdfmetrics.registerFont(TTFont("CalBI", F + "calibriz.ttf"))
pdfmetrics.registerFont(TTFont("Got", F + "GOTHIC.TTF"))
pdfmetrics.registerFont(TTFont("GotB", F + "GOTHICB.TTF"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily  # noqa: E402

registerFontFamily("Cal", normal="Cal", bold="CalB", italic="CalI", boldItalic="CalBI")


def Y(top):
    return H - top


def box(c, x0, top, x1, bottom, html, size=8.0, color=colors.black, align=TA_LEFT, min_size=5.5, lead=1.18,
        font="Cal", space=1.5):
    """Tulis paragraf (dipisah '\\n\\n') di dalam kotak; perkecil huruf sampai muat."""
    w, h = x1 - x0, bottom - top
    s = size
    while True:
        st = ParagraphStyle("p", fontName=font, fontSize=s, leading=s * lead, textColor=color, alignment=align,
                            spaceAfter=space)
        paras = [Paragraph(t.strip(), st) for t in html.split("\n\n") if t.strip()]
        tot = sum(p.wrap(w, h)[1] + st.spaceAfter for p in paras)
        if tot <= h or s <= min_size:
            break
        s -= 0.2
    if tot > h:
        print(f"  PERINGATAN: teks melebihi kotak ({tot:.0f} > {h:.0f}) di top={top}")
    y = Y(top)
    for p in paras:
        _, ph = p.wrap(w, h)
        p.drawOn(c, x0, y - ph)
        y -= ph + st.spaceAfter
    return s


def white(c, x0, top, x1, bottom):
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.white)
    c.rect(x0, Y(bottom), x1 - x0, bottom - top, fill=1, stroke=0)


def image(c, path, x0, top, w=None, h=None, border=True):
    ir = ImageReader(path)
    iw, ih = ir.getSize()
    if w and not h:
        h = w * ih / iw
    elif h and not w:
        w = h * iw / ih
    c.drawImage(ir, x0, Y(top + h), w, h)
    if border:
        c.setStrokeColor(colors.Color(0.75, 0.75, 0.75))
        c.setLineWidth(0.5)
        c.rect(x0, Y(top + h), w, h, fill=0, stroke=1)
    return w, h


def caption(c, text, x0, top, x1, size=7.2):
    box(c, x0, top, x1, top + 30, f"<i>{text}</i>", size=size, color=colors.Color(0.3, 0.3, 0.3), align=TA_CENTER)


def heading(c, text, x, top, size=10.5, color=RED):
    c.setFont("GotB", size)
    c.setFillColor(color)
    c.drawString(x, Y(top) - size, text)


# ------------------------------------------------------------------ halaman 2
def page2(c):
    WHITE = colors.white
    box(c, 48, 253, 532, 322, (
        "Kemacetan di puteran <b>Jl. Dr. Setiabudi ±No. 226</b> depan mulut <b>Jl. Gegerkalong Girang (Gerlong)</b>, Bandung. "
        "Sejak median dipermanenkan dengan kanstin + pagar stainless, kendaraan dari arah Lembang yang menuju Gerlong harus "
        "<b>putar balik di bukaan A</b> (±35 m sebelum mulut Gerlong) lalu belok kiri, sedangkan kendaraan dari arah kota putar "
        "balik di <b>bukaan B</b> (dekat gerbang UPI). Jalan hanya 2 lajur per arah (±7 m), sehingga setiap kendaraan yang "
        "putar balik, terutama <b>truk dan bus</b>, memotong dan menutup kedua arah; diperparah angkot ngetem dan tanjakan ±4,9%. "
        "Simulasi jam puncak: perjalanan Lembang → Gerlong ±28 menit, antrean arah turun ±640 m."), size=8.6, color=WHITE)
    box(c, 48, 339, 532, 408, (
        "<b>Sosial–ekonomi (utama):</b> waktu tempuh warga, mahasiswa UPI dan pekerja bertambah; pemborosan BBM serta "
        "keterlambatan angkutan umum (angkot, bus) dan angkutan barang (dump truck).\n\n"
        "<b>Lingkungan:</b> emisi dan kebisingan dari arus berhenti-jalan dan kendaraan berat yang menanjak.\n\n"
        "<b>Keselamatan:</b> manuver putar balik memotong 2 lajur arus berlawanan; banyak pejalan kaki di sekitar bukaan."),
        size=8.6)
    S = 7.3
    box(c, 64, 461, 286, 496, "Jl. Dr. Setiabudi ±No. 226 (−6,8648; 107,5941), Bandung, simpang Jl. Gegerkalong Girang "
        "depan kampus UPI. Titik konflik: <b>bukaan A</b> (35 m selatan mulut Gerlong), <b>mulut Gerlong</b> (median tertutup), "
        "<b>bukaan B</b> (105 m utara).", size=S)
    box(c, 64, 508, 286, 543, "Terutama <b>jam sibuk pagi</b> (berangkat kerja/kuliah) dan <b>sore</b> (pulang), serta "
        "<b>akhir pekan</b> saat arus wisata dari/ke Lembang; makin parah bila ada truk/bus yang putar balik.", size=S)
    box(c, 64, 555, 286, 590, "Berulang setiap hari pada jam sibuk. Pembatasan puteran sudah ada sejak ≥ Des 2023 "
        "(water barrier, Google Street View) lalu dipermanenkan dengan pagar baru. Simulasi: macet terbentuk ±8 menit "
        "setelah jam puncak dimulai dan bertahan sepanjang jam puncak.", size=S)
    box(c, 64, 602, 286, 637, "Kendaraan menunggu celah di lajur kanan → arah turun tinggal 1 lajur; saat putar balik "
        "memotong 2 lajur arah naik → arah naik berhenti; truk/bus harus maju-mundur menutup kedua arah; angkot ngetem di "
        "sudut Gerlong.", size=S)
    box(c, 64, 649, 286, 766, (
        "a) <b>Geometri:</b> lebar ±7 m/arah jauh di bawah kebutuhan putar balik (truk/bus ±25 m).\n\n"
        "b) Belok kanan ke Gerlong <b>dipaksa jadi putar balik</b> yang terlalu dekat simpang (35 m).\n\n"
        "c) Arus padat, banyak kendaraan berat, tanjakan 4,9%.\n\n"
        "d) Angkot ngetem di mulut simpang.\n\n"
        "e) Tidak ada APILL/pengaturan di titik konflik.\n\n"
        "<b>Bukti simulasi:</b> volume sama tanpa putar balik → tundaan 37 s & antrean 0 m; dengan puteran → tundaan 274 s. "
        "Jadi penyebab utamanya adalah puteran, bukan semata volume."), size=S)
    box(c, 294, 453, 534, 766, (
        "Memodelkan kondisi nyata dalam <b>mikro-simulasi SUMO</b>, membandingkan beberapa solusi secara terukur, lalu "
        "menerapkan solusi terbaik secara <b>bertahap</b>.\n\n"
        "<b>1. Pemodelan kondisi nyata.</b> Peta OpenStreetMap + citra satelit + Street View + foto/video lapangan: 2 lajur × "
        "3,1 m per arah, median 0,8 m, bukaan A & B, tanjakan 4,86% (SRTM). Kendaraan: motor (menyelip), mobil, angkot, dump "
        "truck, bus. Perilaku: truk/bus maju-mundur saat putar balik, angkot ngetem. Arus jam puncak 8.080 kend/jam (asumsi, "
        "PKJI 2023).\n\n"
        "<b>2. Tiga alternatif solusi:</b><br/>"
        "• <b>Tahap 1</b> (murah): larangan putar balik truk/bus + penertiban ngetem.<br/>"
        "• <b>S1</b>: buka median di mulut Gerlong + APILL 2 fase adaptif (fase belok kanan 5–14 s) + lajur khusus belok kanan "
        "60 m; bukaan A ditutup.<br/>"
        "• <b>S2</b>: U-turn layang 480 m (dek ±7,5 m, kelandaian ≤ 5%, loop R 13 m).\n\n"
        "<b>3. Evaluasi:</b> waktu tempuh, tundaan dan panjang antrean (jam puncak 60 menit, 3 seed acak, uji sensitivitas 80%).\n\n"
        "<b>4. Hasil:</b> waktu Lembang → Gerlong turun <b>76%</b> (S1), 72% (S2), 24% (Tahap 1); antrean Gerlong 332 m → 10 m "
        "(S1/S2); tundaan rata-rata 750 s → 426 s (S1) / 229 s (S2).\n\n"
        "<b>5. Rekomendasi bertahap:</b> segera terapkan Tahap 1 → <b>S1 sebagai solusi utama</b> (murah, tanpa pembebasan "
        "lahan) → S2 sebagai rencana jangka panjang bila arus terus meningkat."), size=7.6)


# ------------------------------------------------------------------ halaman 3
def page3(c):
    S = 7.4
    # Masalah
    white(c, 164, 380, 217, 398)
    box(c, 166, 380, 360, 408, "<b>Macet akibat puteran di Jl. Setiabudi × Gerlong</b> (Lembang → Gerlong ±28 menit)", size=S)
    # Rencana solusi
    white(c, 72, 470, 147, 488)
    box(c, 46, 463, 159, 516, "<b>Penataan simpang bertahap:</b> APILL adaptif + lajur khusus belok kanan (S1); jangka panjang "
        "U-turn layang (S2)", size=7.0)
    # Target capaian: tutup contoh bawaan, gambar ulang garis cabang
    white(c, 308, 470, 532.2, 496.4)     # baris contoh 1-3
    white(c, 308, 497.6, 402, 505.5)     # "menghindarkan diri"
    white(c, 308, 505.5, 383, 517)       # "dari kecelakaan" (tidak menyentuh lingkaran Pengguna)
    c.setStrokeColor(colors.Color(0.5, 0, 0))
    c.setLineWidth(2.0)
    c.line(288.5, Y(497.3), 404.4, Y(497.3))
    c.line(404.4, Y(497.3), 404.4, Y(509.0))
    box(c, 309, 471, 530, 496, "Waktu tempuh Lembang → Gerlong turun ≥ 70%, antrean Gerlong &lt; 20 m, tidak ada truk/bus "
        "putar balik di jalan 2 lajur (simulasi S1: −76%, antrean 10 m)", size=6.9)
    # Pembuat kebijakan & pengguna
    white(c, 214, 535, 266, 552)
    box(c, 216, 535, 340, 552, "Dishub, Satlantas & pengelola jalan", size=6.8)
    white(c, 425, 529, 479, 546)
    box(c, 427, 529, 534, 546, "Pengendara, angkot, truk & bus", size=6.8)
    # langkah: label hanya selebar ruang di antara lingkaran (±62 pt)
    for x0, top, x1, xb1, txt in [(163, 579, 225, 211.5, "Larang putar balik truk/bus + tertib ngetem"),
                                  (268.5, 578, 331, 319.5, "Buka median + APILL adaptif + lajur khusus"),
                                  (374.5, 578, 437, 423.0, "Patuhi rambu & lajur khusus"),
                                  (482, 578, 535, 525.5, "Truk/bus pakai titik putar lebar")]:
        white(c, x0 - 1, top + 2, xb1, top + 18)
        box(c, x0, top + 1, x1, top + 31, txt, size=6.5, min_size=5.6)
    box(c, 52, 614, 526, 744, (
        "<b>Rincian tahap pencapaian</b>\n\n"
        "<b>Pembuat kebijakan – Langkah 1 (0–3 bulan):</b> rambu larangan putar balik truk/bus di bukaan A & B, petugas Pos "
        "Gatur Panorama Gerlong pada jam sibuk, halte resmi dan larangan ngetem di mulut Gerlong.\n\n"
        "<b>Pembuat kebijakan – Langkah 2 (3–12 bulan):</b> buka median di mulut Gerlong, pasang APILL 2 fase adaptif (fase "
        "belok kanan 5–14 s sesuai antrean), marka lajur khusus belok kanan 60 m, tutup bukaan A. <i>Jangka panjang:</i> kajian "
        "kelayakan U-turn layang (perlu pelebaran jalan & lahan).\n\n"
        "<b>Pengguna – Langkah 1:</b> patuhi rambu, tidak berhenti/ngetem di mulut simpang, lajur kanan hanya untuk belok kanan.\n\n"
        "<b>Pengguna – Langkah 2:</b> truk/bus memakai titik putar yang lebar atau rute alternatif; penumpang angkot naik-turun "
        "di halte.\n\n"
        "<b>Capaian (simulasi S1):</b> Lembang → Gerlong −76%, Gerlong → atas −84%, antrean Gerlong 332 m → 10 m."), size=7.6)


# ------------------------------------------------------------------ halaman 4
def page4(c):
    white(c, 38, 236, 558, 792)
    heading(c, "Aplikasi: SUMO 1.28 + simulasi 3D Three.js (setara Unity) + mode kemudi", 42, 240, size=10)
    box(c, 42, 258, 553, 476, (
        "<b>SUMO</b> (Simulation of Urban MObility) menghitung pergerakan setiap kendaraan; <b>aplikasi 3D Three.js</b> tersambung "
        "langsung ke SUMO untuk visualisasi dan <b>mode kemudi</b> (pengguna mengemudikan motor/mobil/angkot/truk/bus di dalam "
        "simulasi, kendaraan lain bereaksi).\n\n"
        "<b>Rencana pemodelan:</b><br/>"
        "<b>1. Peta & geometri</b> – OpenStreetMap (median baru sudah terpetakan) dicocokkan dengan citra satelit, Street View, "
        "foto & video lapangan → 2 lajur × 3,1 m per arah, median pagar 0,8 m, bukaan A, mulut Gerlong, bukaan B; 1.703 gedung "
        "untuk tampilan 3D.<br/>"
        "<b>2. Kelandaian</b> – data elevasi SRTM → 4,86% menanjak ke arah UPI/Lembang.<br/>"
        "<b>3. Agen kendaraan</b> – motor (model sublane, menyelip), mobil, angkot hijau, dump truck, bus; lalu lintas lajur kiri.<br/>"
        "<b>4. Perilaku lokal</b> – truk/bus maju-mundur 18–35 s saat putar balik sambil menutup lajur, mobil/angkot +2–6 s, angkot "
        "ngetem, pengemudi “maksa” setelah lama menunggu.<br/>"
        "<b>5. Arus</b> – jam puncak 8.080 kend/jam (asumsi, PKJI 2023) + uji kontrol dan uji sensitivitas 80%.<br/>"
        "<b>6. Skenario</b> – S0 eksisting, Tahap 1, S1 APILL adaptif, S2 U-turn layang; masing-masing 3 seed acak, jam puncak 60 "
        "menit → waktu tempuh, tundaan, panjang antrean.<br/>"
        "<b>7. Visualisasi</b> – kamera bebas & preset (bukaan A, mulut Gerlong, bukaan B, flyover), grafik antrean real-time."),
        size=8.6)
    w, h = image(c, os.path.join(IMG, "3d_S0_bukaan_A.png"), 48, 420, w=500)
    caption(c, "Tampilan 3D simulasi kondisi eksisting (S0) di bukaan A, menit ke-8 jam puncak: antrean arah turun 343 m.",
            48, 420 + h + 3, 548)


# ------------------------------------------------------------------ halaman 5
def arrow(c, x0, y0, x1, y1, col=RED):
    c.setStrokeColor(col)
    c.setFillColor(col)
    c.setLineWidth(1.2)
    c.line(x0, y0, x1, y1)
    import math
    a = math.atan2(y1 - y0, x1 - x0)
    p = c.beginPath()
    p.moveTo(x1, y1)
    p.lineTo(x1 - 6 * math.cos(a - 0.4), y1 - 6 * math.sin(a - 0.4))
    p.lineTo(x1 - 6 * math.cos(a + 0.4), y1 - 6 * math.sin(a + 0.4))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def page5(c):
    white(c, 40, 138, 556, 556)
    heading(c, "Aplikasi yang dipilih: SUMO + simulasi 3D (Three.js)", 42, 142, size=10)
    w, h = image(c, os.path.join(IMG, "3d_S2_flyover.png"), 58, 160, w=478)
    caption(c, "Skenario S2 (U-turn layang) di aplikasi 3D: dek layang ditopang pilar, loop putar balik di selatan, "
            "kendaraan dari Lembang mendarat 70 m sebelum Gerlong lalu belok kiri.", 58, 160 + h + 3, 536)
    image(c, os.path.join(ROOT, "results", "grafik_tundaan.png"), 132, 160 + h + 30, w=330)
    # bagan unsur
    cols = [
        ("INPUT", ["Geometri jalan (OSM, citra satelit, Street View, foto/video)", "Kelandaian SRTM 4,86%",
                   "Volume & komposisi kendaraan (asumsi jam puncak)", "Perilaku pengemudi lokal"]),
        ("MODEL SUMO", ["Jaringan jalan + median pagar + bukaan A/B", "Agen: motor, mobil, angkot, truk, bus",
                        "Pengendali: putar balik, ngetem, “maksa”", "APILL adaptif / flyover (per skenario)"]),
        ("SKENARIO", ["S0 Eksisting", "Tahap 1: larangan putar balik truk/bus + tertib ngetem",
                      "S1: APILL adaptif + lajur khusus belok kanan", "S2: U-turn layang"]),
        ("OUTPUT", ["Waktu tempuh per pergerakan", "Tundaan rata-rata", "Panjang antrean per koridor",
                    "Visual 3D + mode kemudi"]),
    ]
    x0, top, gap, bw, bh = 52, 598, 14, 113, 132
    for i, (title, items) in enumerate(cols):
        x = x0 + i * (bw + gap)
        c.setFillColor(colors.Color(1, 1, 0.8))
        c.setStrokeColor(RED)
        c.setLineWidth(0.9)
        c.roundRect(x, Y(top + bh), bw, bh, 6, fill=1, stroke=1)
        c.setFillColor(RED)
        c.roundRect(x, Y(top + 16), bw, 16, 6, fill=1, stroke=0)
        c.rect(x, Y(top + 16), bw, 8, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("GotB", 8)
        c.drawCentredString(x + bw / 2, Y(top + 11.5), title)
        box(c, x + 5, top + 20, x + bw - 5, top + bh - 3, "\n\n".join("• " + t for t in items), size=7.2, space=2.2)
        if i < 3:
            arrow(c, x + bw + 1, Y(top + bh / 2), x + bw + gap - 1, Y(top + bh / 2))
    # umpan balik
    yb = top + bh + 10
    c.setStrokeColor(RED)
    c.setLineWidth(1.2)
    xr = x0 + 3 * (bw + gap) + bw / 2
    xl = x0 + 2 * (bw + gap) + bw / 2
    c.line(xr, Y(top + bh), xr, Y(yb))
    c.line(xr, Y(yb), xl, Y(yb))
    arrow(c, xl, Y(yb), xl, Y(top + bh + 1))
    box(c, x0, yb + 3, x0 + 4 * bw + 3 * gap, yb + 22,
        "<b>Evaluasi → pilih solusi:</b> S1 sebagai solusi utama (Lembang → Gerlong −76%), S2 sebagai rencana jangka panjang.",
        size=7.4, align=TA_CENTER)


# ------------------------------------------------------------------ halaman 6
def page6(c):
    x0, top = 72, 186
    w1, h1 = image(c, os.path.join(IMG, "denah_S1.png"), x0, top, w=205)
    w2, h2 = image(c, os.path.join(IMG, "denah_S2.png"), x0 + 230, top, w=205)
    caption(c, "Denah solusi utama S1: median dibuka di mulut Gerlong, APILL 2 fase adaptif, lajur khusus belok kanan 60 m, "
            "bukaan A ditutup.", x0, top + h1 + 2, x0 + w1, size=6.8)
    caption(c, "Denah jangka panjang S2: U-turn layang, ramp dari lajur median dekat UPI, loop R 13 m, mendarat 70 m sebelum "
            "Gerlong.", x0 + 230, top + h2 + 2, x0 + 230 + w2, size=6.8)
    t2 = top + max(h1, h2) + 34
    w3, h3 = image(c, os.path.join(IMG, "3d_S1_mulut_gerlong.png"), 97, t2, w=410)
    caption(c, "Rancangan S1 di simulasi 3D: APILL di mulut Gerlong, kendaraan dari Lembang belok kanan pada fase khusus; "
            "antrean arah turun hanya 37 m.", 97, t2 + h3 + 2, 507, size=6.8)


def build():
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    for fn in (None, page2, page3, page4, page5, page6):
        if fn:
            print("halaman", fn.__name__)
            fn(c)
        c.showPage()
    c.save()
    buf.seek(0)
    overlay = PdfReader(buf)
    tpl = PdfReader(SRC)
    out = PdfWriter()
    for i, p in enumerate(tpl.pages):
        p.merge_page(overlay.pages[i])
        out.add_page(p)
    out.add_metadata({"/Title": "LKM-2 Transportasi – Puteran Jl. Dr. Setiabudi × Gerlong (terisi)"})
    with open(OUT, "wb") as f:
        out.write(f)
    print("tersimpan:", OUT)
    pdf = pdfium.PdfDocument(OUT)
    for i in range(len(pdf)):
        pdf[i].render(scale=1.6).to_pil().save(os.path.join(IMG, f"lkm_hal{i + 1}.png"))


if __name__ == "__main__":
    build()
