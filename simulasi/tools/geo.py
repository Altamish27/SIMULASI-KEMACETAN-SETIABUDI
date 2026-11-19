"""Geometri lokasi: proyeksi lokal, ekstraksi garis jalan dari OSM, utilitas polyline.

Sistem koordinat lokal (meter): (0,0) = lat -6.8645, lon 107.5942; x = timur, y = utara.
Semua skrip (SUMO, 3D) memakai sistem koordinat yang sama.
"""
import json
import math
import os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
LAT0, LON0 = -6.8645, 107.5942
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110574.0


def to_xy(lat, lon):
    return ((lon - LON0) * KX, (lat - LAT0) * KY)


def to_ll(x, y):
    return (LAT0 + y / KY, LON0 + x / KX)


_OSM = None


def osm():
    """Muat area.osm sekali; kembalikan (nodes{id:(x,y)}, ways{id:{'nd':[...], 'tags':{}}})."""
    global _OSM
    if _OSM is None:
        r = ET.parse(os.path.join(DATA, "area.osm")).getroot()
        nodes = {n.get("id"): to_xy(float(n.get("lat")), float(n.get("lon"))) for n in r.iter("node")}
        ways = {}
        for w in r.iter("way"):
            ways[w.get("id")] = {
                "nd": [x.get("ref") for x in w.iter("nd")],
                "tags": {t.get("k"): t.get("v") for t in w.iter("tag")},
            }
        _OSM = (nodes, ways)
    return _OSM


def way_xy(wid, reverse=False):
    nodes, ways = osm()
    pts = [nodes[i] for i in ways[str(wid)]["nd"] if i in nodes]
    return pts[::-1] if reverse else pts


# ---------------------------------------------------------------- polyline utils
def length(pl):
    return sum(math.dist(pl[i], pl[i + 1]) for i in range(len(pl) - 1))


def dedup(pl, tol=0.3):
    out = [pl[0]]
    for p in pl[1:]:
        if math.dist(p, out[-1]) > tol:
            out.append(p)
    return out


def concat(*pls):
    out = []
    for pl in pls:
        out.extend(pl if not out else pl[1:] if math.dist(pl[0], out[-1]) < 1.0 else pl)
    return dedup(out)


def point_at(pl, s):
    """Titik pada jarak s sepanjang polyline."""
    if s <= 0:
        return pl[0]
    acc = 0.0
    for i in range(len(pl) - 1):
        d = math.dist(pl[i], pl[i + 1])
        if acc + d >= s:
            t = (s - acc) / d if d else 0
            return (pl[i][0] + t * (pl[i + 1][0] - pl[i][0]), pl[i][1] + t * (pl[i + 1][1] - pl[i][1]))
        acc += d
    return pl[-1]


def project(pl, p):
    """Jarak sepanjang polyline dari titik terdekat ke p."""
    best, bs, acc = 1e18, 0.0, 0.0
    for i in range(len(pl) - 1):
        a, b = pl[i], pl[i + 1]
        d = math.dist(a, b)
        if d == 0:
            continue
        t = max(0, min(1, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / d / d))
        q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        dd = math.dist(q, p)
        if dd < best:
            best, bs = dd, acc + t * d
        acc += d
    return bs


def s_at_y(pl, y):
    """Jarak sepanjang polyline saat pertama kali melintasi koordinat y (polyline monoton-y)."""
    acc = 0.0
    for i in range(len(pl) - 1):
        a, b = pl[i], pl[i + 1]
        d = math.dist(a, b)
        if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
            return acc + d * (y - a[1]) / (b[1] - a[1])
        acc += d
    raise ValueError(f"y={y} di luar polyline")


def sub(pl, s0, s1, step=None):
    """Potongan polyline dari s0 ke s1 (s0<s1). Simpul asli dipertahankan."""
    out = [point_at(pl, s0)]
    acc = 0.0
    for i in range(len(pl) - 1):
        acc += math.dist(pl[i], pl[i + 1])
        if s0 < acc < s1:
            out.append(pl[i + 1])
    out.append(point_at(pl, s1))
    return dedup(out, 0.2)


def resample(pl, step=5.0):
    L = length(pl)
    n = max(1, int(round(L / step)))
    return [point_at(pl, L * i / n) for i in range(n + 1)]


def offset(pl, d):
    """Geser polyline sejauh d ke KIRI arah gerak (d<0 = kanan)."""
    out = []
    n = len(pl)
    for i in range(n):
        if i == 0:
            dx, dy = pl[1][0] - pl[0][0], pl[1][1] - pl[0][1]
        elif i == n - 1:
            dx, dy = pl[-1][0] - pl[-2][0], pl[-1][1] - pl[-2][1]
        else:
            dx, dy = pl[i + 1][0] - pl[i - 1][0], pl[i + 1][1] - pl[i - 1][1]
        L = math.hypot(dx, dy) or 1
        out.append((pl[i][0] - dy / L * d, pl[i][1] + dx / L * d))
    return out


