"""Buat presentasi LKM-1 + LKM-2 + simulasi di atas template 'Laporan Kemajuan AeroEdge 202611.pptx'.

python tools/buat_ppt.py
Keluaran: MSTR/Presentasi_LKM1_LKM2_Puteran_Setiabudi.pptx dan MSTR/Naskah_Presentasi_6_Penyaji.docx
"""
import csv
import glob
import json
import os
import statistics as st
import sys

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MSTR = os.path.dirname(ROOT)
TPL = os.path.join(MSTR, "Laporan Kemajuan AeroEdge 202611.pptx")
OUT = os.path.join(MSTR, "Presentasi_LKM1_LKM2_Puteran_Setiabudi.pptx")
OUT_DOC = os.path.join(MSTR, "Naskah_Presentasi_6_Penyaji.docx")
G = os.path.join(ROOT, "results", "gambar")
TMP = os.path.join(ROOT, "results", "gambar", "_ppt")
os.makedirs(TMP, exist_ok=True)

RED, BLUE, NAVY, DARK = "C4161C", "1F4E9E", "163A78", "34363A"
GRAY, LBLUE, PINK, LGRAY, MGRAY, DRED = "E1E2E1", "DCE6F5", "F8DCDD", "EEF0EE", "6B6E73", "8C1015"
SC = ["S0", "S0_tahap1", "S1", "S2"]
SCN = {"S0": "S0 Eksisting", "S0_tahap1": "Tahap 1", "S1": "S1 APILL", "S2": "S2 Flyover"}
SCC = {"S0": RED, "S0_tahap1": MGRAY, "S1": BLUE, "S2": "7FA6DA"}
NOTES = []  # (penyaji, nomor slide, judul, naskah)


def rgb(h):
    return RGBColor.from_string(h)


# ------------------------------------------------------------------ data
D = json.load(open(os.path.join(ROOT, "results", "ringkasan.json"), encoding="utf-8"))


def loss(s, od):
    return D[s]["od"][od]["loss"][0]


def main_v(s, k):
    return D[s][k][0]


SENS = D["_sensitivitas_p15"]
KON = D["_kontrol"]
TS = {}
for s in SC:
    series = []
    for f in sorted(glob.glob(os.path.join(ROOT, "results", "runs", f"{s}_seed*", "queues.csv"))):
        m = {}
        for r in csv.DictReader(open(f)):
            t = float(r["t"])
            if t >= 600:
                m.setdefault(int((t - 600) // 60), []).append(float(r["turun"]))
        series.append([st.mean(m[i]) for i in sorted(m)][:60])
    TS[s] = [round(st.mean(x)) for x in zip(*series)]
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_scenario as ms  # noqa: E402

VOL = {k: round(v * ms.KALIBRASI) for k, v in ms.VOLUMES.items()}
TOTAL = VOL["SB_total"] + VOL["NB_total"] + VOL["GER_north"] + VOL["GER_south"] + VOL["KAH_south"] + VOL["KAH_north"]


def mnt(sec):
    return f"{sec / 60:.1f}".replace(".", ",") + " menit"


def pct(s, od="SB_ger"):
    return round((loss(s, od) - loss("S0", od)) / loss("S0", od) * 100)


# ------------------------------------------------------------------ gambar (ubah ke JPEG kecil)
def prep(src, name, box=None, maxw=1800):
    out = os.path.join(TMP, name)
    im = Image.open(src).convert("RGB")
    if box:
        im = im.crop(box)
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(out, quality=88)
    return out


def shot(name, fallback):
    p = os.path.join(G, name)
    return p if os.path.exists(p) else os.path.join(G, fallback)


IMG = {
    "sat": prep(os.path.join(G, "peta_satelit_anotasi.png"), "sat.jpg"),
    "sv_median": prep(os.path.join(MSTR, "MAPS", "Screenshot 2026-11-19 142636.png"), "sv_median.jpg"),
    "sv_226": prep(os.path.join(MSTR, "MAPS", "Screenshot 2026-11-19 142658.png"), "sv_226.jpg"),
    "sv_226b": prep(os.path.join(MSTR, "MAPS", "Screenshot 2026-11-19 142705.png"), "sv_226b.jpg"),
    "sv_2023": prep(os.path.join(MSTR, "MAPS", "Screenshot 2026-11-19 142449.png"), "sv_2023.jpg"),
    "foto1": prep(os.path.join(G, "foto_lapangan_1.jpg"), "foto1.jpg"),
    "foto2": prep(os.path.join(G, "foto_lapangan_2.jpg"), "foto2.jpg"),
    "foto3": prep(os.path.join(G, "foto_lapangan_3.jpg"), "foto3.jpg"),
    "foto4": prep(os.path.join(G, "foto_lapangan_4.jpg"), "foto4.jpg"),
    "denah0": prep(os.path.join(G, "denah_S0_crop.png"), "denah0.jpg"),
    "denah1": prep(os.path.join(G, "denah_S1_crop.png"), "denah1.jpg"),
    "denah2": prep(os.path.join(G, "denah_S2_crop.png"), "denah2.jpg"),
}
for k, f, fb in [("s0", "kal_S0_bukaan_A.png", "3d_S0_bukaan_A.png"),
                 ("t1", "kal_tahap1_bukaan_A.png", "3d_S0_bukaan_A.png"),
                 ("s1", "kal_S1_mulut_gerlong.png", "3d_S1_mulut_gerlong.png"),
                 ("s2", "kal_S2_flyover.png", "3d_S2_flyover.png"),
                 ("ik", "kal_S0_ikhtisar.png", "3d_S0_bukaan_A.png")]:
    src = shot(f, fb)
    w, h = Image.open(src).size
    IMG[k] = prep(src, f"3d_{k}.jpg", box=(int(w * 0.205), 0, w, h))   # buang panel kiri
    IMG[k + "_full"] = prep(src, f"3d_{k}_full.jpg")

# ------------------------------------------------------------------ presentasi dasar
prs = Presentation(TPL)
sld = prs.slides._sldIdLst
for sid in list(sld)[1:]:
    prs.part.drop_rel(sid.rId)
    sld.remove(sid)
LAY = [l for l in prs.slide_layouts if l.name == "Title Only"][0]
for sh in prs.slide_master.shapes:
    if sh.name == "AEROEDGE Label":
        sh.left, sh.width = Inches(11.0), Inches(7.88)
        sh.text_frame.paragraphs[0].runs[0].text = "MSTR · TRANSPORTASI"


def para_fmt(p, size, color, bold, font, italic=False, align=None):
    if align is not None:
        p.alignment = align
    for r in p.runs:
        r.font.size = Pt(size)
        r.font.color.rgb = rgb(color)
        r.font.bold = bold
        r.font.italic = italic
        r.font.name = font


def tb(s, x, y, w, h, paras, size=22, color=DARK, bold=False, font=None, align=None, anchor=MSO_ANCHOR.TOP,
       italic=False, bullet=False, space=6, line=None, margin=0, name=None):
    """paras: str | list[str | list[(teks, {opsi})]]"""
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(margin)
    if isinstance(paras, str):
        paras = [paras]
    for i, pr in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        runs = pr if isinstance(pr, list) else [(pr, {})]
        for txt, o in runs:
            r = p.add_run()
            r.text = txt
            b = o.get("bold", bold)
            f = o.get("font", font or ("Arimo Bold" if b else ("Arimo Italics" if o.get("italic", italic) else "Arimo")))
            r.font.name = f
            r.font.size = Pt(o.get("size", size))
            r.font.bold = b
            r.font.italic = o.get("italic", italic)
            r.font.color.rgb = rgb(o.get("color", color))
        if align is not None:
            p.alignment = align
        p.space_after = Pt(space)
        if line:
            p.line_spacing = line
        if bullet:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Inches(0.32)))
            pPr.set("indent", str(-Inches(0.32)))
            bc = etree.SubElement(pPr, qn("a:buClr"))
            etree.SubElement(bc, qn("a:srgbClr")).set("val", bullet if isinstance(bullet, str) else RED)
            etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
            etree.SubElement(pPr, qn("a:buChar")).set("char", "•")
    return box


