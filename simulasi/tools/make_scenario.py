"""Buat demand (rute + arus jam puncak), tipe kendaraan, halte/ngetem angkot, dan program APILL.

Volume = ASUMSI jam puncak (tidak ada hitungan lapangan). VOLUMES di bawah = asumsi awal; arus yang
dipakai = VOLUMES × KALIBRASI. Faktor KALIBRASI dipilih agar tundaan S0 "dari Lembang → Gerlong"
cocok dengan pengalaman lapangan (macet biasa, < 10 menit). Semua bisa diskalakan lagi dengan --scale.

Pemakaian: python tools/make_scenario.py [S0 S1 S2] [--scale 1.0]
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import geo  # noqa: E402
import sumolib  # noqa: E402

SCEN_DIR = os.path.join(geo.ROOT, "scenarios")

# ------------------------------------------------------------------ ASUMSI VOLUME (kend/jam)
# Kalibrasi 23-11-2026: uji S0 pada 50/60/70/80/100% asumsi awal → tundaan Lembang→Gerlong
# 0,5 / 0,9 / 8,2 / 16 / 27 menit. Pengamatan lapangan: "macet biasa, kurang dari 10 menit" → 0,70.
KALIBRASI = 0.70
VOLUMES = {  # asumsi awal (sebelum kalibrasi)
    "SB_total": 3600,   # arus dari atas (Lembang/UPI) ke bawah
    "NB_total": 3800,   # arus dari bawah (kota) ke atas
    "SB_ger": 280,      # dari atas → Gerlong (gerakan utama yang dipersoalkan)
    "SB_uturn": 90,     # dari atas putar balik ke atas
    "SB_kah": 40,       # dari atas → Jl. Kapten Abdul Hamid
    "NB_ger": 320,      # dari bawah → Gerlong (belok kiri)
    "NB_uturn": 140,    # dari bawah putar balik ke bawah
    "NB_kah": 30,
    "GER_north": 350,   # keluar Gerlong → atas
    "GER_south": 260,   # keluar Gerlong → bawah
    "KAH_south": 40,
    "KAH_north": 30,
}
# komposisi (proporsi) — dari pengamatan video: motor dominan, angkot hijau, dump truck, bus
MIX = {
    "main": {"motor": 0.62, "mobil": 0.27, "angkot": 0.05, "truk": 0.035, "bus": 0.025},
    "turn": {"motor": 0.63, "mobil": 0.27, "angkot": 0.05, "truk": 0.035, "bus": 0.015},
    "ger":  {"motor": 0.65, "mobil": 0.27, "angkot": 0.06, "truk": 0.02, "bus": 0.0},
    "kah":  {"motor": 0.80, "mobil": 0.20},
}
HEAVY = ("truk", "bus")

VTYPES = """
  <!-- Motor: menyelip (sublane), agresif khas lalu lintas Bandung -->
  <vType id="motor" vClass="motorcycle" length="1.95" width="0.75" height="1.4" minGap="0.8" maxSpeed="16.7"
         accel="3.2" decel="6.0" emergencyDecel="9" sigma="0.6" tau="0.6" speedFactor="normc(1.05,0.15,0.6,1.5)"
         latAlignment="arbitrary" minGapLat="0.25" maxSpeedLat="1.6" lcStrategic="2" lcCooperative="0.3"
         lcSpeedGain="3" lcKeepRight="0" lcPushy="0.9" lcImpatience="0.9" lcAssertive="2.5"
         jmDriveAfterRedTime="1.5" jmIgnoreKeepClearTime="8" impatience="0.9" color="0.95,0.4,0.1" guiShape="motorcycle"/>
  <vType id="mobil" vClass="passenger" length="4.3" width="1.75" height="1.5" minGap="1.8" maxSpeed="22"
         accel="2.4" decel="4.5" sigma="0.5" tau="1.0" speedFactor="normc(1,0.1,0.6,1.3)"
         latAlignment="center" minGapLat="0.45" lcPushy="0.3" lcAssertive="1.3" lcImpatience="0.5"
         impatience="0.6" color="0.85,0.85,0.88" guiShape="passenger"/>
  <!-- Angkot hijau (Suzuki Carry): sering berhenti/ngetem — diatur oleh pengendali TraCI -->
  <vType id="angkot" vClass="passenger" length="3.95" width="1.6" height="1.9" minGap="1.5" maxSpeed="16"
         accel="1.8" decel="4.0" sigma="0.6" tau="0.9" lcPushy="0.6" lcAssertive="1.6" impatience="0.8"
         color="0.1,0.6,0.3" guiShape="passenger/van"/>
  <!-- Dump truck engkel bermuatan -->
  <vType id="truk" vClass="truck" length="6.8" width="2.4" height="3.0" minGap="2.5" maxSpeed="15"
         accel="0.9" decel="3.8" sigma="0.4" tau="1.3" lcAssertive="1" impatience="0.5" color="0.9,0.8,0.1" guiShape="truck"/>
  <!-- Bus sedang (arah Lembang) -->
  <vType id="bus" vClass="bus" length="9.5" width="2.5" height="3.2" minGap="2.5" maxSpeed="14"
         accel="0.9" decel="3.5" sigma="0.3" tau="1.3" color="0.2,0.7,0.3" guiShape="bus"/>
  <!-- Varian menanjak (±5%): akselerasi & kecepatan kendaraan berat turun -->
  <vType id="truk_naik" vClass="truck" length="6.8" width="2.4" height="3.0" minGap="2.5" maxSpeed="9"
         accel="0.5" decel="3.8" sigma="0.4" tau="1.3" impatience="0.5" color="0.9,0.8,0.1" guiShape="truck"/>
  <vType id="bus_naik" vClass="bus" length="9.5" width="2.5" height="3.2" minGap="2.5" maxSpeed="10"
         accel="0.6" decel="3.5" sigma="0.3" tau="1.3" impatience="0.5" color="0.2,0.7,0.3" guiShape="bus"/>
