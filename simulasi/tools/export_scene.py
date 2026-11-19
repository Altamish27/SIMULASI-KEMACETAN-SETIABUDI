"""Ekspor geometri adegan 3D (JSON) untuk tampilan Three.js.

web/data/common.json   : tanah (heightmap), gedung, pohon, area hijau, jalan konteks, landmark
web/data/scene_S0.json : lajur & simpang dari jaringan SUMO + median pagar + rambu + (APILL/flyover)

Koordinat = koordinat lokal SUMO (x timur, y utara, z naik). Three.js: (x, z, -y).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import geo  # noqa: E402
import sumolib  # noqa: E402

OUT = os.path.join(geo.ROOT, "web", "data")
BX = (-420, 420)
BY = (-520, 470)
R2 = lambda v: round(v, 2)  # noqa: E731


def inside(p, pad=0):
    return BX[0] - pad <= p[0] <= BX[1] + pad and BY[0] - pad <= p[1] <= BY[1] + pad


def poly_area(pts):
    a = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def point_in_poly(p, poly):
    x, y = p
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            c = not c
        j = i
    return c


# ------------------------------------------------------------------ adegan bersama
def export_common():
    nodes, ways = geo.osm()
    import random
    rng = random.Random(7)
    # tanah
    step = 10
    xs = list(range(BX[0], BX[1] + 1, step))
    ys = list(range(BY[0], BY[1] + 1, step))
    heights = [[R2(geo.terrain_z(x, y) - 0.25) for x in xs] for y in ys]
    terrain = {"x0": BX[0], "y0": BY[0], "step": step, "nx": len(xs), "ny": len(ys), "z": heights}

    buildings, greens, trees, ctx_roads = [], [], [], []
    sim_names = ("Jalan Dr. Setiabudi",)
    sim_ways = {"860967810", "331191951", "222611443"}
    road_w = {"trunk": 9, "trunk_link": 5, "primary": 8, "primary_link": 5, "secondary": 7, "tertiary": 6,
              "unclassified": 5, "residential": 4.5, "living_street": 3.5, "service": 3.2, "pedestrian": 3,
              "footway": 1.6, "steps": 1.6, "path": 1.4}
    palette = ["#e9e4d8", "#f1ede4", "#d9d2c3", "#cfc6b4", "#e6dccb", "#c9c3b8", "#ece7df", "#bfb7a8", "#d7cbb5"]
    roofs = ["#9b4a33", "#8a3f2c", "#7c7a76", "#6d6a66", "#a85a3c", "#5f6b73"]
    for wid, w in ways.items():
        t = w["tags"]
        pts = [nodes[i] for i in w["nd"] if i in nodes]
        if len(pts) < 2:
            continue
        if "building" in t and len(pts) >= 4 and pts[0] == pts[-1]:
            ring = pts[:-1]
            c = centroid(ring)
            if not inside(c):
                continue
            area = abs(poly_area(ring))
            if area < 8:
                continue
            if "height" in t:
                try:
                    h = float(t["height"].split()[0])
                except ValueError:
                    h = 7
            elif "building:levels" in t:
                try:
                    h = float(t["building:levels"]) * 3.3 + 0.8
                except ValueError:
                    h = 7
            else:
                big = t.get("building") in ("university", "school", "commercial", "retail", "office", "hotel")
                h = (rng.choice([7.5, 10.5, 13.5]) if big or area > 600 else rng.choice([3.6, 4.2, 6.8, 7.4]))
            if poly_area(ring) < 0:
                ring = ring[::-1]
            z = min(geo.terrain_z(*p) for p in ring) - 0.3
            buildings.append({"p": [[R2(p[0]), R2(p[1])] for p in ring], "z": R2(z), "h": R2(h),
                              "c": rng.choice(palette), "r": rng.choice(roofs) if h < 8 else "#8e8c88",
                              "n": t.get("name", "")})
        elif (t.get("landuse") in ("grass", "forest") or t.get("natural") in ("wood", "scrub")
              or t.get("leisure") in ("park", "garden")) and pts[0] == pts[-1]:
            ring = pts[:-1]
            if not inside(centroid(ring), 100):
                continue
            kind = "wood" if t.get("natural") == "wood" or t.get("landuse") == "forest" else "grass"
            greens.append({"p": [[R2(p[0]), R2(p[1]), R2(geo.terrain_z(*p) - 0.15)] for p in ring], "k": kind})
            # isi pohon
            xs_ = [p[0] for p in ring]
            ys_ = [p[1] for p in ring]
            area = abs(poly_area(ring))
            dens = 1 / 90 if kind == "wood" else 1 / 450
            for _ in range(min(400, int(area * dens))):
                q = (rng.uniform(min(xs_), max(xs_)), rng.uniform(min(ys_), max(ys_)))
                if point_in_poly(q, ring) and inside(q):
                    trees.append([R2(q[0]), R2(q[1]), R2(geo.terrain_z(*q)), R2(rng.uniform(0.7, 1.4))])
        elif "highway" in t and t["highway"] in road_w and wid not in sim_ways and t.get("name") not in sim_names:
            if not any(inside(p) for p in pts):
                continue
            ctx_roads.append({"p": [[R2(p[0]), R2(p[1]), R2(geo.terrain_z(*p) - 0.12)] for p in pts],
                              "w": road_w[t["highway"]], "k": t["highway"]})
    for nid, p in nodes.items():
        pass
    # pohon OSM (natural=tree)
    import xml.etree.ElementTree as ET
    r = ET.parse(os.path.join(geo.DATA, "area.osm")).getroot()
    for n in r.iter("node"):
        tg = {x.get("k"): x.get("v") for x in n.iter("tag")}
        if tg.get("natural") == "tree":
            q = geo.to_xy(float(n.get("lat")), float(n.get("lon")))
            if inside(q):
                trees.append([R2(q[0]), R2(q[1]), R2(geo.terrain_z(*q)), 1.6])
    # pohon peneduh besar di sisi UPI sepanjang Setiabudi (terlihat di video: pohon besar & pinus)
    ax = geo.setiabudi_axis()
    for y in range(-60, 330, 14):
        try:
            s = geo.s_at_y(ax, y)
        except ValueError:
            continue
        p = geo.point_at(ax, s)
        q = geo.point_at(ax, s + 1)
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        w = (p[0] - dy / L * 13.5, p[1] + dx / L * 13.5)  # 13,5 m ke barat (trotoar UPI)
        if -40 < y < -25:
            continue  # mulut Gerlong
        trees.append([R2(w[0]), R2(w[1]), R2(geo.terrain_z(*w)), R2(rng.uniform(1.6, 2.2))])

    landmarks = [
        {"type": "billboard", "x": -21, "y": -6, "h": 11, "w": 5, "hh": 9, "text": "", "color": "#d9d9d9", "rot": 70},
        {"type": "sign_green", "x": -15.5, "y": -24, "h": 5.5, "text": "KORAMIL 1807\nBIRO REKLAME RAJAWALI NEON", "rot": 75},
        {"type": "billboard", "x": -27, "y": -14, "h": 13, "w": 4, "hh": 6, "text": "JAZY\nMAX FILTER", "color": "#1f2733", "rot": 80},
        {"type": "billboard", "x": -30, "y": -80, "h": 10, "w": 9, "hh": 4, "text": "Tiramisusu", "color": "#1f6b4a", "rot": 80},
        {"type": "round_sign", "x": -21, "y": -70, "h": 5, "text": "Vitasari", "color": "#7a1f2b"},
        {"type": "booth", "x": -24, "y": -20, "text": "POS GATUR LANTAS\nPANORAMA GERLONG", "rot": 80},
        {"type": "shop_sign", "x": -21, "y": -42, "text": "J&T EXPRESS", "color": "#d6262b", "rot": 80},
        {"type": "halte", "x": -24, "y": -89, "text": "Gegerkalong Girang", "rot": 80},
        {"type": "gate", "x": 40, "y": 128, "text": "UPI", "rot": -60},
        {"type": "label", "x": -170, "y": 8, "text": "Jl. Gegerkalong Girang (Gerlong)"},
        {"type": "label", "x": 30, "y": -200, "text": "↓ arah kota"},
        {"type": "label", "x": 80, "y": 330, "text": "↑ arah UPI / Lembang"},
    ]
    for lm in landmarks:
        lm["z"] = R2(geo.terrain_z(lm["x"], lm["y"]))
    cams = {
        "Ikhtisar": {"pos": [180, 160, -40], "target": [-5, 0, -20]},
        "Bukaan A": {"pos": [35, 22, -95], "target": [-6, -1.5, -67]},
        "Mulut Gerlong": {"pos": [40, 20, 0], "target": [-8, 0, -33]},
        "Bukaan B": {"pos": [55, 25, 40], "target": [20, 5, 72]},
        "Flyover": {"pos": [90, 45, -270], "target": [-20, 0, -150]},
        "Pejalan kaki": {"pos": [-17, 1.7, -28], "target": [10, 1, -50]},
    }
    common = {"terrain": terrain, "buildings": buildings, "greens": greens, "trees": trees,
              "roads": ctx_roads, "landmarks": landmarks, "cameras": cams,
              "grade_pct": round(geo.axis_grade() * 100, 2)}
    os.makedirs(OUT, exist_ok=True)
    json.dump(common, open(os.path.join(OUT, "common.json"), "w", encoding="utf-8"), separators=(",", ":"))
    print(f"common: {len(buildings)} gedung, {len(trees)} pohon, {len(greens)} area hijau, {len(ctx_roads)} jalan konteks")


# ------------------------------------------------------------------ per skenario
MEDIAN = {
    # rentang y pagar median (sumbu), tiap segmen (y_selatan, y_utara)
    "S0": [(-60.0, 66.0)],
    "S1": [(-150.0, -42.0), (-25.0, 66.0)],
    "S2": [(-245.0, 143.0)],
}
SIGNS = {
    "S0": [("uturn", -58, 0.0, 1), ("uturn", 64, 0.0, -1), ("nouturn", -33, 0.0, 1)],
    "S1": [("uturn", 64, 0.0, -1), ("keep", -50, 0.0, 1)],
    "S2": [("uturn", 142, 0.0, -1), ("flyover", 115, 6.0, 1)],
}


def lane_json(ln):
    sh = ln.getShape3D() if hasattr(ln, "getShape3D") else [(x, y, 0) for x, y in ln.getShape()]
    e = ln.getEdge()
    return {"id": ln.getID(), "e": e.getID(), "i": ln.getIndex(), "n": len(e.getLanes()), "w": R2(ln.getWidth()),
            "s": [[R2(p[0]), R2(p[1]), R2(p[2])] for p in sh]}


def export_scenario(sc):
    net = sumolib.net.readNet(os.path.join(geo.ROOT, "net", sc, "net.net.xml"), withInternal=True, withPrograms=True)
    lanes, internal, juncs = [], [], []
    for e in net.getEdges(withInternal=True):
        for ln in e.getLanes():
            (internal if e.getID().startswith(":") else lanes).append(lane_json(ln))
    for j in net.getNodes():
        sh = j.getShape3D() if hasattr(j, "getShape3D") else [(x, y, 0) for x, y in j.getShape()]
        if len(sh) >= 3:
            juncs.append({"id": j.getID(), "s": [[R2(p[0]), R2(p[1]), R2(p[2])] for p in sh]})
    ax = geo.setiabudi_axis()
    medians = []
    for y0, y1 in MEDIAN[sc]:
        s0, s1 = geo.s_at_y(ax, y0), geo.s_at_y(ax, y1)
        pl = geo.resample(geo.sub(ax, s0, s1), 2.5)
        medians.append([[R2(p[0]), R2(p[1]), R2(geo.ground_z(*p))] for p in pl])
    signs = []
    for kind, y, lat, facing in SIGNS[sc]:
        s = geo.s_at_y(ax, y)
        p = geo.point_at(ax, s)
        q = geo.point_at(ax, s + 1)
        ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        signs.append({"k": kind, "x": R2(p[0]), "y": R2(p[1]), "z": R2(geo.ground_z(*p)), "a": R2(ang), "f": facing})
    scene = {"scenario": sc, "lanes": lanes, "internal": internal, "junctions": juncs, "median": medians, "signs": signs}
    if sc == "S1":
        tl = net.getTLS("G")
        links = []
        for (inl, outl, idx) in tl.getConnections():
            sh = inl.getShape()
            p = sh[-1]
            links.append({"i": idx, "x": R2(p[0]), "y": R2(p[1]), "from": inl.getID(), "to": outl.getID()})
        scene["tls"] = {"id": "G", "links": links}
        # panah marka lajur khusus belok kanan
        scene["arrows"] = []
        e = net.getEdge("SB_Gq_G")
        ln = e.getLanes()[1]
        sh = ln.getShape()
        for frac in (0.25, 0.6, 0.9):
            L = geo.length(sh)
            p = geo.point_at(sh, L * frac)
            q = geo.point_at(sh, L * frac + 1)
            scene["arrows"].append({"x": R2(p[0]), "y": R2(p[1]), "z": R2(geo.ground_z(*p) + 0.03),
                                    "a": R2(math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))), "k": "right_uturn"})
    if sc == "S2":
        fo = net.getEdge("FO").getLanes()[0]
        sh = fo.getShape3D()
        scene["flyover"] = {"s": [[R2(p[0]), R2(p[1]), R2(p[2])] for p in sh], "w": R2(fo.getWidth())}
        # pilar tiap ±22 m di bagian yang tinggi (> 4,5 m di atas tanah)
        piers, acc, last = [], 0.0, -99
        for a, b in zip(sh, sh[1:]):
            d = math.dist(a[:2], b[:2])
            acc += d
            if acc - last >= 22:
                g = geo.terrain_z(b[0], b[1])
                if b[2] - g > 4.5:
                    piers.append([R2(b[0]), R2(b[1]), R2(g), R2(b[2])])
                    last = acc
        scene["flyover"]["piers"] = piers
    json.dump(scene, open(os.path.join(OUT, f"scene_{sc}.json"), "w", encoding="utf-8"), separators=(",", ":"))
    print(f"{sc}: {len(lanes)} lajur, {len(internal)} lajur internal, {len(juncs)} simpang")


if __name__ == "__main__":
    args = sys.argv[1:] or ["common", "S0", "S1", "S2"]
    for a in args:
        export_common() if a == "common" else export_scenario(a)