def midline(pl_a, pl_b, step=4.0):
    """Garis tengah antara dua polyline searah (contoh: dua jalur terpisah median)."""
    A = resample(pl_a, step)
    out = []
    for p in A:
        q = point_at(pl_b, project(pl_b, p))
        out.append(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2))
    return dedup(out)


# ---------------------------------------------------------------- elevasi
_ELEV = None


def elevation(x, y):
    """Elevasi relatif (m) terhadap mulut Gerlong, interpolasi IDW dari titik SRTM."""
    global _ELEV
    if _ELEV is None:
        _ELEV = json.load(open(os.path.join(DATA, "elevation.json")))
    num = den = 0.0
    for e in _ELEV:
        d = math.hypot(e["x"] - x, e["y"] - y)
        if d < 1:
            return e["z"] - ELEV_REF
        w = 1 / d ** 2
        num += w * e["z"]
        den += w
    return num / den - ELEV_REF


ELEV_REF = 894.0  # ≈ elevasi mulut Gerlong (m dpl); z lokal = elevasi - ELEV_REF


_FIT = None


def _axis_fit():
    """Regresi linear elevasi SRTM terhadap jarak sepanjang sumbu Setiabudi (meredam derau SRTM)."""
    global _FIT, _ELEV
    if _FIT is None:
        if _ELEV is None:
            _ELEV = json.load(open(os.path.join(DATA, "elevation.json")))
        ax = setiabudi_axis()
        pts = []
        for e in _ELEV:
            s = project(ax, (e["x"], e["y"]))
            q = point_at(ax, s)
            if math.dist(q, (e["x"], e["y"])) < 40:
                pts.append((s, e["z"]))
        n = len(pts)
        ms = sum(p[0] for p in pts) / n
        mz = sum(p[1] for p in pts) / n
        b = sum((p[0] - ms) * (p[1] - mz) for p in pts) / sum((p[0] - ms) ** 2 for p in pts)
        a = mz - b * ms
        sG = project(ax, (-6, -34))
        _FIT = (ax, a, b, a + b * sG)
    return _FIT


def ground_z(x, y):
    """Elevasi lokal (m) permukaan Setiabudi di titik terdekat sumbu; 0 = mulut Gerlong."""
    ax, a, b, zG = _axis_fit()
    return a + b * project(ax, (x, y)) - zG


def axis_grade():
    return _axis_fit()[2]


def axis_elevation(y):
    """Kompatibilitas: elevasi di sumbu pada ordinat y."""
    ax = _axis_fit()[0]
    p = point_at(ax, s_at_y(ax, y))
    return ground_z(*p)


def side_z(p, mouth, kind):
    """Elevasi jalan samping: Gerlong naik ±2% ke barat (SRTM), Kapten Abdul Hamid datar."""
    z0 = ground_z(*mouth)
    if kind == "GER":
        return z0 + min(math.dist(p, mouth), 150) * 0.02
    return z0


# ---------------------------------------------------------------- sumbu jalan
def setiabudi_axis():
    """Garis tengah Setiabudi (garis median) dari selatan ke utara."""
    south = way_xy(708711416, reverse=True)  # (-75,-655) -> (-11,-67)
    nb = concat(way_xy(1429001951), way_xy(1030698160))  # jalur naik (barat), selatan->utara
    sb = way_xy(1429001952, reverse=True)  # jalur turun (timur) dibalik: selatan->utara
    mid = midline(nb, sb)
    north = concat(way_xy(1429001950, reverse=True), way_xy(1030698156, reverse=True), way_xy(318054785, reverse=True))
    return concat(south, mid, north)


def gerlong_line():
    """Jl. Gegerkalong Girang dari barat ke mulut simpang."""
    return concat(way_xy(331191951), way_xy(860967810))


def kah_line():
    """Jl. Kapten Abdul Hamid dari timur ke bukaan A."""
    return way_xy(222611443, reverse=True)


def terrain_z(x, y):
    """Permukaan tanah 3D & jalan samping: profil Setiabudi (4,86%) + sisi barat naik ±2% (SRTM: Gerlong 900 vs 897)."""
    ax = _axis_fit()[0]
    s = project(ax, (x, y))
    q = point_at(ax, s)
    q2 = point_at(ax, s + 1.0)
    dx, dy = q2[0] - q[0], q2[1] - q[1]
    side = dx * (y - q[1]) - dy * (x - q[0])  # >0 = kiri arah utara = barat
    d = math.dist(q, (x, y))
    bonus = 0.02 * min(max(d - 8.0, 0.0), 150.0) if side > 0 else 0.0
    return ground_z(x, y) + bonus