"""


# ------------------------------------------------------------------ rute per skenario
def routes_for(sc):
    if sc == "S0":
        SB = ["SB_N_B", "SB_B_G", "SB_G_A"]
        NB = ["NB_S_A", "NB_A_G"]
        return {
            "SB_thru": SB + ["SB_A_S"],
            "SB_ger": SB + ["NB_A_G", "GER_out"],
            "SB_uturn": SB + ["NB_A_G", "NB_G_B", "NB_B_N"],
            "SB_kah": SB + ["KAH_out"],
            "NB_thru": NB + ["NB_G_B", "NB_B_N"],
            "NB_ger": NB + ["GER_out"],
            "NB_uturn": NB + ["NB_G_B", "SB_B_G", "SB_G_A", "SB_A_S"],
            "NB_kah": ["NB_S_A", "KAH_out"],
            "GER_north": ["GER_in", "NB_G_B", "NB_B_N"],
            "GER_south": ["GER_in", "NB_G_B", "SB_B_G", "SB_G_A", "SB_A_S"],
            "KAH_south": ["KAH_in", "SB_A_S"],
            "KAH_north": ["KAH_in", "NB_A_G", "NB_G_B", "NB_B_N"],
        }
    if sc == "S1":
        SB = ["SB_N_B", "SB_B_Gq", "SB_Gq_G"]
        NB = ["NB_S_A", "NB_A_G"]
        return {
            "SB_thru": SB + ["SB_G_A", "SB_A_S"],
            "SB_ger": SB + ["GER_out"],
            "SB_uturn": SB + ["NB_G_Gq", "NB_Gq_B", "NB_B_N"],
            "SB_kah": SB + ["SB_G_A", "KAH_out"],
            "NB_thru": NB + ["NB_G_Gq", "NB_Gq_B", "NB_B_N"],
            "NB_ger": NB + ["GER_out"],
            "NB_uturn": NB + ["NB_G_Gq", "NB_Gq_B", "SB_B_Gq", "SB_Gq_G", "SB_G_A", "SB_A_S"],
            "NB_kah": NB + ["NB_G_Gq", "NB_Gq_B", "SB_B_Gq", "SB_Gq_G", "SB_G_A", "KAH_out"],
            "GER_north": ["GER_in", "NB_G_Gq", "NB_Gq_B", "NB_B_N"],
            "GER_south": ["GER_in", "NB_G_Gq", "NB_Gq_B", "SB_B_Gq", "SB_Gq_G", "SB_G_A", "SB_A_S"],
            "KAH_south": ["KAH_in", "SB_A_S"],
            "KAH_north": ["KAH_in", "SB_A_S"],  # A ditutup: keluar lewat selatan
        }
    if sc == "S2":
        SB = ["SB_N_B", "SB_B_Fu"]
        NB = ["NB_S_Fd", "NB_Fd_A", "NB_A_G"]
        return {
            "SB_thru": SB + ["SB_Fu_G", "SB_G_A", "SB_A_S"],
            "SB_ger": SB + ["FO", "NB_Fd_A", "NB_A_G", "GER_out"],
            "SB_uturn": SB + ["FO", "NB_Fd_A", "NB_A_G", "NB_G_B", "NB_B_N"],
            "SB_kah": SB + ["SB_Fu_G", "SB_G_A", "KAH_out"],
            "NB_thru": NB + ["NB_G_B", "NB_B_N"],
            "NB_ger": NB + ["GER_out"],
            "NB_uturn": NB + ["NB_G_B", "SB_B_Fu", "SB_Fu_G", "SB_G_A", "SB_A_S"],
            "NB_kah": NB + ["NB_G_B", "SB_B_Fu", "SB_Fu_G", "SB_G_A", "KAH_out"],
            "GER_north": ["GER_in", "NB_G_B", "NB_B_N"],
            "GER_south": ["GER_in", "NB_G_B", "SB_B_Fu", "SB_Fu_G", "SB_G_A", "SB_A_S"],
            "KAH_south": ["KAH_in", "SB_A_S"],
            "KAH_north": ["KAH_in", "SB_A_S"],
        }
    raise ValueError(sc)


def heavy_banned(sc, rname, variant=None):
    """Larangan truk/bus putar balik (bagian dari semua solusi; S0 eksisting tanpa larangan)."""
    if sc == "S0" and variant == "tahap1":
        return rname in ("SB_ger", "SB_uturn", "NB_uturn", "GER_south")
    if sc == "S1":
        return rname in ("SB_uturn", "NB_uturn", "GER_south")   # belok kanan ke Gerlong dilindungi lampu: truk boleh
    if sc == "S2":
        return rname in ("NB_uturn", "GER_south")
    return False


def build_flows(sc, scale=1.0, variant=None):
    V = dict(VOLUMES)
    if variant == "lurus":  # uji kontrol: arus total sama, semua lurus (tanpa belok/putar balik)
        for k in V:
            if not k.endswith("total"):
                V[k] = 0
    V["SB_thru"] = V["SB_total"] - V["SB_ger"] - V["SB_uturn"] - V["SB_kah"]
    V["NB_thru"] = V["NB_total"] - V["NB_ger"] - V["NB_uturn"] - V["NB_kah"]
    routes = routes_for(sc)
    flows = []  # (route, vtype, vph)
    moved = {"SB_thru": {}, "NB_thru": {}}
    for r in routes:
        mix = MIX["main"] if r.endswith("thru") else MIX["ger"] if r.startswith("GER") or r.endswith("ger") \
            else MIX["kah"] if "KAH" in r or r.endswith("kah") else MIX["turn"]
        for vt, share in mix.items():
            vph = V[r] * share * scale * KALIBRASI
            if vt in HEAVY and heavy_banned(sc, r, variant):
                # tetap ada di jaringan sebagai arus lurus (dialihkan ke titik putar lain di luar area)
                tgt = "SB_thru" if r.startswith("SB") else "NB_thru"
                moved[tgt][vt] = moved[tgt].get(vt, 0) + vph
                continue
            flows.append([r, vt, vph])
    for f in flows:
        if f[0] in moved and f[1] in moved[f[0]]:
            f[2] += moved[f[0]][f[1]]
    return routes, flows


def uphill(rname):
    return rname.startswith("NB") or rname.startswith("GER_north") or rname == "KAH_north"


def write_routes(sc, scale, begin=0, end=4200, variant=None, folder=None):
    routes, flows = build_flows(sc, scale, variant)
    d = os.path.join(SCEN_DIR, folder or sc)
    os.makedirs(d, exist_ok=True)
    out = ["<routes>", VTYPES]
    for r, edges in routes.items():
        out.append(f'  <route id="{r}" edges="{" ".join(edges)}"/>')
    for r, vt, vph in flows:
        if vph < 0.5:
            continue
        t = vt
        if vt in HEAVY and uphill(r):
            t = vt + "_naik"
        lat = 'departPosLat="random"' if vt == "motor" else ""
        out.append(
            f'  <flow id="{r}__{vt}" type="{t}" route="{r}" begin="{begin}" end="{end}" '
            f'period="exp({vph / 3600:.6f})" departLane="best" departSpeed="avg" {lat}/>'
        )
    out.append("</routes>")
    open(os.path.join(d, "routes.rou.xml"), "w", encoding="utf-8").write("\n".join(out))
    return flows


# ------------------------------------------------------------------ halte & ngetem
def locate(net, pt, prefixes, lane_index=0):
    """Cari lane (indeks tertentu) pada edge berawalan tertentu yang paling dekat ke pt; kembalikan (laneID, pos)."""
    best = None
    for e in net.getEdges():
        if not any(e.getID().startswith(p) for p in prefixes):
            continue
        if lane_index >= len(e.getLanes()):
            continue
        ln = e.getLanes()[lane_index]
        shape = ln.getShape()
        pos = geo.project(shape, pt)
        q = geo.point_at(shape, pos)
        dist = math.dist(q, pt)
        if best is None or dist < best[0]:
            best = (dist, ln.getID(), pos, ln.getLength())
    return best[1], best[2], best[3]


def write_additional(sc, net, folder=None):
    d = os.path.join(SCEN_DIR, folder or sc)
    add = ["<additional>"]
    stops = {}
    # Halte TfB "Gegerkalong Girang" (y≈-89, sisi barat/jalur naik)
    ln, pos, L = locate(net, (-17, -89), ("NB_",))
    add.append(f'  <busStop id="halte_GG" lane="{ln}" startPos="{max(0, pos - 12):.1f}" endPos="{min(L, pos + 6):.1f}" '
               f'name="Halte Gegerkalong Girang" lines="angkot"/>')
    stops["halte_GG"] = ln.rsplit("_", 1)[0]
    # Titik ngetem angkot: tepat sebelum mulut Gerlong (jalur naik) & di mulut Gerlong
    if sc != "S1":
        ln, pos, L = locate(net, (-10, -16), ("NB_",))
        add.append(f'  <busStop id="ngetem_NB" lane="{ln}" startPos="{max(0, pos - 10):.1f}" endPos="{min(L, pos + 4):.1f}" '
                   f'name="Ngetem sudut Gerlong (J&amp;T)" lines="angkot"/>')
        stops["ngetem_NB"] = ln.rsplit("_", 1)[0]
    ger = net.getEdge("GER_in")
    L = ger.getLength()
    add.append(f'  <busStop id="ngetem_GER" lane="GER_in_0" startPos="{L - 30:.1f}" endPos="{L - 14:.1f}" '
               f'name="Ngetem mulut Gerlong" lines="angkot"/>')
    stops["ngetem_GER"] = "GER_in"
    if sc == "S1":
        add.append(tls_program(net))
    add.append("</additional>")
    open(os.path.join(d, "stops.add.xml"), "w", encoding="utf-8").write("\n".join(add))
    return stops


# ------------------------------------------------------------------ program APILL S1
TLS_DEFAULT = {"g1min": 30, "g1max": 70, "g2min": 5, "g2max": 14, "y": 3, "ar": 2}


def tls_classes(net):
    tl = net.getTLS("G")
    cls = {}
    for (inl, outl, idx) in tl.getConnections():
        fe, te = inl.getEdge().getID(), outl.getEdge().getID()
        if fe.startswith("NB"):
            c = "NB_left" if te == "GER_out" else "NB_uturn" if te.startswith("SB") else "NB_thru"
        elif fe.startswith("SB"):
            c = "SB_right" if te == "GER_out" else "SB_uturn" if te.startswith("NB") else "SB_thru"
        else:
            c = "GER_left" if te.startswith("NB") else "GER_right"
        cls[idx] = c
    return [cls[i] for i in range(len(cls))]


def tls_program(net, p=None):
    """APILL 2 fase adaptif (actuated): fase belok kanan diperpanjang selama ada antrean, maks g2max."""
    p = dict(TLS_DEFAULT, **(p or {}))
    cls = tls_classes(net)

    def st(green, minor=(), yellow=()):
        return "".join("G" if c in green else "g" if c in minor else "y" if c in yellow else "r" for c in cls)

    phases = [
        (p["g1min"], p["g1max"], st({"NB_thru", "NB_left", "SB_thru"}, {"GER_left"}), "Fase 1: Setiabudi lurus + kiri ke/dari Gerlong"),
        (p["y"], p["y"], st({"SB_thru"}, {"GER_left"}, {"NB_thru", "NB_left"}), "kuning arah naik"),
        (p["ar"], p["ar"], st({"SB_thru"}, {"GER_left"}), "merah semua arah naik"),
        (p["g2min"], p["g2max"], st({"SB_thru", "SB_right", "SB_uturn"}, {"GER_left"}), "Fase 2: dari atas belok kanan ke Gerlong / putar balik"),
        (p["y"], p["y"], st({"SB_thru"}, {"GER_left"}, {"SB_right", "SB_uturn"}), "kuning belok kanan"),
        (p["ar"], p["ar"], st({"SB_thru"}, {"GER_left"}), "pengosongan"),
    ]
    xml = ['  <tlLogic id="G" type="actuated" programID="lkm" offset="0">',
           '    <param key="max-gap" value="3.0"/>', '    <param key="detector-gap" value="2.0"/>',
           '    <param key="passing-time" value="1.9"/>']
    for mn, mx, state, name in phases:
        dur = mn if mn == mx else round((mn + mx) / 2)
        xml.append(f'    <phase duration="{dur}" minDur="{mn}" maxDur="{mx}" state="{state}" name="{name}"/>')
    xml.append("  </tlLogic>")
    return "\n".join(xml)


def write_config(sc, step=0.5, end=4200, folder=None):
    d = os.path.join(SCEN_DIR, folder or sc)
    cfg = f"""<configuration>
  <input>
    <net-file value="../../net/{sc}/net.net.xml"/>
    <route-files value="routes.rou.xml"/>
    <additional-files value="stops.add.xml"/>
  </input>
  <time><begin value="0"/><end value="{end}"/><step-length value="{step}"/></time>
  <processing>
    <lateral-resolution value="0.8"/>
    <time-to-teleport value="240"/>
    <time-to-impatience value="45"/>
    <collision.action value="warn"/>
    <collision.check-junctions value="false"/>
    <ignore-route-errors value="true"/>
    <default.speeddev value="0.1"/>
  </processing>
  <report><no-step-log value="true"/><verbose value="false"/></report>