def rect(s, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, line=None, name=None):
    r = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    r.fill.solid()
    r.fill.fore_color.rgb = rgb(fill)
    if line:
        r.line.color.rgb = rgb(line)
        r.line.width = Pt(1.5)
    else:
        r.line.fill.background()
    r.shadow.inherit = False
    if name:
        r.name = name
    if r.has_text_frame:
        r.text_frame.text = ""
    return r


def pic(s, path, x, y, w, h, mode="cover", border=None):
    iw, ih = Image.open(path).size
    if mode == "contain":
        sc = min(w / iw, h / ih)
        nw, nh = iw * sc, ih * sc
        p = s.shapes.add_picture(path, Inches(x + (w - nw) / 2), Inches(y + (h - nh) / 2), Inches(nw), Inches(nh))
    else:
        p = s.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
        ar, iar = w / h, iw / ih
        if iar > ar:
            c = (1 - ar / iar) / 2
            p.crop_left = p.crop_right = c
        else:
            c = (1 - iar / ar) / 2
            p.crop_top = p.crop_bottom = c
    if border:
        p.line.color.rgb = rgb(border)
        p.line.width = Pt(1.5)
    return p


def caption(s, x, y, w, text, h=0.4, size=15):
    return tb(s, x, y, w, h, text, size=size, italic=True, color=DARK)


def new(title, sub=None, penyaji=None, bagian=None, notes=""):
    s = prs.slides.add_slide(LAY)
    s.shapes.title.text = title
    if sub:
        tb(s, 1.12, 3.32, 17.75, 0.55, sub, size=24)
    if penyaji:
        tb(s, 11.0, 1.12, 7.88, 0.4, f"PENYAJI {penyaji} · {bagian}", size=15, bold=True, color=MGRAY,
           align=PP_ALIGN.RIGHT)
    NOTES.append((penyaji, len(prs.slides), title, notes))
    s.notes_slide.notes_text_frame.text = notes
    return s


def card(s, x, y, w, h, fill, kicker=None, title=None, body=None, dark=False, tsize=30, bsize=20, ksize=15,
         bullet=False, kcolor=None, tcolor=None):
    rect(s, x, y, w, h, fill)
    cy = y + 0.25
    fg = "FFFFFF" if dark else DARK
    if kicker:
        tb(s, x + 0.35, cy, w - 0.7, 0.35, kicker, size=ksize, bold=True, color=kcolor or ("FFFFFF" if dark else NAVY))
        cy += 0.4
    if title:
        tb(s, x + 0.35, cy, w - 0.7, 0.6, title, size=tsize, bold=True, color=tcolor or ("FFFFFF" if dark else RED))
        cy += 0.62 + (0.45 if len(title) * tsize * 0.0075 > w - 0.7 else 0)
    if body:
        tb(s, x + 0.35, cy + 0.08, w - 0.7, y + h - cy - 0.2, body, size=bsize, color=fg, bullet=bullet, space=5,
           line=1.05)


def stat(s, x, y, w, h, fill, value, label, vcolor=BLUE, vsize=46, lsize=18):
    rect(s, x, y, w, h, fill)
    tb(s, x + 0.35, y + 0.15, w - 0.7, 0.95, value, size=vsize, bold=True, color=vcolor)
    tb(s, x + 0.35, y + h - 0.62 - (0.32 if len(label) * lsize * 0.0068 > w - 0.7 else 0), w - 0.7, 0.9, label,
       size=lsize, color=DARK)


def cell_border(cell, color="34363A", width=12700):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = tcPr.find(qn(tag))
        if ln is None:
            ln = etree.SubElement(tcPr, qn(tag))
        ln.set("w", str(width))
        for c in list(ln):
            ln.remove(c)
        sf = etree.SubElement(ln, qn("a:solidFill"))
        etree.SubElement(sf, qn("a:srgbClr")).set("val", color)


def table(s, x, y, w, rows, colw, size=16, rowh=0.5, head=True, first_red=True, fills=None, hsize=None):
    nr, nc = len(rows), len(rows[0])
    shp = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(rowh * nr))
    t = shp.table
    tblPr = t._tbl.tblPr
    for a in ("firstRow", "bandRow"):
        tblPr.set(a, "0")
    st_id = tblPr.find(qn("a:tableStyleId"))
    if st_id is not None:
        tblPr.remove(st_id)
    for j, cw in enumerate(colw):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rowh)
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.12)
            c.margin_top = c.margin_bottom = Inches(0.05)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            ishead = head and i == 0
            fill = RED if ishead else (fills[i][j] if fills and fills[i][j] else ("FFFFFF" if i % 2 else LGRAY))
            c.fill.solid()
            c.fill.fore_color.rgb = rgb(fill)
            tf = c.text_frame
            tf.word_wrap = True
            lines = val if isinstance(val, list) else [val]
            for k, ln in enumerate(lines):
                p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                r = p.add_run()
                r.text = str(ln)
                bold = ishead or (first_red and j == 0)
                r.font.bold = bold
                r.font.name = "Arimo Bold" if bold else "Arimo"
                r.font.size = Pt(hsize if (ishead and hsize) else size)
                r.font.color.rgb = rgb("FFFFFF" if ishead else (RED if (first_red and j == 0) else DARK))
            cell_border(c, "34363A" if not ishead else RED)
    return t


