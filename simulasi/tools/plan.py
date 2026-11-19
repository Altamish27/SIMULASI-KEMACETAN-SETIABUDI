"""Gambar denah (tampak atas) tiap skenario dari jaringan SUMO + gedung OSM → results/gambar/denah_*.png"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

import geo  # noqa: E402
import sumolib  # noqa: E402

OUT = os.path.join(geo.ROOT, "results", "gambar")
TEXT, TEXT2, SURF = "#0b0b0b", "#52514e", "#fcfcfb"
TITLE = {"S0": "S0 Eksisting — bukaan A & B, median depan Gerlong tertutup",
         "S1": "S1 — APILL 2 fase adaptif + lajur khusus belok kanan (bukaan A ditutup)",
         "S2": "S2 — U-turn layang (putaran balik layang) + bukaan B dipindah"}


def draw(sc, xlim=(-90, 90), ylim=(-260, 190)):
    net = sumolib.net.readNet(os.path.join(geo.ROOT, "net", sc, "net.net.xml"), withInternal=True)
    common = json.load(open(os.path.join(geo.ROOT, "web", "data", "common.json"), encoding="utf-8"))
    scene = json.load(open(os.path.join(geo.ROOT, "web", "data", f"scene_{sc}.json"), encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(7.5, 11), dpi=160)
    fig.patch.set_facecolor(SURF)
    ax.set_facecolor("#eef0e6")
    for b in common["buildings"]:
        xs = [p[0] for p in b["p"]]
        ys = [p[1] for p in b["p"]]
        if max(xs) < xlim[0] - 20 or min(xs) > xlim[1] + 20 or max(ys) < ylim[0] - 20 or min(ys) > ylim[1] + 20:
            continue
        ax.add_patch(Polygon(b["p"], closed=True, fc="#d9d3c7", ec="#bdb5a6", lw=0.4))
    for r in common["roads"]:
        ax.plot([p[0] for p in r["p"]], [p[1] for p in r["p"]], color="#c4c4c0", lw=r["w"] * 0.9, solid_capstyle="round", zorder=1)
    for j in net.getNodes():
        sh = j.getShape()
        if len(sh) >= 3:
            ax.add_patch(Polygon(sh, closed=True, fc="#55585c", ec="none", zorder=2))
    for e in net.getEdges(withInternal=True):
        for ln in e.getLanes():
            sh = ln.getShape()
            if e.getID() == "FO":
                continue
            ax.plot([p[0] for p in sh], [p[1] for p in sh], color="#55585c", lw=ln.getWidth() * 2.6, solid_capstyle="butt", zorder=2)
    for pl in scene["median"]:
        ax.plot([p[0] for p in pl], [p[1] for p in pl], color="#9aa3ab", lw=2.2, zorder=4)
        ax.plot([p[0] for p in pl], [p[1] for p in pl], color="#ffffff", lw=0.7, ls=(0, (2, 2)), zorder=5)
    if "flyover" in scene:
        s = scene["flyover"]["s"]
        ax.plot([p[0] for p in s], [p[1] for p in s], color="#eda100", lw=9, alpha=0.85, zorder=6, solid_capstyle="round")
        for pr in scene["flyover"]["piers"]:
            ax.plot(pr[0], pr[1], "s", color="#6d6a66", ms=3.5, zorder=7)
    # anotasi
    def note(x, y, t, dx=28, dy=0, c=TEXT):
        ax.annotate(t, (x, y), (x + dx, y + dy), fontsize=8, color=c, zorder=9,
                    arrowprops=dict(arrowstyle="-", color=TEXT2, lw=0.7),
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c9c6bf", lw=0.6))
    ax_ = geo.setiabudi_axis()
    P = lambda y: geo.point_at(ax_, geo.s_at_y(ax_, y))  # noqa: E731
    G = P(-33.5)
    note(-60, -22, "Jl. Gegerkalong Girang\n(Gerlong)", dx=-10, dy=40)
    if sc == "S0":
        a = P(-67); note(a[0], a[1], "Bukaan A: dari Lembang\nputar balik → Gerlong", dx=35, dy=-30)
        b = P(72); note(b[0], b[1], "Bukaan B: dari bawah\nputar balik", dx=38, dy=10)
        note(G[0], G[1], "Median tertutup\ndi depan Gerlong", dx=40, dy=8)
    elif sc == "S1":
        note(G[0], G[1], "APILL 2 fase adaptif\n(belok kanan terlindung)", dx=40, dy=-6)
        q = P(5); note(q[0], q[1], "Lajur khusus belok\nkanan 60 m", dx=40, dy=12)
        b = P(72); note(b[0], b[1], "Bukaan B (kendaraan kecil)", dx=38, dy=10)
        a = P(-67); note(a[0], a[1], "Bukaan A ditutup", dx=35, dy=-25)
    else:
        f = P(95); note(f[0] + 5, f[1], "Ramp naik (dari arah\nLembang, lajur median)", dx=35, dy=25)
        lp = P(-215); note(lp[0], lp[1], "Loop R 13 m\n(pembebasan lahan)", dx=40, dy=0)
        d = P(-100); note(d[0] - 5, d[1], "Mendarat → belok\nkiri ke Gerlong", dx=-75, dy=-25)
        b = P(150); note(b[0], b[1], "Bukaan B dipindah", dx=25, dy=20)
    ax.annotate("", (xlim[1] - 12, ylim[1] - 12), (xlim[1] - 12, ylim[1] - 40), arrowprops=dict(arrowstyle="-|>", color=TEXT, lw=1.4))
    ax.text(xlim[1] - 12, ylim[1] - 8, "U", ha="center", fontsize=10, fontweight="bold", color=TEXT)
    ax.text(xlim[0] + 6, ylim[1] - 14, "↑ ke UPI / Lembang (menanjak 4,9%)", fontsize=8, color=TEXT2)
    ax.text(xlim[0] + 6, ylim[0] + 8, "↓ ke kota", fontsize=8, color=TEXT2)
    ax.plot([xlim[0] + 8, xlim[0] + 58], [ylim[0] + 22, ylim[0] + 22], color=TEXT, lw=2)
    ax.text(xlim[0] + 33, ylim[0] + 26, "50 m", ha="center", fontsize=8, color=TEXT)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#c9c6bf")
    ax.set_title(TITLE[sc], loc="left", fontsize=10, color=TEXT, fontweight="bold")
    os.makedirs(OUT, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"denah_{sc}.png"), facecolor=SURF)
    plt.close(fig)
    print("denah", sc)


if __name__ == "__main__":
    for sc in sys.argv[1:] or ["S0", "S1", "S2"]:
        draw(sc)
