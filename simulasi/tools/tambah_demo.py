"""Sisipkan slide DEMO sebelum 'KESIMPULAN & REKOMENDASI' di PPT yang sudah direvisi pengguna, lalu buat naskah final.

python tools/tambah_demo.py
"""
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MSTR = os.path.dirname(ROOT)
PPT = os.path.join(MSTR, "Presentasi_LKM1_LKM2_Puteran_Setiabudi.pptx")
DOC = os.path.join(MSTR, "Naskah_Final_Presentasi.docx")
IMG = os.path.join(ROOT, "results", "gambar", "_ppt", "3d_s0_full.jpg")
RED, BLUE, NAVY, DARK, GRAY, LBLUE = "C4161C", "1F4E9E", "163A78", "34363A", "E1E2E1", "DCE6F5"


def rgb(h):
    return RGBColor.from_string(h)


def rect(s, x, y, w, h, fill):
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    r.fill.solid()
    r.fill.fore_color.rgb = rgb(fill)
    r.line.fill.background()
    r.shadow.inherit = False
    return r


def tb(s, x, y, w, h, paras, size=20, color=DARK, bold=False, align=None, anchor=MSO_ANCHOR.TOP):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, pr in enumerate(paras if isinstance(paras, list) else [paras]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        for txt, o in (pr if isinstance(pr, list) else [(pr, {})]):
            r = p.add_run()
            r.text = txt
            b = o.get("bold", bold)
            r.font.name = "Arimo Bold" if b else "Arimo"
            r.font.bold = b
            r.font.size = Pt(o.get("size", size))
            r.font.color.rgb = rgb(o.get("color", color))
        if align is not None:
            p.alignment = align
    return box


prs = Presentation(PPT)
titles = [s.shapes.title.text if s.shapes.title is not None else "" for s in prs.slides]
if any(t.startswith("DEMO") for t in titles):
    raise SystemExit("Slide demo sudah ada.")
pos = next(i for i, t in enumerate(titles) if t.startswith("KESIMPULAN"))
lay = [l for l in prs.slide_layouts if l.name == "Title Only"][0]
s = prs.slides.add_slide(lay)
s.shapes.title.text = "DEMO SIMULASI 3D"
tb(s, 1.12, 3.32, 17.75, 0.55, "Langsung dari aplikasi: kondisi awal dibandingkan usulan solusi", size=24)

# gambar aplikasi + label LIVE
iw, ih = Image.open(IMG).size
x, y, w, h = 1.12, 4.15, 10.4, 5.85
p = s.shapes.add_picture(IMG, Inches(x), Inches(y), Inches(w), Inches(h))
ar, iar = w / h, iw / ih
if iar > ar:
    p.crop_left = p.crop_right = (1 - ar / iar) / 2
else:
    p.crop_top = p.crop_bottom = (1 - iar / ar) / 2
p.line.color.rgb = rgb(GRAY)
rect(s, x + 0.25, y + 0.25, 2.1, 0.6, RED)
tb(s, x + 0.25, y + 0.25, 2.1, 0.6, "● LIVE DEMO", size=18, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER,
   anchor=MSO_ANCHOR.MIDDLE)

steps = [("1", "Kondisi awal", "Kamera Bukaan A: antrean & truk maju-mundur"),
         ("2", "Usulan 2: APILL adaptif", "Kamera Mulut Gerlong: lampu & lajur khusus"),
         ("3", "Usulan 3: U-turn layang", "Kamera Flyover: putar balik lewat atas"),
         ("4", "Mode kemudi", "Menyetir sendiri dari arah Lembang ke Gerlong")]
for i, (n, t, d) in enumerate(steps):
    yy = 4.15 + i * 1.27
    hot = i == 3
    rect(s, 11.85, yy, 7.02, 1.12, RED if hot else GRAY)
    tb(s, 12.1, yy, 0.7, 1.12, n, size=36, bold=True, color="FFFFFF" if hot else RED, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, 12.85, yy + 0.14, 5.85, 0.45, t, size=21, bold=True, color="FFFFFF" if hot else RED)
    tb(s, 12.85, yy + 0.6, 5.85, 0.45, d, size=16, color="FFFFFF" if hot else DARK)
rect(s, 11.85, 9.3, 7.02, 0.7, LBLUE)
tb(s, 12.1, 9.3, 6.6, 0.7, [[("Buka: ", {"bold": True, "color": BLUE}),
                             ("JALANKAN_SIMULASI_3D.bat → 127.0.0.1:8000", {})]], size=16, anchor=MSO_ANCHOR.MIDDLE)

DEMO_NOTES = (
    "[Sebelum presentasi: aplikasi sudah dibuka di tab browser, kecepatan 5x.] "
    "Sekarang kami tunjukkan simulasinya langsung. [Pilih S0, kamera Bukaan A, Mulai.] Ini kondisi awal: kendaraan dari "
    "Lembang yang mau ke Gerlong menunggu di lajur kanan untuk putar balik, antreannya memanjang ke atas. Perhatikan truk "
    "atau bus kuning dan hijau, saat berputar mereka maju-mundur dan menutup kedua arah. Angka panjang antrean juga terlihat "
    "di panel kiri. [Ganti ke S1, kamera Mulut Gerlong.] Ini usulan kedua: median dibuka, ada lampu lalu lintas, dan "
    "kendaraan dari Lembang menunggu di lajur khusus belok kanan tanpa menghalangi arus lurus. [Ganti ke S2, kamera Flyover.] "
    "Ini usulan ketiga: kendaraan putar balik lewat jembatan layang, jadi arus di bawah tidak terpotong. [Mode kemudi: pilih "
    "Mobil, titik Dari Lembang, Mulai kemudi.] Terakhir, kami bisa ikut menyetir. W untuk gas, A dan D untuk belok. Mobil kami "
    "masuk ke simulasi, jadi kendaraan lain ikut bereaksi. [Tutup demo, kembali ke slide.]")
ns = s.notes_slide
if ns.notes_text_frame is None:   # notes master hasil simpan PowerPoint tanpa placeholder isi → salin dari slide lain
    import copy
    src = next(sl.notes_slide for sl in prs.slides if sl.has_notes_slide and sl.notes_slide.notes_placeholder is not None)
    ns.shapes._spTree.append(copy.deepcopy(src.notes_placeholder._element))
ns.notes_text_frame.text = DEMO_NOTES

# pindahkan slide baru ke posisi sebelum KESIMPULAN
lst = prs.slides._sldIdLst
el = list(lst)[-1]
lst.remove(el)
lst.insert(pos, el)
prs.save(PPT)
print("slide demo disisipkan di posisi", pos + 1, "· total", len(prs.slides))

# ------------------------------------------------------------------ naskah final
from docx import Document  # noqa: E402
from docx.shared import Pt as DPt, RGBColor as DRGB  # noqa: E402

prs = Presentation(PPT)
DIV = [(1, "Pembuka & lokasi", [1, 2]), (2, "Masalah lokal (LKM 1) & akar masalah (LKM 2)", [3, 4]),
       (3, "Strategi, alat yang dipakai, skema percobaan", [5, 6, 7]), (4, "Kondisi awal & usulan 1", [8, 9]),
       (5, "Usulan 2, usulan 3 & hasil", [10, 11, 12]), (6, "Demo, kesimpulan & penutup", [13, 14, 15])]
TRANS = {2: "Selanjutnya, masalah lokal dan akar masalahnya akan dijelaskan oleh Penyaji 2.",
         4: "Berikutnya Penyaji 3 akan menjelaskan strategi dan bagaimana kami mengujinya dengan simulasi.",
         7: "Penyaji 4 akan memperlihatkan kondisi awal dan usulan pertama.",
         9: "Dua usulan berikutnya dan hasilnya akan disampaikan oleh Penyaji 5.",
         12: "Untuk melihatnya langsung, Penyaji 6 akan mendemokan aplikasinya."}
doc = Document()
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = DPt(11)
doc.add_heading("Naskah Final – Presentasi LKM 1 & 2 Transportasi", 0)
doc.add_paragraph("Kemacetan akibat puteran di Jl. Dr. Setiabudi × Jl. Gegerkalong Girang (Gerlong). 15 slide, ±25 menit "
                  "termasuk demo. Teks dalam [kurung siku] adalah aksi, bukan untuk dibacakan.")
t = doc.add_table(rows=1, cols=3)
t.style = "Light Grid Accent 2"
for i, h in enumerate(["Penyaji", "Bagian", "Slide"]):
    t.rows[0].cells[i].text = h
for n, b, sl in DIV:
    c = t.add_row().cells
    c[0].text, c[1].text, c[2].text = f"Penyaji {n}", b, f"{sl[0]}–{sl[-1]}"
for n, b, sl in DIV:
    doc.add_heading(f"Penyaji {n} · {b}", 1)
    for k in sl:
        sld = prs.slides[k - 1]
        ttl = sld.shapes.title.text if sld.shapes.title is not None else "Sampul"
        ttl = "Sampul" if k == 1 else ttl.title()
        p = doc.add_paragraph()
        r = p.add_run(f"Slide {k} – {ttl}")
        r.bold = True
        r.font.color.rgb = DRGB(0xC4, 0x16, 0x1C)
        note = sld.notes_slide.notes_text_frame.text if sld.has_notes_slide else ""
        doc.add_paragraph(note.replace("[Penyaji 1] ", ""))
        if k in TRANS:
            q = doc.add_paragraph()
            rr = q.add_run("Transisi: " + TRANS[k])
            rr.italic = True
doc.add_heading("Rencana demo (slide 13)", 1)
for step in ["Sebelum mulai presentasi: klik dua kali simulasi/JALANKAN_SIMULASI_3D.bat, tunggu browser terbuka di "
             "127.0.0.1:8000, pilih kecepatan 5x, lalu biarkan tab tetap terbuka.",
             "Kondisi awal: pilih S0 → kamera Bukaan A → Mulai. Tunggu ±30 detik sampai antrean terlihat.",
             "Usulan 2: pilih S1 → kamera Mulut Gerlong → Mulai. Tunjukkan lampu dan lajur khusus belok kanan.",
             "Usulan 3: pilih S2 → kamera Flyover (S2) → Mulai.",
             "Mode kemudi: pilih Mobil, titik muncul Dari Lembang → Mulai kemudi. W gas, S rem, A/D setir, C ganti kamera.",
             "Waktu demo maksimal ±3 menit, lalu kembali ke PPT (Alt+Tab).",
             "Cadangan bila aplikasi bermasalah: kembali ke slide 8–11, gambar 3D di sana diambil dari aplikasi yang sama."]:
    doc.add_paragraph(step, style="List Number")
doc.add_heading("Antisipasi pertanyaan", 1)
for q, a in [
    ("Jumlah kendaraannya dari mana?", "Belum ada hitungan resmi, jadi jumlah kendaraan kami setel sampai kondisi sekarang "
     "macetnya sekitar 7–8 menit, sesuai pengalaman kami di lapangan. Lalu kami uji juga dengan arus 15% lebih padat."),
    ("Kenapa tidak langsung flyover?", "Flyover memang terbaik, tetapi mahal dan butuh pelebaran jalan serta lahan. Pada jam "
     "sibuk biasa, rekayasa murah dan APILL sudah memangkas waktu macet menjadi sekitar satu menit."),
    ("Kenapa rekayasa murah bisa sangat efektif?", "Truk dan bus yang maju-mundur saat putar balik menutup dua arah sekaligus. "
     "Begitu mereka tidak putar balik di sini, jalan kembali lancar. Tetapi saat arus lebih padat, celah untuk putar balik "
     "makin jarang sehingga usulan ini mulai goyah."),
    ("Lalu truk dan bus putar balik di mana?", "Di titik putar lain yang lebih lebar di luar area ini. Dampaknya di tempat "
     "lain belum kami hitung, ini menjadi catatan untuk kajian berikutnya."),
    ("Apa kekurangan APILL?", "Kendaraan yang lurus sesekali harus berhenti di lampu merah, tetapi gerakan ke Gerlong tetap "
     "lancar walaupun jalan lebih padat."),
    ("Seberapa mirip simulasinya dengan kenyataan?", "Bentuk jalan diambil dari peta dan citra satelit lalu dicek dengan foto, "
     "tanjakan dari data ketinggian, jenis kendaraan dari video, dan kebiasaan lokal seperti ngetem dan truk maju-mundur "
     "ikut dimodelkan. Setiap percobaan diulang tiga kali."),
    ("Kenapa memakai SUMO?", "Gratis, umum dipakai untuk riset lalu lintas, menghitung setiap kendaraan satu per satu, dan bisa "
     "diatur lewat Python.")]:
    p = doc.add_paragraph()
    p.add_run(q + " ").bold = True
    p.add_run(a)
doc.save(DOC)
print("tersimpan:", DOC)
