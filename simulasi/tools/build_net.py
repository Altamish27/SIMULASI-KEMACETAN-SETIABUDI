"""Bangun jaringan SUMO untuk skenario S0 / S1 / S2 dari geometri OSM nyata.

S0  Eksisting   : median pagar baru; bukaan A (y≈-67) untuk putar balik dari atas → Gerlong;
                  bukaan B (y≈+72) untuk putar balik dari bawah; median di depan Gerlong tertutup.
S1  APILL       : median dibuka di mulut Gerlong + lampu 2 fase adaptif (fase belok kanan sesuai antrean),
                  lajur kanan arah turun 60 m jadi lajur khusus belok kanan/putar balik; bukaan A ditutup,
                  bukaan B tetap (kendaraan kecil).
S2  U-turn layang: putar balik layang arah turun → naik (mendarat 67 m sebelum Gerlong),
                  pelebaran jalan di zona ramp, bukaan A ditutup, bukaan B dipindah ke y≈+150.

Pemakaian:  python tools/build_net.py            (semua skenario)
            python tools/build_net.py S1
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import geo  # noqa: E402

import sumo  # noqa: E402

SUMO_BIN = os.path.join(sumo.SUMO_HOME, "bin")
NETDIR = os.path.join(geo.ROOT, "net")

LANE_W = 3.1          # lebar lajur Setiabudi (m)
MEDIAN_HALF = 0.4     # setengah lebar median pagar (m)
V_MAIN = 11.11        # 40 km/jam
V_GER = 8.33          # 30 km/jam
V_KAH = 5.56          # 20 km/jam
V_UTURN = 3.0         # kecepatan di dalam gerakan putar balik (m/s)
FO_W = 4.0            # lebar lajur flyover (m)

Y = {"S": -450.0, "Fd": -100.0, "A": -67.2, "G": -33.5, "Gq": 28.0, "B": 72.1, "B2": 150.0, "Fu": 95.0, "N": 430.0}

AXIS = geo.setiabudi_axis()


def s_of(key):
    return geo.s_at_y(AXIS, Y[key])


def xyz(p, z=None):
    z = geo.ground_z(*p) if z is None else z
    return f"{p[0]:.2f},{p[1]:.2f},{z:.2f}"


def shape_str(pl, zs=None):
    if zs is None:
        return " ".join(xyz(p) for p in pl)
    return " ".join(xyz(p, z) for p, z in zip(pl, zs))


# ------------------------------------------------------------------ penyusun file plain-XML
class Net:
    def __init__(self, name):
        self.name = name
        self.nodes, self.edges, self.cons, self.extra_nod_attrs = [], [], [], {}

    def node(self, nid, p, z=None, ntype="priority", **kw):
        attrs = " ".join(f'{k}="{v}"' for k, v in kw.items())
        zz = geo.ground_z(*p) if z is None else z
        self.nodes.append(f'  <node id="{nid}" x="{p[0]:.2f}" y="{p[1]:.2f}" z="{zz:.2f}" type="{ntype}" {attrs}/>')

    def edge(self, eid, frm, to, shape, lanes, speed, prio, width, name, zs=None, **kw):
        attrs = " ".join(f'{k}="{v}"' for k, v in kw.items())
        self.edges.append(
            f'  <edge id="{eid}" from="{frm}" to="{to}" numLanes="{lanes}" speed="{speed}" priority="{prio}" '
            f'width="{width}" name="{name}" shape="{shape_str(shape, zs)}" {attrs}/>'
        )

    def con(self, frm, to, fl, tl, **kw):
        attrs = " ".join(f'{k}="{v}"' for k, v in kw.items())
        self.cons.append(f'  <connection from="{frm}" to="{to}" fromLane="{fl}" toLane="{tl}" {attrs}/>')

    def write_and_build(self):
        d = os.path.join(NETDIR, self.name)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "net.nod.xml"), "w", encoding="utf-8").write("<nodes>\n" + "\n".join(self.nodes) + "\n</nodes>\n")
        open(os.path.join(d, "net.edg.xml"), "w", encoding="utf-8").write("<edges>\n" + "\n".join(self.edges) + "\n</edges>\n")
        open(os.path.join(d, "net.con.xml"), "w", encoding="utf-8").write("<connections>\n" + "\n".join(self.cons) + "\n</connections>\n")
        out = os.path.join(d, "net.net.xml")
        cmd = [
            os.path.join(SUMO_BIN, "netconvert"),
            "-n", os.path.join(d, "net.nod.xml"),
            "-e", os.path.join(d, "net.edg.xml"),
            "-x", os.path.join(d, "net.con.xml"),
            "--lefthand", "true",
            "--offset.disable-normalization", "true",
            "--no-turnarounds", "true",
            "--junctions.corner-detail", "8",
            "--junctions.internal-link-detail", "8",
            "--rectangular-lane-cut", "false",
            "--tls.default-type", "static",
            "--output.original-names", "true",
            "-o", out,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[{self.name}] netconvert rc={r.returncode}")
        if r.stderr.strip():
            print("\n".join(l for l in r.stderr.splitlines() if "Warning" in l or "Error" in l)[:3000])
        return out


# ------------------------------------------------------------------ elemen bersama
def carriageway(net, a, b, lanes=2, prefix=None, off=MEDIAN_HALF):
    """Dua edge searah (NB: a->b ke utara, SB: b->a ke selatan) pada segmen sumbu a..b."""
    sa, sb_ = s_of(a), s_of(b)
    seg = geo.sub(AXIS, sa, sb_)
    nb = geo.offset(seg, off)
    sbw = geo.offset(seg[::-1], off)
    if prefix in (None, "NB"):
        net.edge(f"NB_{a}_{b}", a, b, nb, lanes, V_MAIN, 10, LANE_W, "Jl. Dr. Setiabudi (naik)")
    if prefix in (None, "SB"):
        net.edge(f"SB_{b}_{a}", b, a, sbw, lanes, V_MAIN, 10, LANE_W, "Jl. Dr. Setiabudi (turun)")


def axis_pt(key, lateral=0.0):
    """Titik pada sumbu (lateral>0 = timur/jalur turun)."""
    s = s_of(key)
    p = geo.point_at(AXIS, s)
    q = geo.point_at(AXIS, s + 1)
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    # normal kanan arah utara = timur
    return (p[0] + dy / L * lateral, p[1] - dx / L * lateral)


def side_roads(net):
    G = axis_pt("G")
    ger = geo.gerlong_line()
    s_end = geo.project(ger, (-430, 70))
    s_mouth = geo.project(ger, (-10, -33))
    gl = geo.sub(ger, s_end, s_mouth)
    gl[-1] = (G[0] - (LANE_W * 2 + MEDIAN_HALF) + 0.5, G[1] + 1.0)  # ujung di tepi jalur naik
    gz = [geo.terrain_z(*p) for p in gl]
    net.node("GW", gl[0], z=gz[0], ntype="dead_end")
    net.edge("GER_in", "GW", "G", gl, 1, V_GER, 5, 3.0, "Jl. Gegerkalong Girang", zs=gz)
    net.edge("GER_out", "G", "GW", gl[::-1], 1, V_GER, 5, 3.0, "Jl. Gegerkalong Girang", zs=gz[::-1])

    A = axis_pt("A")
    kah = geo.kah_line()
    s_end = geo.project(kah, (160, -88))
    kl = geo.sub(kah, s_end, geo.length(kah))
    kl[-1] = (A[0] + LANE_W * 2 + MEDIAN_HALF - 0.5, A[1] - 1.0)
    kz = [geo.terrain_z(*p) for p in kl]
    net.node("KE", kl[0], z=kz[0], ntype="dead_end")
    small = "motorcycle passenger taxi"
    net.edge("KAH_in", "KE", "A", kl, 1, V_KAH, 2, 2.6, "Jl. Kapten Abdul Hamid", zs=kz, allow=small)
    net.edge("KAH_out", "A", "KE", kl[::-1], 1, V_KAH, 2, 2.6, "Jl. Kapten Abdul Hamid", zs=kz[::-1], allow=small)


def uturn(net, frm, to, fl=1, tl=0):
    net.con(frm, to, fl, tl, speed=V_UTURN)


# ------------------------------------------------------------------ S0 eksisting
def build_s0():
    net = Net("S0")
    for k in ("S", "A", "G", "B", "N"):
        net.node(k, axis_pt(k), ntype="dead_end" if k in ("S", "N") else "priority")
    for a, b in (("S", "A"), ("A", "G"), ("G", "B"), ("B", "N")):
        carriageway(net, a, b)
    side_roads(net)
    # Bukaan A: putar balik dari atas (lajur kanan/median) + akses Kapten Abdul Hamid
    net.con("SB_G_A", "SB_A_S", 0, 0); net.con("SB_G_A", "SB_A_S", 1, 1)
    uturn(net, "SB_G_A", "NB_A_G", 1, 0)
    net.con("SB_G_A", "KAH_out", 0, 0)
    net.con("NB_S_A", "NB_A_G", 0, 0); net.con("NB_S_A", "NB_A_G", 1, 1)
    net.con("NB_S_A", "KAH_out", 1, 0)
    net.con("KAH_in", "SB_A_S", 0, 0); net.con("KAH_in", "NB_A_G", 0, 1)
    # Mulut Gerlong: median tertutup
    net.con("NB_A_G", "NB_G_B", 0, 0); net.con("NB_A_G", "NB_G_B", 1, 1)
    net.con("NB_A_G", "GER_out", 0, 0)
    net.con("SB_B_G", "SB_G_A", 0, 0); net.con("SB_B_G", "SB_G_A", 1, 1)
    net.con("GER_in", "NB_G_B", 0, 0)
    # Bukaan B: putar balik dari bawah
    net.con("NB_G_B", "NB_B_N", 0, 0); net.con("NB_G_B", "NB_B_N", 1, 1)
    uturn(net, "NB_G_B", "SB_B_G", 1, 0)
    net.con("SB_N_B", "SB_B_G", 0, 0); net.con("SB_N_B", "SB_B_G", 1, 1)
    return net.write_and_build()


# ------------------------------------------------------------------ S1 APILL
def build_s1():
    net = Net("S1")
    for k in ("S", "A", "G", "Gq", "B", "N"):
        t = {"S": "dead_end", "N": "dead_end", "G": "traffic_light"}.get(k, "priority")
        net.node(k, axis_pt(k), ntype=t)
    for a, b in (("S", "A"), ("A", "G"), ("G", "Gq"), ("Gq", "B"), ("B", "N")):
        carriageway(net, a, b)
    side_roads(net)
    # A ditutup (hanya kiri-masuk / kiri-keluar Kapten Abdul Hamid)
    net.con("SB_G_A", "SB_A_S", 0, 0); net.con("SB_G_A", "SB_A_S", 1, 1)
    net.con("SB_G_A", "KAH_out", 0, 0)
    net.con("NB_S_A", "NB_A_G", 0, 0); net.con("NB_S_A", "NB_A_G", 1, 1)
    net.con("KAH_in", "SB_A_S", 0, 0)
    # G bersinyal
    net.con("NB_A_G", "NB_G_Gq", 0, 0); net.con("NB_A_G", "NB_G_Gq", 1, 1)
    net.con("NB_A_G", "GER_out", 0, 0)
    net.con("SB_Gq_G", "SB_G_A", 0, 0); net.con("SB_Gq_G", "SB_G_A", 0, 1)
    net.con("SB_Gq_G", "GER_out", 1, 0, speed=5.0)
    uturn(net, "SB_Gq_G", "NB_G_Gq", 1, 1)
    net.con("GER_in", "NB_G_Gq", 0, 0)
    # Gq: awal lajur khusus belok kanan (lajur 1 = sisi median)
    net.con("SB_B_Gq", "SB_Gq_G", 0, 0); net.con("SB_B_Gq", "SB_Gq_G", 1, 1)
    net.con("NB_G_Gq", "NB_Gq_B", 0, 0); net.con("NB_G_Gq", "NB_Gq_B", 1, 1)
    # B tetap untuk putar balik dari bawah (kendaraan kecil; larangan truk/bus lewat demand)
    net.con("NB_Gq_B", "NB_B_N", 0, 0); net.con("NB_Gq_B", "NB_B_N", 1, 1)
    uturn(net, "NB_Gq_B", "SB_B_Gq", 1, 0)
    net.con("SB_N_B", "SB_B_Gq", 0, 0); net.con("SB_N_B", "SB_B_Gq", 1, 1)
    return net.write_and_build()


# ------------------------------------------------------------------ S2 U-turn layang
def flyover_geometry():
    """Garis tengah dek flyover + elevasi (absolut lokal).

    Naik dari lajur median arah turun di y=+95, melayang ke selatan, loop R=13 m di y≈-220,
    kembali ke utara di atas lajur median arah naik, mendarat di y=-100.
    """
    R = 13.0
    lat_up, lat_dn = MEDIAN_HALF + LANE_W * 1.5, -(MEDIAN_HALF + LANE_W * 1.5)  # pusat lajur median
    y_up0, y_loop, y_dn = Y["Fu"], -205.0, Y["Fd"]

    def axis_y(y, lat):
        return axis_pt_y(y, lat)

    pts, zs = [], []
    # ramp naik + dek ke selatan
    for y in frange(y_up0, y_loop, -4.0):
        p = axis_y(y, lat_up)
        g = geo.ground_z(*p)
        deck = min(geo.ground_z(*axis_y(y_up0, lat_up)), g + 7.5)
        pts.append(p); zs.append(deck)
    # loop (bola lampu): melebar ke timur, memutar searah jarum jam ke barat
    c = axis_y(y_loop - R, 0.0)
    zl = geo.ground_z(*c) + 7.5
    p0 = pts[-1]
    # transisi ke titik timur lingkaran
    east = (c[0] + R, c[1])
    for t in (0.33, 0.66):
        pts.append((p0[0] + (east[0] - p0[0]) * t, p0[1] + (east[1] - p0[1]) * t)); zs.append(zl)
    for k in range(0, 19):
        a = -math.pi * k / 18  # 0 → -180° (timur → selatan → barat)
        pts.append((c[0] + R * math.cos(a), c[1] + R * math.sin(a))); zs.append(zl)
    west_end = pts[-1]
    first_dn = axis_y(y_loop, lat_dn)
    for t in (0.33, 0.66):
        pts.append((west_end[0] + (first_dn[0] - west_end[0]) * t, west_end[1] + (first_dn[1] - west_end[1]) * t)); zs.append(zl)
    # ramp turun ke utara, mendarat di y_dn
    n = int((y_dn - y_loop) / 4.0)
    for i in range(n + 1):
        y = y_loop + (y_dn - y_loop) * i / n
        t = i / n
        g = geo.ground_z(*axis_y(y, lat_dn))
        deck = zl + (g - zl) * (t ** 1.15)
        pts.append(axis_y(y, lat_dn)); zs.append(deck)
    return pts, zs


def frange(a, b, step):
    out, v = [], a
    while (step < 0 and v > b) or (step > 0 and v < b):
        out.append(v); v += step
    out.append(b)
    return out


def axis_pt_y(y, lateral):
    s = geo.s_at_y(AXIS, y)
    p = geo.point_at(AXIS, s)
    q = geo.point_at(AXIS, s + 1)
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    return (p[0] + dy / L * lateral, p[1] - dx / L * lateral)


def build_s2():
    net = Net("S2")
    lat_c = MEDIAN_HALF + LANE_W  # pusat jalur (2 lajur)
    for k in ("S", "A", "G", "N"):
        net.node(k, axis_pt(k), ntype="dead_end" if k in ("S", "N") else "priority")
    net.node("B", axis_pt_y(Y["B2"], 0.0))
    fo, fz = flyover_geometry()
    net.node("Fu", axis_pt_y(Y["Fu"], lat_c))
    net.node("Fd", axis_pt_y(Y["Fd"], -lat_c))

    def seg(y0, y1, lat_sign):
        s0, s1 = sorted((geo.s_at_y(AXIS, y0), geo.s_at_y(AXIS, y1)))
        pl = geo.sub(AXIS, s0, s1)
        return pl

    # Arah naik: S → Fd → A → G → B → N
    ys_nb = [("S", Y["S"]), ("Fd", Y["Fd"]), ("A", Y["A"]), ("G", Y["G"]), ("B", Y["B2"]), ("N", Y["N"])]
    for (a, ya), (b, yb) in zip(ys_nb, ys_nb[1:]):
        pl = geo.offset(seg(ya, yb, 1), MEDIAN_HALF)
        net.edge(f"NB_{a}_{b}", a, b, pl, 2, V_MAIN, 10, LANE_W, "Jl. Dr. Setiabudi (naik)")
    # Arah turun: N → B → Fu → G → A → S
    ys_sb = [("N", Y["N"]), ("B", Y["B2"]), ("Fu", Y["Fu"]), ("G", Y["G"]), ("A", Y["A"]), ("S", Y["S"])]
    for (a, ya), (b, yb) in zip(ys_sb, ys_sb[1:]):
        pl = geo.offset(seg(yb, ya, -1)[::-1], MEDIAN_HALF)
        net.edge(f"SB_{a}_{b}", a, b, pl, 2, V_MAIN, 10, LANE_W, "Jl. Dr. Setiabudi (turun)")
    net.edge("FO", "Fu", "Fd", fo, 1, V_GER, 6, FO_W, "Putaran Balik Layang", zs=fz,
             disallow="pedestrian bicycle")
    side_roads(net)
    # Fu: lajur median arah turun bercabang ke flyover
    net.con("SB_B_Fu", "SB_Fu_G", 0, 0); net.con("SB_B_Fu", "SB_Fu_G", 1, 1)
    net.con("SB_B_Fu", "FO", 1, 0)
    # Fd: flyover bergabung ke lajur median arah naik (mengalah)
    net.con("NB_S_Fd", "NB_Fd_A", 0, 0); net.con("NB_S_Fd", "NB_Fd_A", 1, 1)
    net.con("FO", "NB_Fd_A", 0, 1)
    # A ditutup
    net.con("SB_G_A", "SB_A_S", 0, 0); net.con("SB_G_A", "SB_A_S", 1, 1)
    net.con("SB_G_A", "KAH_out", 0, 0)
    net.con("NB_Fd_A", "NB_A_G", 0, 0); net.con("NB_Fd_A", "NB_A_G", 1, 1)
    net.con("KAH_in", "SB_A_S", 0, 0)
    # G (median tertutup)
    net.con("NB_A_G", "NB_G_B", 0, 0); net.con("NB_A_G", "NB_G_B", 1, 1)
    net.con("NB_A_G", "GER_out", 0, 0)
    net.con("SB_Fu_G", "SB_G_A", 0, 0); net.con("SB_Fu_G", "SB_G_A", 1, 1)
    net.con("GER_in", "NB_G_B", 0, 0)
    # B dipindah ke y=+150 (kendaraan kecil saja – larangan via demand)
    net.con("NB_G_B", "NB_B_N", 0, 0); net.con("NB_G_B", "NB_B_N", 1, 1)
    uturn(net, "NB_G_B", "SB_B_Fu", 1, 0)
    net.con("SB_N_B", "SB_B_Fu", 0, 0); net.con("SB_N_B", "SB_B_Fu", 1, 1)
    return net.write_and_build()


BUILDERS = {"S0": build_s0, "S1": build_s1, "S2": build_s2}

if __name__ == "__main__":
    which = sys.argv[1:] or list(BUILDERS)
    for w in which:
        BUILDERS[w]()