</configuration>
"""
    open(os.path.join(d, "sim.sumocfg"), "w", encoding="utf-8").write(cfg)


def make(sc, scale=1.0, variant=None, folder=None, step=0.5):
    folder = folder or sc + ("_" + variant if variant else "")
    os.makedirs(os.path.join(SCEN_DIR, folder), exist_ok=True)
    net = sumolib.net.readNet(os.path.join(geo.ROOT, "net", sc, "net.net.xml"), withPrograms=True)
    flows = write_routes(sc, scale, variant=variant, folder=folder)
    stops = write_additional(sc, net, folder=folder)
    write_config(sc, folder=folder, step=step)
    meta = {"scenario": sc, "scale": scale, "kalibrasi": KALIBRASI, "volumes": VOLUMES, "mix": MIX, "stops": stops,
            "flows": [[r, vt, round(v, 1)] for r, vt, v in flows]}
    json.dump(meta, open(os.path.join(SCEN_DIR, folder, "meta.json"), "w", encoding="utf-8"), indent=1)
    tot = sum(f[2] for f in flows)
    print(f"[{folder}] {len(flows)} arus, total {tot:.0f} kend/jam, halte={list(stops)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scenarios", nargs="*", default=["S0", "S1", "S2"])
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--variant")
    a = ap.parse_args()
    for s in a.scenarios:
        make(s, a.scale, a.variant)