def style_chart(ch, size=16, legend=True, legend_pos=XL_LEGEND_POSITION.TOP):
    ch.font.name = "Arimo"
    ch.font.size = Pt(size)
    ch.font.color.rgb = rgb(DARK)
    ch.has_legend = legend
    if legend:
        ch.legend.position = legend_pos
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(size)
        ch.legend.font.name = "Arimo"
    try:
        va = ch.value_axis
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = rgb(GRAY)
        va.format.line.fill.background()
        va.tick_labels.font.size = Pt(size - 1)
        va.tick_labels.font.color.rgb = rgb(MGRAY)
        ca = ch.category_axis
        ca.format.line.color.rgb = rgb("A7A9AC")
        ca.tick_labels.font.size = Pt(size)
        ca.tick_labels.font.color.rgb = rgb(DARK)
        ca.has_major_gridlines = False
    except Exception:
        pass


def bar(s, x, y, w, h, cats, series, kind=XL_CHART_TYPE.COLUMN_CLUSTERED, fmt='0', labels=True, legend=True,
        size=16, point_colors=None, gap=60, overlap=-5, vmax=None, title=None, lab_size=None):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals, _ in series:
        cd.add_series(name, vals)
    gf = s.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    style_chart(ch, size, legend)
    if title:
        ch.has_title = True
        ch.chart_title.text_frame.text = title
        para_fmt(ch.chart_title.text_frame.paragraphs[0], size + 1, DARK, True, "Arimo Bold")
    else:
        ch.has_title = False
    pl = ch.plots[0]
    pl.gap_width = gap
    try:
        pl.overlap = overlap
    except Exception:
        pass
    for i, (_, _, col) in enumerate(series):
        srs = pl.series[i]
        srs.format.fill.solid()
        srs.format.fill.fore_color.rgb = rgb(col)
        srs.invert_if_negative = False
    if point_colors:
        for j, col in enumerate(point_colors):
            pt = pl.series[0].points[j]
            pt.format.fill.solid()
            pt.format.fill.fore_color.rgb = rgb(col)
    if labels:
        pl.has_data_labels = True
        dl = pl.data_labels
        dl.number_format = fmt
        dl.number_format_is_linked = False
        dl.position = XL_LABEL_POSITION.OUTSIDE_END
        dl.font.size = Pt(lab_size or size)
        dl.font.bold = True
        dl.font.name = "Arimo Bold"
        dl.font.color.rgb = rgb(DARK)
    if vmax:
        ch.value_axis.maximum_scale = vmax
    ch.value_axis.minimum_scale = 0
    ch.value_axis.tick_labels.number_format = '#,##0'
    ch.value_axis.tick_labels.number_format_is_linked = False
    return ch


def arrow(s, x, y, w, h, fill=RED):
    return rect(s, x, y, w, h, fill, shape=MSO_SHAPE.RIGHT_ARROW)


# ================================================================== SLIDE 1 — SAMPUL
s1 = prs.slides[0]
for sh in list(s1.shapes):
    nm = sh.name
    if nm in ("Group 2", "Freeform 11"):
        if nm == "Freeform 11":
            idx = list(s1.shapes._spTree).index(sh._element)
        sh._element.getparent().remove(sh._element)
cov = prep(os.path.join(G, "sampul_satelit.jpg"), "cover.jpg")
p = pic(s1, cov, 13.92, 0, 6.08, 11.25)
s1.shapes._spTree.remove(p._element)
s1.shapes._spTree.insert(idx - 1, p._element)
for sh in s1.shapes:
    if not sh.has_text_frame:
        continue
    t = sh.text_frame.text
    if t.startswith("LAPORAN"):
        r0 = sh.text_frame.paragraphs[0].runs[0]
        r0.text = "LKM 1 & 2 TRANSPORTASI"
        r0.font.size = Pt(80)
    elif t.startswith("AeroEdge"):
        r0 = sh.text_frame.paragraphs[0].runs
        r0[0].text = ("Kemacetan akibat Puteran di Jl. Dr. Setiabudi × Jl. Gegerkalong Girang (Gerlong), Bandung: "
                      "Mendefinisikan Masalah, Simulasi Lalu Lintas, dan Rancangan Solusi")
        for r in r0[1:]:
            r.text = ""
        for extra in sh.text_frame.paragraphs[1:]:
            for r in extra.runs:
                r.text = ""
    elif t.startswith("Dr. EDDY"):
        sh.width = Inches(10.5)
        sh.text_frame.paragraphs[0].runs[0].text = "MATA KULIAH MSTR · TRANSPORTASI · 24 NOVEMBER 2026"
        for r in sh.text_frame.paragraphs[0].runs[1:]:
            r.text = ""
    elif t.strip() == "AEROEDGE":
        sh.left, sh.width = Inches(6.6), Inches(7.0)
        sh.text_frame.paragraphs[0].runs[0].text = "MSTR · TRANSPORTASI"
s1.notes_slide.notes_text_frame.text = (
    "[Penyaji 1] Assalamu'alaikum dan selamat pagi. Kami akan mempresentasikan LKM 1 dan LKM 2 mata kuliah MSTR bidang "
    "transportasi. Topik kami adalah kemacetan akibat puteran (U-turn) di Jl. Dr. Setiabudi sekitar nomor 226, tepat di "
    "mulut Jl. Gegerkalong Girang atau Gerlong, depan kampus UPI. Gambar di kanan adalah citra satelit lokasi: titik merah "
    "bukaan A tempat kendaraan dari Lembang putar balik, titik biru mulut Gerlong, dan titik biru tua bukaan B. "
    "Alurnya: masalah lokal dari LKM 1, rancangan solusi di LKM 2, lalu simulasi untuk menguji solusinya.")
NOTES.append((1, 1, "Sampul", s1.notes_slide.notes_text_frame.text))

# ================================================================== SLIDE 2 — PEMBAGIAN
s = new("PEMBAGIAN PENYAJI", "Enam penyaji · ±25 menit · LKM 1 → LKM 2 → simulasi → hasil", 1, "PEMBUKA", notes=(
    "Presentasi kami bagi untuk enam penyaji. Penyaji 1 membuka dan menunjukkan lokasi. Penyaji 2 menyampaikan masalah "
    "lokal dari LKM 1 dan akar masalah di LKM 2. Penyaji 3 menjelaskan strategi, alat yang dipakai, dan skema percobaan "
    "simulasi. Penyaji 4 dan 5 memperlihatkan kondisi awal dan tiga usulan solusi. Penyaji 6 menyampaikan hasil, "
    "rekomendasi, dan penutup."))
