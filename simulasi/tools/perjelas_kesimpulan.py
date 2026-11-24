"""Ganti istilah teknis (median, APILL) dengan bahasa sehari-hari dan tulis ulang slide Kesimpulan.

python tools/perjelas_kesimpulan.py
"""
import os
import shutil

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPT = os.path.join(os.path.dirname(ROOT), "Presentasi_LKM1_LKM2_Puteran_Setiabudi.pptx")
shutil.copy(PPT, os.path.join(ROOT, "results", "cadangan_sebelum_kesimpulan.pptx"))
RED, BLUE, NAVY, DARK, GRAY, LGRAY, LBLUE = "C4161C", "1F4E9E", "163A78", "34363A", "E1E2E1", "EEF0EE", "DCE6F5"


def rgb(h):
    return RGBColor.from_string(h)


def rect(s, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
    r = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    r.fill.solid()
    r.fill.fore_color.rgb = rgb(fill)
    r.line.fill.background()
    r.shadow.inherit = False
    return r


def tb(s, x, y, w, h, paras, size=20, color=DARK, bold=False, anchor=MSO_ANCHOR.TOP, bullet=None, space=6,
       align=None):
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
        p.space_after = Pt(space)
        if align is not None:
            p.alignment = align
        if bullet:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Inches(0.32)))
            pPr.set("indent", str(-Inches(0.32)))
            bc = etree.SubElement(pPr, qn("a:buClr"))
            etree.SubElement(bc, qn("a:srgbClr")).set("val", bullet)
            etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
            etree.SubElement(pPr, qn("a:buChar")).set("char", "•")
    return box


def set_text(shape, new):
    """Ganti isi satu paragraf tanpa mengubah format run pertama."""
    p = shape.text_frame.paragraphs[0]
    p.runs[0].text = new
    for r in p.runs[1:]:
        r.text = ""


prs = Presentation(PPT)
S = prs.slides
title_of = lambda s: s.shapes.title.text if s.shapes.title is not None else ""
idx = {title_of(s).split(":")[0].strip(): i for i, s in enumerate(S)}

# ------------------------------------------------------------------ istilah lebih sederhana
REPL = {
    "Street View 2024: median pagar baru": "Street View 2024: pagar pembatas tengah jalan yang baru",
    "Pagar median baru menutup akses langsung; dari Lembang harus putar balik tepat sebelum Gerlong.":
        "Pagar pembatas tengah jalan (median) yang baru menutup jalan langsung ke Gerlong; dari Lembang harus putar balik dulu.",
    "Berulang setiap jam sibuk sejak median ditutup pagar": "Berulang setiap jam sibuk sejak pembatas tengah jalan dipagar",
    "Buka median di mulut Gerlong, lampu lalu lintas adaptif + lajur khusus belok kanan.":
        "Buka pagar tengah di depan Gerlong, pasang lampu lalu lintas pintar + lajur khusus belok kanan.",
    "Median dibuka di mulut Gerlong, diatur lampu lalu lintas": "Pagar tengah jalan di depan Gerlong dibuka, diatur lampu lalu lintas",
    "Median di depan Gerlong dibuka, bukaan A ditutup": "Pagar tengah di depan Gerlong dibuka; tempat putar balik lama ditutup",
    "APILL adaptif: siap saat arus naik": "Lampu lalu lintas pintar: siap saat jalan makin padat",
    "Bentuk jalan, lajur, median, dan bukaan sesuai aslinya": "Bentuk jalan, lajur, pagar tengah, dan tempat putar balik sesuai aslinya",
}
n = 0
for s in S:
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                t = "".join(r.text for r in p.runs)
                if t in REPL and p.runs:
                    p.runs[0].text = REPL[t]
                    for r in p.runs[1:]:
                        r.text = ""
                    n += 1
print("istilah diganti:", n)

# ------------------------------------------------------------------ slide kesimpulan ditulis ulang
s = S[idx["KESIMPULAN & REKOMENDASI"]]
for sh in list(s.shapes):
    if sh != s.shapes.title:
        sh._element.getparent().remove(sh._element)
