"""Gabungkan hasil semua run (rata-rata ± simpangan antar seed) → tabel Markdown, JSON, dan grafik PNG.

python tools/report.py
"""
import csv
import glob
import json
import os
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

SCEN = [
    ("S0", "S0 Eksisting"),
    ("S0_tahap1", "Tahap 1: larang truk/bus putar balik + tertib angkot"),
    ("S1", "S1: APILL adaptif + lajur khusus belok kanan"),
    ("S2", "S2: U-turn layang"),
]
SHORT = {"S0": "S0 Eksisting", "S0_tahap1": "Tahap 1 (murah)", "S1": "S1 APILL", "S2": "S2 Flyover"}
# palet kategorikal referensi (slot 1–4, urutan tetap)
COLOR = {"S0": "#2a78d6", "S0_tahap1": "#eb6834", "S1": "#1baf7a", "S2": "#eda100"}
OD = [
    ("SB_ger", "Lembang → Gerlong"),
    ("SB_thru", "Lurus turun"),
    ("NB_thru", "Lurus naik"),
    ("NB_ger", "Bawah → Gerlong"),
    ("GER_north", "Gerlong → atas"),
    ("GER_south", "Gerlong → bawah"),
    ("SB_uturn", "Atas → putar balik"),
    ("NB_uturn", "Bawah → putar balik"),
]
CORR = [("turun", "Arah turun"), ("naik", "Arah naik"), ("gerlong", "Jl. Gegerkalong Girang")]
TEXT, TEXT2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def ms(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, None
    return statistics.mean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0.0)


def collect():
    data = {}
    for sc, _ in SCEN:
        runs = []
        for f in sorted(glob.glob(os.path.join(RES, "runs", f"{sc}_seed*", "summary.json"))):
            runs.append(json.load(open(f, encoding="utf-8")))
        if not runs:
            continue
        d = {"n_seed": len(runs), "od": {}}
        for key in ("tundaan_rata_semua_s", "kendaraan_diukur", "belum_selesai", "teleport"):
            d[key] = ms([r.get(key) for r in runs])
        for c, _ in CORR:
            d[f"antrean_{c}_rata_m"] = ms([r.get(f"antrean_{c}_rata_m") for r in runs])
            d[f"antrean_{c}_p95_m"] = ms([r.get(f"antrean_{c}_p95_m") for r in runs])
        for od, _ in OD:
            d["od"][od] = {
                "tt": ms([r["od"].get(od, {}).get("waktu_tempuh_rata_s") for r in runs]),
                "loss": ms([r["od"].get(od, {}).get("tundaan_rata_s") for r in runs]),
                "n": ms([r["od"].get(od, {}).get("n") for r in runs]),
            }
        data[sc] = d
    return data


def style(ax, title, xlabel):
    ax.set_facecolor(SURF)
    ax.set_title(title, loc="left", fontsize=12, color=TEXT, pad=12, fontweight="bold")
    ax.set_xlabel(xlabel, color=TEXT2, fontsize=9)
    ax.tick_params(colors=TEXT2, labelsize=9, length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def grouped_hbar(fname, title, xlabel, cats, getter, scen):
    fig, ax = plt.subplots(figsize=(10, 0.9 + 0.62 * len(cats) * 1.0 + 0.4), dpi=150)
    fig.patch.set_facecolor(SURF)
    n = len(scen)
    h = 0.8 / n
    for i, sc in enumerate(scen):
        ys, ws, es = [], [], []
        for j, (k, _) in enumerate(cats):
            m, s = getter(sc, k)
            ys.append(j + (i - (n - 1) / 2) * h)
            ws.append(m or 0)
            es.append(s or 0)
        ax.barh(ys, ws, height=h - 0.03, color=COLOR[sc], label=SHORT[sc], xerr=es,
                error_kw={"ecolor": TEXT2, "elinewidth": 0.8, "capsize": 2}, edgecolor=SURF, linewidth=1)
        for y, w in zip(ys, ws):
            if w:
                ax.text(w + max(es) * 0 + 4, y, f"{w:.0f}", va="center", fontsize=7, color=TEXT2)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels([l for _, l in cats], color=TEXT)
    ax.invert_yaxis()
    style(ax, title, xlabel)
    ax.legend(loc="lower right", frameon=False, fontsize=8, labelcolor=TEXT)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, fname), facecolor=SURF)
    plt.close(fig)