rows = [["Penyaji", "Bagian", "Isi yang dibawakan", "Slide"],
        ["Penyaji 1", "Pembuka", "Pembagian tugas, lokasi dan kondisi nyata", "1–3"],
        ["Penyaji 2", "LKM 1 → LKM 2", "Masalah lokal yang ditemukan, akar masalah", "4–5"],
        ["Penyaji 3", "LKM 2 · Simulasi", "Strategi bertahap, alat yang dipakai, skema percobaan", "6–8"],
        ["Penyaji 4", "Simulasi", "Kondisi awal (S0) dan usulan 1: rekayasa murah", "9–10"],
        ["Penyaji 5", "Simulasi", "Usulan 2: APILL adaptif dan usulan 3: U-turn layang", "11–12"],
        ["Penyaji 6", "Hasil", "Waktu macet tiap kondisi, rekomendasi, penutup", "13–15"]]
table(s, 1.12, 4.3, 17.75, rows, [2.6, 3.6, 9.55, 2.0], size=19, rowh=0.75, hsize=19)

# ================================================================== SLIDE 3 — LOKASI
s = new("LOKASI & KONDISI NYATA", "Jl. Dr. Setiabudi ±No. 226, Bandung · mulut Jl. Gegerkalong Girang (Gerlong), depan UPI",
        1, "PEMBUKA", notes=(
            "Ini lokasi yang kami amati: Jl. Dr. Setiabudi sekitar nomor 226, tepat di mulut Jl. Gegerkalong Girang atau "
            "Gerlong, depan kampus UPI. Di kiri citra satelitnya. Sejak median dipasangi pagar stainless, median di depan "
            "Gerlong tertutup. Kendaraan dari arah Lembang yang mau masuk Gerlong harus putar balik dulu di bukaan A, tidak "
            "jauh sebelum Gerlong, lalu belok kiri. Kendaraan dari arah kota yang mau kembali ke bawah putar balik di "
            "bukaan B dekat gerbang UPI. Foto di kanan menunjukkan pagar median baru, angkot, dan kendaraan yang berebut "
            "ruang di jalan yang hanya dua lajur per arah."))
pic(s, IMG["sat"], 1.12, 4.15, 5.0, 5.95)
pic(s, IMG["sv_median"], 6.45, 4.15, 6.3, 2.85)
pic(s, IMG["sv_226"], 6.45, 7.25, 6.3, 2.85)
pic(s, IMG["foto2"], 13.05, 4.15, 2.75, 5.95)
pic(s, IMG["foto3"], 16.1, 4.15, 2.75, 5.95)
for xx, yy, ww, t in [(1.12, 9.65, 5.0, "Citra satelit + anotasi"), (6.45, 6.55, 6.3, "Street View 2024: median pagar baru"),
                      (6.45, 9.65, 6.3, "Street View: mulut Gerlong"), (13.05, 9.65, 5.8, "Foto lapangan 19-11-2026")]:
    rect(s, xx, yy, ww, 0.45, "FFFFFF")
    tb(s, xx + 0.1, yy + 0.05, ww - 0.2, 0.4, t, size=15, italic=True)

# ================================================================== SLIDE 4 — MASALAH LOKAL (LKM 1)
s = new("MASALAH LOKAL (LKM 1)", "Temuan pengamatan yang menjadi dasar LKM 2", 2, "LKM 1", notes=(
    "Dari LKM 1, kami merangkum empat masalah lokal yang paling berkaitan. Pertama, pagar median baru membuat kendaraan "
    "dari Lembang terpaksa putar balik sangat dekat dengan Gerlong. Kedua, jalannya sempit dan menanjak, sehingga truk "
    "dan bus tidak cukup ruang untuk berputar dan harus maju-mundur. Ketiga, angkot ngetem dan ojek menunggu di bahu "
    "jalan. Keempat, tidak ada lampu lalu lintas atau petugas di titik konflik. Dampaknya menyentuh tiga aspek "
    "keberlanjutan: waktu dan BBM terbuang, polusi dari kendaraan yang berhenti-jalan, dan risiko keselamatan karena "
    "kendaraan memotong arus berlawanan."))
probs = [("1", "Putar balik dipaksa", "Pagar median baru menutup akses langsung; dari Lembang harus putar balik tepat "
          "sebelum Gerlong."),
         ("2", "Jalan sempit & menanjak", "Hanya 2 lajur per arah; truk dan bus tidak cukup ruang berputar sehingga "
          "maju-mundur."),
         ("3", "Angkot ngetem", "Angkot dan ojek menunggu penumpang di bahu jalan dekat mulut simpang."),
         ("4", "Tanpa pengaturan", "Tidak ada lampu lalu lintas atau petugas di titik konflik putar balik.")]