s.shapes.title.text = "KESIMPULAN"
tb(s, 1.12, 3.32, 17.75, 0.55, "Macet terjadi karena kendaraan putar balik di jalan yang sempit, bukan karena jalannya terlalu ramai",
   size=23)
cards = [
    ("LANGKAH 1 · SEKARANG", "Tertibkan putar balik",
     ["Truk & bus dilarang putar balik di sini", "Ada petugas saat jam sibuk", "Angkot dilarang ngetem"],
     "Macet ±7,5 menit → kurang dari 1 menit", RED, True),
    ("LANGKAH 2 · BILA MAKIN PADAT", "Pasang lampu lalu lintas",
     ["Pagar tengah di depan Gerlong dibuka", "Ada lampu hijau khusus untuk belok ke Gerlong",
      "Tetap lancar walau kendaraan bertambah"],
     "Tetap ±1–3 menit saat jalan lebih padat", BLUE, True),
    ("LANGKAH 3 · JANGKA PANJANG", "Bangun U-turn layang",
     ["Putar balik lewat jembatan di atas jalan", "Biaya besar & butuh lahan", "Hasil paling baik"],
     "Kurang dari 1 menit, paling stabil", GRAY, False)]
for i, (k, t, items, res, col, dark) in enumerate(cards):
    x = 1.12 + i * 6.05
    rect(s, x, 4.15, 5.6, 4.75, col)
    fg = "FFFFFF" if dark else DARK
    tb(s, x + 0.35, 4.35, 5.0, 0.4, k, size=15, bold=True, color="FFFFFF" if dark else NAVY)
    tb(s, x + 0.35, 4.8, 5.0, 0.6, t, size=27, bold=True, color="FFFFFF" if dark else RED)
    tb(s, x + 0.35, 5.65, 5.0, 2.1, items, size=19, color=fg, bullet="FFFFFF" if dark else RED, space=7)
    rect(s, x + 0.25, 7.85, 5.1, 0.85, "FFFFFF")
    tb(s, x + 0.45, 7.85, 4.8, 0.85, res, size=17, bold=True, color=col if col != GRAY else RED, anchor=MSO_ANCHOR.MIDDLE)
    if i < 2:
        rect(s, x + 5.62, 6.25, 0.4, 0.5, DARK, shape=MSO_SHAPE.RIGHT_ARROW)
rect(s, 1.12, 9.15, 17.75, 0.85, LGRAY)
tb(s, 1.42, 9.15, 17.2, 0.85, [[("Rekomendasi: ", {"bold": True, "color": RED}),
                               ("mulai dari Langkah 1 karena murah dan langsung terasa; siapkan Langkah 2 bila kendaraan terus "
                                "bertambah.", {})]], size=18, anchor=MSO_ANCHOR.MIDDLE)
ns = s.notes_slide
ns.notes_text_frame.text = (
    "Kesimpulannya: macet di depan Gerlong bukan karena jalannya terlalu ramai, tetapi karena kendaraan harus putar balik "
    "di jalan yang sempit, terutama truk dan bus yang sampai maju-mundur. Solusinya kami susun bertahap. Langkah 1, "
    "sekarang: tertibkan putar balik. Truk dan bus dilarang putar balik di sini, ada petugas saat jam sibuk, dan angkot "
    "dilarang ngetem. Murah, dan di simulasi macetnya turun dari sekitar tujuh setengah menit menjadi kurang dari satu "
    "menit. Langkah 2, kalau jalan makin padat: buka pagar tengah di depan Gerlong dan pasang lampu lalu lintas yang punya "
    "lampu hijau khusus untuk belok ke Gerlong. Cara ini tetap lancar walau kendaraan bertambah. Langkah 3, jangka panjang: "
    "U-turn layang, hasilnya paling baik tetapi biayanya besar dan butuh lahan. Rekomendasi kami: mulai dari langkah 1, "
    "dan siapkan langkah 2 bila kendaraan terus bertambah.")
OUT = PPT.replace(".pptx", "_v2.pptx")
prs.save(OUT)
print("tersimpan:", OUT)