def bar_simple(fname, title, xlabel, data, key):
    scen = [s for s, _ in SCEN if s in data]
    fig, ax = plt.subplots(figsize=(10, 2.8), dpi=150)
    fig.patch.set_facecolor(SURF)
    vals = [data[s][key][0] for s in scen]
    errs = [data[s][key][1] for s in scen]
    ax.barh(range(len(scen)), vals, height=0.55, color=[COLOR[s] for s in scen], xerr=errs,
            error_kw={"ecolor": TEXT2, "elinewidth": 0.8, "capsize": 2})
    for i, v in enumerate(vals):
        ax.text(v + 5, i, f"{v:.0f} s", va="center", fontsize=9, color=TEXT)
    ax.set_yticks(range(len(scen)))
    ax.set_yticklabels([SHORT[s] for s in scen], color=TEXT)
    ax.invert_yaxis()
    style(ax, title, xlabel)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, fname), facecolor=SURF)
    plt.close(fig)


def timeseries(fname, corridor, label):
    fig, ax = plt.subplots(figsize=(10, 4.0), dpi=150)
    fig.patch.set_facecolor(SURF)
    for sc, _ in SCEN:
        f = os.path.join(RES, "runs", f"{sc}_seed1", "queues.csv")
        if not os.path.exists(f):
            continue
        rows = list(csv.DictReader(open(f)))
        t = [float(r["t"]) / 60 for r in rows]
        v = [float(r[corridor]) for r in rows]
        # rata-rata bergerak 1 menit
        k = 12
        sm = [sum(v[max(0, i - k):i + 1]) / len(v[max(0, i - k):i + 1]) for i in range(len(v))]
        ax.plot(t, sm, color=COLOR[sc], linewidth=2, label=SHORT[sc])
    ax.axvspan(0, 10, color=GRID, alpha=0.5, linewidth=0)
    ax.text(5, 0.97, "pemanasan", fontsize=8, color=TEXT2, ha="center", va="top", transform=ax.get_xaxis_transform())
    style(ax, f"Panjang jalan tersendat — {label} (seed 1)", "menit simulasi")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_ylabel("meter", color=TEXT2, fontsize=9)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False, fontsize=8, ncol=4, labelcolor=TEXT)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, fname), facecolor=SURF)
    plt.close(fig)


def fmt(m):
    return "–" if m is None or m[0] is None else f"{m[0]:.0f} ± {m[1]:.0f}"