for i, (n, t, b) in enumerate(probs):
    x = 1.12 + (i % 2) * 6.05
    y = 4.2 + (i // 2) * 2.6
    rect(s, x, y, 5.8, 2.4, RED if i == 0 else GRAY)
    dk = i == 0
    tb(s, x + 0.3, y + 0.2, 0.9, 1.0, n, size=44, bold=True, color="FFFFFF" if dk else RED)
    tb(s, x + 1.15, y + 0.28, 4.45, 0.6, t, size=24, bold=True, color="FFFFFF" if dk else RED)
    tb(s, x + 1.15, y + 0.95, 4.45, 1.4, b, size=18, color="FFFFFF" if dk else DARK)
pic(s, IMG["foto4"], 13.45, 4.2, 5.42, 5.0)
caption(s, 13.45, 9.25, 5.42, "Truk di sekitar bukaan putar balik", size=15)
rect(s, 1.12, 9.4 - 0.15, 11.85, 0.85, LBLUE)
tb(s, 1.42, 9.3, 11.4, 0.75, [[("Dampak: ", {"bold": True, "color": BLUE}),
                               ("waktu & BBM terbuang (ekonomi) · polusi berhenti-jalan (lingkungan) · "
                                "risiko tabrakan (sosial)", {})]], size=18, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================== SLIDE 5 — AKAR MASALAH (LKM 2)
s = new("AKAR MASALAH (LKM 2)", "Masalah: macet akibat kendaraan putar balik di depan Gerlong", 2, "LKM 2", notes=(
    "Masuk ke LKM 2. Masalah yang kami fokuskan adalah macet akibat kendaraan yang putar balik di depan Gerlong. Kami "
    "telusuri dengan lima pertanyaan. Di mana: di Jl. Setiabudi depan Gerlong dan UPI. Kapan: jam berangkat dan pulang "
    "kerja atau kuliah, serta akhir pekan arus wisata Lembang. Berapa lama: berulang setiap jam sibuk sejak median "
    "ditutup. Bagaimana timbul: kendaraan yang menunggu putar balik memakan lajur, lalu saat berputar memotong arus "
    "berlawanan; truk dan bus harus maju-mundur. Penyebab utamanya adalah gerakan putar balik itu sendiri. Ini kami "
    "buktikan di simulasi: dengan jumlah kendaraan yang sama tetapi tanpa putar balik, jalan hampir lancar."))
qs = [("Di mana?", "Jl. Setiabudi depan Gerlong & UPI: bukaan A, mulut Gerlong, bukaan B"),
      ("Kapan?", "Jam berangkat & pulang hari kerja; akhir pekan arus wisata Lembang"),
      ("Berapa lama?", "Berulang setiap jam sibuk sejak median ditutup pagar"),
      ("Bagaimana timbul?", "Antre putar balik memakan lajur; saat berputar memotong arus berlawanan; truk/bus maju-mundur")]
for i, (q, a) in enumerate(qs):
    y = 4.2 + i * 1.18
    rect(s, 1.12, y, 10.3, 1.05, GRAY)
    tb(s, 1.4, y + 0.1, 3.0, 0.85, q, size=21, bold=True, color=RED, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, 4.4, y + 0.1, 6.85, 0.85, a, size=18, anchor=MSO_ANCHOR.MIDDLE)
rect(s, 11.75, 4.2, 7.12, 4.57, RED)
tb(s, 12.1, 4.38, 6.5, 0.5, "Apa penyebabnya?", size=24, bold=True, color="FFFFFF")
tb(s, 12.1, 5.0, 6.5, 3.7, ["Gerakan ke Gerlong dipaksa menjadi putar balik dekat simpang",
                            "Jalan terlalu sempit untuk truk & bus berputar",
                            "Angkot ngetem di mulut simpang",
                            "Tidak ada pengaturan di titik konflik"], size=19, color="FFFFFF", bullet="FFFFFF", space=10)
rect(s, 1.12, 9.0, 17.75, 0.95, LBLUE)
tb(s, 1.42, 9.05, 17.2, 0.85, [[("Bukti simulasi: ", {"bold": True, "color": BLUE}),
                                ("jumlah kendaraan sama tanpa putar balik → hampir lancar; dengan putar balik → tertahan "
                                 "±8 kali lebih lama.", {})]], size=19, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================== SLIDE 6 — STRATEGI
s = new("STRATEGI PENYELESAIAN", "LKM 2 · Modelkan → bandingkan → terapkan bertahap", 3, "LKM 2", notes=(
    "Strategi kami: memodelkan kondisi nyata di simulasi, membandingkan beberapa solusi, lalu menerapkannya bertahap dari "
    "yang paling murah. Usulan pertama rekayasa murah: melarang truk dan bus putar balik di sini dan menertibkan angkot "
    "ngetem. Usulan kedua membuka median di mulut Gerlong dengan lampu lalu lintas adaptif dan lajur khusus belok kanan. "
    "Usulan ketiga, jangka panjang, U-turn layang. Targetnya, kendaraan dari Lembang tidak lagi tertahan lama, antrean "
    "di Gerlong hilang, dan tidak ada truk atau bus yang putar balik di jalan sempit ini. Pelaksananya Dishub, "
    "Satlantas, dan pengelola jalan, dibantu kepatuhan pengguna jalan."))
steps = [("USULAN 1 · SEGERA", "Rekayasa murah", "Larang truk/bus putar balik, petugas jam sibuk, tertibkan angkot ngetem."),
         ("USULAN 2 · MENENGAH", "APILL adaptif", "Buka median di mulut Gerlong, lampu lalu lintas adaptif + lajur khusus "
          "belok kanan."),
         ("USULAN 3 · JANGKA PANJANG", "U-turn layang", "Putar balik lewat jembatan layang; butuh pelebaran jalan & lahan.")]
for i, (k, t, b) in enumerate(steps):
    x = 1.12 + i * 4.55
    card(s, x, 4.25, 4.2, 3.75, GRAY, k, t, b, tsize=27, bsize=18, ksize=14)
    if i < 2:
        arrow(s, x + 4.22, 5.9, 0.3, 0.4, RED)
rect(s, 14.77, 4.25, 4.1, 3.75, RED)
tb(s, 15.05, 4.45, 3.6, 0.45, "TARGET", size=15, bold=True, color="FFFFFF")
tb(s, 15.05, 4.95, 3.6, 3.0, ["Tertahan < 1,5 menit dari Lembang ke Gerlong", "Antrean Gerlong hilang",
                              "Nol truk/bus putar balik di jalan sempit"], size=18, color="FFFFFF", bullet="FFFFFF", space=8)
rect(s, 1.12, 8.25, 8.7, 1.7, LGRAY)
tb(s, 1.4, 8.35, 8.2, 0.45, "Pembuat kebijakan", size=19, bold=True, color=RED)
tb(s, 1.4, 8.85, 8.2, 1.05, "Dishub, Satlantas & pengelola jalan: rambu, petugas, APILL, kajian flyover", size=17)
rect(s, 10.17, 8.25, 8.7, 1.7, LGRAY)
tb(s, 10.45, 8.35, 8.2, 0.45, "Pengguna jalan", size=19, bold=True, color=RED)
tb(s, 10.45, 8.85, 8.2, 1.05, "Patuhi rambu & lajur, tidak berhenti di mulut simpang, truk/bus pakai titik putar lain",
   size=17)

# ================================================================== SLIDE 7 — STACK
s = new("ALAT YANG DIPAKAI", "Simulasi lalu lintas berbasis peta nyata, bisa dilihat dalam 3D", 3, "SIMULASI", notes=(
    "Untuk menguji solusi tanpa harus mencobanya di jalan, kami membuat simulasi lalu lintas. Alatnya empat. "
    "OpenStreetMap dan citra satelit untuk peta jalan yang sesuai aslinya. SUMO, perangkat lunak simulasi lalu lintas "
    "gratis, untuk menjalankan ribuan kendaraan yang masing-masing bergerak sendiri seperti pengemudi sungguhan. Python "
    "untuk menambahkan kebiasaan lokal, seperti truk yang maju-mundur saat putar balik dan angkot ngetem. Lalu Three.js "
    "untuk menampilkannya dalam 3D di browser, bahkan kita bisa ikut menyetir di dalamnya. Cara kerjanya sederhana: peta "
    "jalan nyata dimasukkan, kendaraan dijalankan selama satu jam sibuk, lalu diukur berapa lama kendaraan tertahan."))
stack = [("PETA", "OpenStreetMap + citra satelit", "Bentuk jalan, lajur, median, dan bukaan sesuai aslinya"),
         ("SIMULASI", "SUMO", "Menjalankan ribuan kendaraan; tiap kendaraan bergerak sendiri seperti pengemudi nyata"),
         ("PERILAKU LOKAL", "Python", "Truk/bus maju-mundur saat putar balik, angkot ngetem, pengemudi menyerobot"),
         ("TAMPILAN", "Three.js (3D)", "Lihat kondisi jalan dalam 3D di browser + mode menyetir sendiri")]
for i, (k, t, b) in enumerate(stack):
    y = 4.2 + i * 1.47
    rect(s, 1.12, y, 9.6, 1.32, RED if i == 1 else GRAY)
    dk = i == 1
    tb(s, 1.4, y + 0.12, 2.6, 0.35, k, size=14, bold=True, color="FFFFFF" if dk else NAVY)
    tb(s, 1.4, y + 0.45, 3.4, 0.75, t, size=21, bold=True, color="FFFFFF" if dk else RED, anchor=MSO_ANCHOR.TOP)
    tb(s, 4.95, y + 0.15, 5.6, 1.05, b, size=17, color="FFFFFF" if dk else DARK, anchor=MSO_ANCHOR.MIDDLE)
pic(s, IMG["ik"], 11.05, 4.2, 7.82, 3.9)
caption(s, 11.05, 8.12, 7.82, "Tampilan 3D simulasi kondisi sekarang", size=14)
flow = ["Peta jalan nyata", "Jalankan 1 jam sibuk", "Ukur waktu tertahan"]
for i, t in enumerate(flow):
    x = 11.05 + i * 2.67
    rect(s, x, 8.75, 2.35, 1.2, LBLUE)
    tb(s, x + 0.1, 8.75, 2.15, 1.2, t, size=16, bold=True, color=BLUE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 2:
        arrow(s, x + 2.37, 9.17, 0.28, 0.36, BLUE)

# ================================================================== SLIDE 8 — SKEMA PERCOBAAN
s = new("SKEMA PERCOBAAN", "Satu jam sibuk, kendaraan dan perilakunya dibuat mirip kondisi nyata", 3, "SIMULASI", notes=(
    "Skema percobaannya begini. Kami menjalankan satu jam sibuk dengan sekitar 5.600 kendaraan: kira-kira 2.500 turun dari "
    "Lembang, 2.700 naik dari kota, dan sisanya keluar masuk Gerlong. Jumlah ini kami setel supaya kondisi sekarang "
    "macetnya sekitar 7 sampai 8 menit, sesuai pengalaman kami di lapangan. Kendaraannya lima jenis: motor paling banyak "
    "dan bisa menyelip, mobil, angkot yang suka ngetem, serta truk dan bus yang lambat di tanjakan dan harus maju-mundur "
    "saat putar balik. Keempat kondisi, yaitu kondisi awal dan tiga usulan, diuji dengan jumlah kendaraan yang sama, lalu "
    "diulang lagi dengan arus 15 persen lebih padat untuk melihat mana yang tetap bertahan."))
stat(s, 1.12, 4.2, 5.6, 2.05, PINK, "±5.600", "kendaraan dalam 1 jam sibuk", vcolor=RED, vsize=50)
for i, (v, l) in enumerate([("±2.500", "turun dari Lembang"), ("±2.700", "naik dari kota"), ("±850", "keluar-masuk Gerlong")]):
    rect(s, 1.12, 6.45 + i * 0.85, 5.6, 0.75, LGRAY)
    tb(s, 1.4, 6.45 + i * 0.85, 1.9, 0.75, v, size=22, bold=True, color=BLUE, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, 3.3, 6.45 + i * 0.85, 3.3, 0.75, l, size=18, anchor=MSO_ANCHOR.MIDDLE)
tb(s, 1.12, 9.05, 5.6, 0.95, "Jumlah disetel agar kondisi sekarang macet ±7–8 menit, sesuai pengamatan lapangan.",
   size=16, italic=True)
veh = [("Motor", "paling banyak (±6 dari 10)", "Menyelip di antara mobil"),
       ("Mobil", "±3 dari 10", "Perlu waktu tambahan saat putar balik"),
       ("Angkot", "sedikit", "Sering ngetem di halte & mulut Gerlong"),
       ("Truk & bus", "sedikit, tapi berpengaruh besar", "Lambat di tanjakan; maju-mundur saat putar balik, menutup jalan")]
for i, (t, p, b) in enumerate(veh):
    x = 7.05 + (i % 2) * 5.98
    y = 4.2 + (i // 2) * 2.0
    hot = i == 3
    rect(s, x, y, 5.83, 1.82, RED if hot else GRAY)
    tb(s, x + 0.3, y + 0.15, 5.3, 0.55, t, size=24, bold=True, color="FFFFFF" if hot else RED)
    tb(s, x + 0.3, y + 0.7, 5.3, 0.4, p, size=15, bold=True, color="FFFFFF" if hot else NAVY)
    tb(s, x + 0.3, y + 1.08, 5.3, 0.7, b, size=17, color="FFFFFF" if hot else DARK)
rect(s, 7.05, 8.3, 11.82, 1.65, LBLUE)
tb(s, 7.35, 8.35, 11.3, 1.55, [[("Diuji: ", {"bold": True, "color": BLUE}),
                                ("kondisi awal + 3 usulan dengan kendaraan yang sama, lalu diulang dengan arus 15% lebih "
                                 "padat (akhir pekan / libur). Yang diukur: berapa lama kendaraan tertahan.", {})]],
   size=18, anchor=MSO_ANCHOR.MIDDLE)


# ------------------------------------------------------------------ slide per kondisi
def kondisi(code, title, sub, img, denah, what, note, pen, dmode="cover"):
    s = new(title, sub, pen, "SIMULASI", notes=note)
    pic(s, IMG[img], 1.12, 4.1, 8.6, 5.9)
    pic(s, IMG[denah], 9.95, 4.1, 3.9, 5.9, mode=dmode, border=GRAY)
    x0, w = 14.1, 4.77
    rect(s, x0, 4.1, w, 3.45, GRAY)
    tb(s, x0 + 0.3, 4.25, w - 0.5, 0.4, "APA YANG DILAKUKAN" if code != "S0" else "APA YANG TERJADI", size=14,
       bold=True, color=NAVY)
    tb(s, x0 + 0.3, 4.7, w - 0.5, 2.8, what, size=17, bullet=True, space=5)
    lg = loss(code, "SB_ger") / 60
    v = f"±{lg:.1f} menit".replace(".", ",") if lg >= 1.2 else "< 1,5 menit" if lg > 1 else "< 1 menit"
    rect(s, x0, 7.75, w, 2.25, PINK if code == "S0" else LBLUE)
    tb(s, x0 + 0.3, 7.9, w - 0.5, 1.0, v, size=40, bold=True, color=RED if code == "S0" else BLUE)
    tb(s, x0 + 0.3, 8.95, w - 0.5, 0.95, "waktu tertahan dari Lembang sampai masuk Gerlong", size=16)
    return s


kondisi("S0", "KONDISI AWAL", "Putar balik di bukaan A dan B, tanpa pengaturan", "s0", "denah0",
        ["Dari Lembang ke Gerlong harus putar balik dulu", "Yang menunggu putar balik memakan lajur",
         "Truk/bus maju-mundur, menutup dua arah", "Angkot ngetem di mulut Gerlong"],
        "Ini kondisi awal di simulasi 3D, di bukaan A. Kendaraan dari Lembang yang mau ke Gerlong menunggu celah untuk "
        "putar balik di lajur kanan, sehingga antrean memanjang ke atas. Sesekali truk atau bus maju-mundur dan menutup "
        "kedua arah. Rata-rata kendaraan dari Lembang tertahan sekitar tujuh setengah menit sebelum bisa masuk Gerlong. "
        "Angka ini menjadi pembanding untuk ketiga usulan.", 4)
kondisi("S0_tahap1", "USULAN 1: REKAYASA MURAH", "Jalan tetap, hanya aturan dan penertiban", "t1", "denah0",
        ["Rambu larangan putar balik untuk truk & bus", "Truk/bus memakai titik putar lain yang lebar",
         "Petugas di jam sibuk", "Angkot ngetem ditertibkan"],
        "Usulan pertama tidak mengubah jalan sama sekali, hanya aturan. Truk dan bus dilarang putar balik di sini dan "
        "diarahkan ke titik putar lain yang lebih lebar, ada petugas di jam sibuk, dan angkot dilarang ngetem di mulut "
        "Gerlong. Hasilnya langsung terasa: waktu tertahan dari Lembang ke Gerlong turun menjadi kurang dari satu menit. "
        "Artinya pemicu terbesar macet adalah manuver truk dan bus yang maju-mundur.", 4)
kondisi("S1", "USULAN 2: APILL ADAPTIF", "Median dibuka di mulut Gerlong, diatur lampu lalu lintas", "s1", "denah1",
        ["Median di depan Gerlong dibuka, bukaan A ditutup", "Lampu lalu lintas 2 fase yang menyesuaikan antrean",
         "Lajur kanan jadi lajur khusus belok kanan"],
        "Usulan kedua mengganti putar balik dengan belok kanan langsung ke Gerlong yang dilindungi lampu lalu lintas. "
        "Lampunya adaptif: lampu hijau untuk belok kanan hanya menyala selama ada kendaraan yang menunggu. Lajur kanan "
        "dijadikan lajur khusus belok kanan sehingga yang menunggu tidak menghalangi arus lurus. Waktu tertahan dari Lembang "
        "ke Gerlong menjadi sekitar satu menit. Konsekuensinya, arus lurus sesekali berhenti di lampu merah.", 5)
kondisi("S2", "USULAN 3: U-TURN LAYANG", "Putar balik lewat atas, tidak memotong arus", "s2", "denah2",
        ["Kendaraan putar balik lewat jembatan layang", "Turun kembali tepat sebelum Gerlong",
         "Butuh pelebaran jalan & pembebasan lahan"],
        "Usulan ketiga adalah U-turn layang. Kendaraan dari Lembang naik ke jembatan, berputar di atas, lalu turun kembali "
        "tepat sebelum Gerlong. Tidak ada lagi kendaraan yang memotong arus di bawah, sehingga hasilnya paling baik: waktu "
        "tertahan kurang dari satu menit dan antrean hampir hilang. Tetapi biayanya besar dan butuh pelebaran jalan serta "
        "lahan, jadi ini rencana jangka panjang.", 5, dmode="contain")

# ================================================================== SLIDE 13 — HASIL
mn = lambda v: round(v / 60, 1)
s = new("HASIL: WAKTU MACET", "Berapa lama kendaraan dari Lembang tertahan sampai masuk Gerlong (menit)", 6, "HASIL", notes=(
    "Ini hasil utamanya: berapa lama kendaraan dari Lembang tertahan sampai bisa masuk Gerlong. Batang abu-abu adalah "
    "kondisi jam sibuk biasa. Kondisi awal sekitar tujuh setengah menit, dan ketiga usulan sama-sama memangkasnya menjadi "
    "sekitar satu menit. Batang merah adalah saat arus 15 persen lebih padat, misalnya akhir pekan atau musim libur. "
    "Kondisi awal melonjak menjadi sekitar 17 menit. Di sini perbedaannya terlihat: rekayasa murah mulai goyah, sekitar "
    "5 menit, karena celah untuk putar balik makin jarang. APILL tetap sekitar 3 menit, dan flyover tetap paling baik "
    "sekitar satu setengah menit."))
bar(s, 1.12, 4.0, 11.6, 6.0, ["Kondisi awal", "Usulan 1", "Usulan 2", "Usulan 3"],
    [("Jam sibuk biasa", [mn(loss(x, "SB_ger")) for x in SC], "A7A9AC"),
     ("Arus +15%", [mn(SENS[x]["lg"][0]) for x in SC], RED)], size=18, gap=60, overlap=-5, fmt='0.0', lab_size=17)
stat(s, 13.1, 4.15, 5.77, 2.65, LBLUE, "±7,5 → ±1", "menit: semua usulan efektif di jam sibuk biasa", vcolor=BLUE, vsize=44,
     lsize=18)
stat(s, 13.1, 7.05, 5.77, 2.9, PINK, "Arus +15%", "Usulan 1 mulai goyah (±5 menit); Usulan 2 tetap ±3 menit; Usulan 3 "
     "terbaik", vcolor=RED, vsize=40, lsize=18)

# ================================================================== SLIDE 14 — REKOMENDASI
s = new("KESIMPULAN & REKOMENDASI", "Murah dan cepat dulu, lalu tingkatkan sesuai pertumbuhan arus", 6, "HASIL", notes=(
    "Kesimpulannya, macet di depan Gerlong terutama disebabkan oleh gerakan putar balik, khususnya truk dan bus, bukan "
    "semata banyaknya kendaraan. Rekomendasi kami bertahap. Sekarang: terapkan rekayasa murah karena biayanya kecil dan "
    "hasilnya langsung terasa. Bila arus terus bertambah: pasang APILL adaptif karena tetap stabil saat jalan lebih "
    "padat. Jangka panjang: kaji U-turn layang. Catatan kami, jumlah kendaraan dalam simulasi masih berdasarkan "
    "pengamatan, jadi langkah berikutnya adalah menghitung kendaraan langsung di lapangan untuk memperkuat hasil ini."))
plan = [("SEKARANG", "Usulan 1: Rekayasa murah", ["Larangan putar balik truk/bus", "Petugas jam sibuk", "Tertibkan ngetem"],
         RED, True),
        ("BILA ARUS NAIK", "Usulan 2: APILL adaptif", ["Buka median di mulut Gerlong", "Lampu adaptif + lajur khusus",
                                                      "Tetap stabil saat padat"], BLUE, True),
        ("JANGKA PANJANG", "Usulan 3: U-turn layang", ["Kajian kelayakan", "Pelebaran jalan & lahan", "Hasil terbaik"],
         GRAY, False)]
for i, (k, t, items, col, dark) in enumerate(plan):
    x = 1.12 + i * 6.05
    rect(s, x, 4.2, 5.6, 4.45, col)
    fg = "FFFFFF" if dark else DARK
    tb(s, x + 0.35, 4.4, 5.0, 0.4, k, size=16, bold=True, color="FFFFFF" if dark else NAVY)
    tb(s, x + 0.35, 4.85, 5.0, 1.1, t, size=27, bold=True, color="FFFFFF" if dark else RED)
    tb(s, x + 0.35, 6.1, 5.0, 2.5, items, size=22, color=fg, bullet="FFFFFF" if dark else RED, space=8)
    if i < 2:
        arrow(s, x + 5.62, 6.2, 0.4, 0.5, DARK)
rect(s, 1.12, 8.95, 17.75, 1.0, LGRAY)
tb(s, 1.42, 9.0, 17.2, 0.9, [[("Catatan: ", {"bold": True, "color": RED}),
                              ("jumlah kendaraan masih dari pengamatan; langkah berikutnya menghitung kendaraan langsung "
                               "di lapangan untuk memperkuat hasil.", {})]], size=18, anchor=MSO_ANCHOR.MIDDLE)

# ================================================================== SLIDE 15 — PENUTUP
s = new("TERIMA KASIH", "Sesi tanya jawab", 6, "PENUTUP", notes=(
    "Sebagai penutup: masalahnya adalah putar balik di depan Gerlong, solusinya bertahap dari rekayasa murah, APILL "
    "adaptif, sampai U-turn layang. Simulasi 3D-nya bisa kami tunjukkan langsung. Terima kasih, kami persilakan "
    "pertanyaan."))
pic(s, IMG["s1"], 1.12, 4.2, 9.6, 5.75)
rect(s, 11.05, 4.2, 7.82, 5.75, RED)
tb(s, 11.45, 4.5, 7.1, 0.9, "Ringkasnya", size=30, bold=True, color="FFFFFF")
tb(s, 11.45, 5.45, 7.1, 4.3, ["Macet disebabkan gerakan putar balik, terutama truk & bus",
                              "Rekayasa murah: efektif sekarang",
                              "APILL adaptif: siap saat arus naik",
                              "U-turn layang: solusi jangka panjang"], size=21, color="FFFFFF", bullet="FFFFFF", space=12)


# ------------------------------------------------------------------ simpan
prs.core_properties.title = "LKM 1 & 2 Transportasi – Puteran Jl. Dr. Setiabudi × Gerlong"
prs.save(OUT)
print("tersimpan:", OUT, "slide:", len(prs.slides))

# ------------------------------------------------------------------ naskah docx
from docx import Document  # noqa: E402
from docx.shared import Pt as DPt, RGBColor as DRGB  # noqa: E402

doc = Document()
st_ = doc.styles["Normal"]
st_.font.name = "Calibri"
st_.font.size = DPt(11)
h = doc.add_heading("Naskah Presentasi LKM 1 & 2 – Puteran Jl. Dr. Setiabudi × Gerlong", 0)
doc.add_paragraph("Pembagian enam penyaji, total ±25 menit. Naskah yang sama tersimpan di catatan pembicara (speaker notes) "
                  "setiap slide di file PPT. Angka berasal dari simulasi SUMO yang sudah dikalibrasi.")
t = doc.add_table(rows=1, cols=4)
t.style = "Light Grid Accent 2"
for i, h_ in enumerate(["Penyaji", "Bagian", "Slide", "Durasi"]):
    t.rows[0].cells[i].text = h_
for r in [("Penyaji 1", "Pembuka, pembagian, lokasi & kondisi nyata", "1–3", "±4 menit"),
          ("Penyaji 2", "Masalah lokal (LKM 1), akar masalah (LKM 2)", "4–5", "±4 menit"),
          ("Penyaji 3", "Strategi, alat yang dipakai, skema percobaan", "6–8", "±5 menit"),
          ("Penyaji 4", "Kondisi awal, usulan 1 rekayasa murah", "9–10", "±4 menit"),
          ("Penyaji 5", "Usulan 2 APILL adaptif, usulan 3 U-turn layang", "11–12", "±4 menit"),
          ("Penyaji 6", "Hasil waktu macet, rekomendasi, penutup", "13–15", "±4 menit")]:
    c = t.add_row().cells
    for i, v in enumerate(r):
        c[i].text = v
cur = None
for pen, no, title, note in sorted(NOTES, key=lambda x: x[1]):
    if pen != cur:
        cur = pen
        doc.add_heading(f"Penyaji {pen}", 1)
    p = doc.add_paragraph()
    r = p.add_run(f"Slide {no} – {title.title() if title.isupper() else title}")
    r.bold = True
    r.font.color.rgb = DRGB(0xC4, 0x16, 0x1C)
    doc.add_paragraph(note)
doc.add_heading("Antisipasi pertanyaan", 1)
for q, a in [
    ("Jumlah kendaraannya dari mana?", "Belum ada hitungan resmi, jadi jumlah kendaraan kami setel sampai kondisi sekarang "
     "macetnya sekitar 7–8 menit, sesuai pengalaman kami di lapangan. Lalu kami uji juga dengan arus 15% lebih padat."),
    ("Kenapa tidak langsung flyover?", "Flyover memang terbaik, tetapi mahal dan butuh pelebaran jalan serta lahan. Pada jam "
     "sibuk biasa, rekayasa murah dan APILL sudah memangkas waktu macet menjadi sekitar satu menit."),
    ("Kenapa rekayasa murah bisa sangat efektif?", "Truk dan bus yang maju-mundur saat putar balik menutup dua arah sekaligus. "
     "Begitu mereka tidak putar balik di sini, jalan kembali lancar. Tetapi saat arus lebih padat, celah untuk putar balik "
     "makin jarang sehingga usulan ini mulai goyah."),
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
doc.save(OUT_DOC)
print("tersimpan:", OUT_DOC)