def main():
    data = collect()
    scen = [s for s, _ in SCEN if s in data]
    json.dump(data, open(os.path.join(RES, "ringkasan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    grouped_hbar("grafik_waktu_tempuh.png", "Waktu tempuh rata-rata per pergerakan (detik, ±1 sd antar seed)",
                 "detik", OD, lambda s, k: data[s]["od"][k]["tt"], scen)
    grouped_hbar("grafik_tundaan_pergerakan.png", "Tundaan di simpang Gerlong per pergerakan (detik, ±1 sd antar seed)",
                 "detik", OD, lambda s, k: data[s]["od"][k]["loss"], scen)
    grouped_hbar("grafik_antrean.png", "Panjang jalan tersendat rata-rata (meter)", "meter", CORR,
                 lambda s, k: data[s][f"antrean_{k}_rata_m"], scen)
    bar_simple("grafik_tundaan.png", "Tundaan rata-rata seluruh kendaraan (detik/kendaraan)", "detik",
               data, "tundaan_rata_semua_s")
    timeseries("grafik_antrean_turun_waktu.png", "turun", "arah turun (dari Lembang)")
    timeseries("grafik_antrean_naik_waktu.png", "naik", "arah naik (dari kota)")

    L = ["# Ringkasan Hasil Simulasi — Puteran Jl. Dr. Setiabudi × Gerlong", "",
         f"Jam puncak 60 menit (setelah pemanasan 10 menit), {data[scen[0]]['n_seed']} seed acak per skenario. "
         "Nilai = rata-rata ± simpangan baku antar seed. Volume = asumsi jam puncak yang DIKALIBRASI (70% asumsi awal = "
         "5.656 kend/jam) agar tundaan S0 dari Lembang → Gerlong sesuai pengamatan lapangan (macet biasa, < 10 menit). "
         "Tundaan = tambahan waktu dibanding jalan lancar, termasuk menunggu di antrean akibat simpang/puteran.", "",
         "## Skenario"]
    for s, l in SCEN:
        if s in data:
            L.append(f"- **{SHORT[s]}** — {l}")
    L += ["", "## Indikator utama", "",
          "| Indikator | " + " | ".join(SHORT[s] for s in scen) + " |",
          "|---|" + "---|" * len(scen),
          "| Tundaan rata-rata semua kendaraan (s) | " + " | ".join(fmt(data[s]["tundaan_rata_semua_s"]) for s in scen) + " |"]
    for c, l in CORR:
        L.append(f"| Panjang tersendat {l} (m) | " + " | ".join(fmt(data[s][f'antrean_{c}_rata_m']) for s in scen) + " |")
    L.append("| Kendaraan selesai diukur | " + " | ".join(fmt(data[s]["kendaraan_diukur"]) for s in scen) + " |")
    L += ["", "## Tundaan di simpang Gerlong per pergerakan (detik) — indikator utama", "",
          "| Pergerakan | " + " | ".join(SHORT[s] for s in scen) + " |", "|---|" + "---|" * len(scen)]
    for od, l in OD:
        L.append(f"| {l} | " + " | ".join(fmt(data[s]["od"][od]["loss"]) for s in scen) + " |")
    L += ["", "## Perubahan tundaan terhadap S0", "",
          "| Pergerakan | " + " | ".join(SHORT[s] for s in scen[1:]) + " |", "|---|" + "---|" * (len(scen) - 1)]
    for od, l in OD:
        base = data["S0"]["od"][od]["loss"][0] if "S0" in data else None
        cells = []
        for s in scen[1:]:
            v = data[s]["od"][od]["loss"][0]
            cells.append("–" if not base or v is None else f"{(v - base) / base * 100:+.0f}%")
        L.append(f"| {l} | " + " | ".join(cells) + " |")
    L += ["", "## Waktu tempuh rata-rata per pergerakan (detik)", "",
          "Diukur dari batas model (±450 m dari mulut Gerlong) sampai keluar model; rute S2 lebih panjang karena loop flyover.", "",
          "| Pergerakan | " + " | ".join(SHORT[s] for s in scen) + " |", "|---|" + "---|" * len(scen)]
    for od, l in OD:
        L.append(f"| {l} | " + " | ".join(fmt(data[s]["od"][od]["tt"]) for s in scen) + " |")
    L += ["", "## Perubahan terhadap S0 (waktu tempuh)", "",
          "| Pergerakan | " + " | ".join(SHORT[s] for s in scen[1:]) + " |", "|---|" + "---|" * (len(scen) - 1)]
    for od, l in OD:
        base = data["S0"]["od"][od]["tt"][0] if "S0" in data else None
        cells = []
        for s in scen[1:]:
            v = data[s]["od"][od]["tt"][0]
            cells.append("–" if not base or v is None else f"{(v - base) / base * 100:+.0f}%")
        L.append(f"| {l} | " + " | ".join(cells) + " |")
    sens = {}
    for sc, _ in SCEN:
        runs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(RES, "runs", f"{sc}_p15_seed*", "summary.json")))]
        if runs:
            sens[sc] = {"n": len(runs), "delay": ms([r["tundaan_rata_semua_s"] for r in runs]),
                        "lg": ms([r["od"].get("SB_ger", {}).get("tundaan_rata_s") for r in runs]),
                        "sbt": ms([r["od"].get("SB_thru", {}).get("tundaan_rata_s") for r in runs]),
                        "nbt": ms([r["od"].get("NB_thru", {}).get("tundaan_rata_s") for r in runs]),
                        "qg": ms([r.get("antrean_gerlong_rata_m") for r in runs])}
    if sens:
        sc_s = [s for s, _ in SCEN if s in sens]
        L += ["", "## Uji sensitivitas: arus jam puncak +15%", "",
              f"{sens[sc_s[0]]['n']} seed per skenario. Tujuannya memeriksa apakah urutan/kesimpulan berubah bila arus lebih padat dari hasil kalibrasi.", "",
              "| Indikator | " + " | ".join(SHORT[s] for s in sc_s) + " |", "|---|" + "---|" * len(sc_s)]
        for key, lab in (("delay", "Tundaan rata-rata semua (s)"), ("lg", "Tundaan Lembang → Gerlong (s)"), ("sbt", "Tundaan lurus turun (s)"), ("nbt", "Tundaan lurus naik (s)"), ("qg", "Antrean Gerlong (m)")):
            L.append(f"| {lab} | " + " | ".join(fmt(sens[s][key]) for s in sc_s) + " |")
        data["_sensitivitas_p15"] = sens
        json.dump(data, open(os.path.join(RES, "ringkasan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    ctl = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(RES, "runs", "S0_lurus_seed*", "summary.json")))]
    if ctl and "S0" in data:
        d0 = data["S0"]
        L += ["", "## Uji kontrol (validasi logika)", "",
              f"S0 dengan arus utama yang sama tetapi semua kendaraan lurus (tanpa belok/putar balik), {len(ctl)} seed:", "",
              "| Indikator | Uji kontrol (semua lurus) | S0 dengan puteran |", "|---|---|---|",
              f"| Tundaan rata-rata (s) | {fmt(ms([r['tundaan_rata_semua_s'] for r in ctl]))} | {fmt(d0['tundaan_rata_semua_s'])} |",
              f"| Tundaan lurus turun (s) | {fmt(ms([r['od'].get('SB_thru', {}).get('tundaan_rata_s') for r in ctl]))} | {fmt(d0['od']['SB_thru']['loss'])} |",
              f"| Antrean arah turun (m) | {fmt(ms([r.get('antrean_turun_rata_m') for r in ctl]))} | {fmt(d0['antrean_turun_rata_m'])} |"]
        data["_kontrol"] = {"delay": ms([r["tundaan_rata_semua_s"] for r in ctl]),
                            "sbt": ms([r["od"].get("SB_thru", {}).get("tundaan_rata_s") for r in ctl]),
                            "qt": ms([r.get("antrean_turun_rata_m") for r in ctl])}
        json.dump(data, open(os.path.join(RES, "ringkasan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    L += ["", "Grafik: `grafik_tundaan_pergerakan.png`, `grafik_waktu_tempuh.png`, `grafik_antrean.png`, `grafik_tundaan.png`, "
          "`grafik_antrean_turun_waktu.png`, `grafik_antrean_naik_waktu.png`."]
    open(os.path.join(RES, "ringkasan.md"), "w", encoding="utf-8").write("\n".join(L))
    # salin ke aplikasi web (halaman hasil.html)
    import shutil
    web = os.path.join(ROOT, "web", "hasil")
    os.makedirs(web, exist_ok=True)
    for f in glob.glob(os.path.join(RES, "grafik_*.png")) + [os.path.join(RES, "ringkasan.json"), os.path.join(RES, "ringkasan.md")]:
        shutil.copy(f, web)
    print("\n".join(L))


if __name__ == "__main__":
    main()
