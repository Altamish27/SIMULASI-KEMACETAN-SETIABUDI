"""Jalankan satu skenario (headless atau GUI) dan simpan metrik.

python tools/run.py S0 --seed 1            (headless)
python tools/run.py S1 --gui               (sumo-gui untuk melihat langsung)
python tools/run.py S1 --tls g1=45,g2=14,g3=12
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
import geo  # noqa: E402
import sumo  # noqa: E402
import sumolib  # noqa: E402

if "--gui" not in sys.argv:
    os.environ["SIM_LIBSUMO"] = "1"
    import libsumo as traci  # noqa: E402
else:
    import traci  # noqa: E402
from control import Controller  # noqa: E402

WARMUP, MEASURE = 600, 3600
OD_LABEL = {
    "SB_thru": "Dari atas → lurus ke bawah",
    "SB_ger": "Dari atas (Lembang) → Gerlong",
    "SB_uturn": "Dari atas → putar balik",
    "NB_thru": "Dari bawah → lurus ke atas",
    "NB_ger": "Dari bawah → Gerlong",
    "NB_uturn": "Dari bawah → putar balik",
    "GER_north": "Gerlong → atas",
    "GER_south": "Gerlong → bawah",
}


def run(sc, seed=1, gui=False, tls=None, tag=None, end=WARMUP + MEASURE, scale=None):
    base = sc.split("_")[0]
    sdir = os.path.join(geo.ROOT, "scenarios", sc)
    tag = tag or f"{sc}_seed{seed}"
    odir = os.path.join(geo.ROOT, "results", "runs", tag)
    os.makedirs(odir, exist_ok=True)
    if scale is not None or tls is not None:
        import make_scenario as ms
        if tls is not None:
            ms.TLS_DEFAULT.update(tls)
        ms.make(base, scale if scale is not None else 1.0, sc.split("_")[1] if "_" in sc else None)
    binname = "sumo-gui" if gui else "sumo"
    cmd = [os.path.join(sumo.SUMO_HOME, "bin", binname), "-c", os.path.join(sdir, "sim.sumocfg"),
           "--seed", str(seed), "--end", str(end),
           "--tripinfo-output", os.path.join(odir, "tripinfo.xml"),
           "--tripinfo-output.write-unfinished", "true",
           "--statistic-output", os.path.join(odir, "stats.xml"),
           "--duration-log.statistics", "true"]
    if gui:
        cmd += ["--start", "--delay", "40", "--gui-settings-file", os.path.join(geo.ROOT, "tools", "gui.xml")]
    net = sumolib.net.readNet(os.path.join(geo.ROOT, "net", base, "net.net.xml"), withInternal=True)
    traci.start(cmd)
    ctl = Controller(sc, net, seed=seed)
    t0 = time.time()
    step = traci.simulation.getDeltaT()
    t = 0.0
    while t < end:
        traci.simulationStep()
        t = traci.simulation.getTime()
        ctl.step(t)
        if abs(t % 5.0) < step / 2 or abs(t % 5.0 - 5.0) < step / 2:
            ctl.measure_queues(t)
    traci.close()
    wall = time.time() - t0
    summary = summarize(sc, odir, ctl.queue_log)
    summary.update({"seed": seed, "tag": tag, "wall_s": round(wall, 1)})
    json.dump(summary, open(os.path.join(odir, "summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    with open(os.path.join(odir, "queues.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ctl.queue_log[0].keys()))
        w.writeheader(); w.writerows(ctl.queue_log)
    return summary


def summarize(sc, odir, qlog):
    trips = ET.parse(os.path.join(odir, "tripinfo.xml")).getroot()
    od = {}
    allv = []
    unfinished = 0
    for tr in trips.iter("tripinfo"):
        vid = tr.get("id")
        dep = float(tr.get("depart"))
        if dep < 0:  # belum berangkat sampai akhir (tertahan di luar jaringan)
            unfinished += 1
            continue
        if not (WARMUP <= dep < WARMUP + MEASURE):
            continue
        route = vid.split("__")[0]
        dur = float(tr.get("duration")) + float(tr.get("departDelay"))
        loss = float(tr.get("timeLoss")) + float(tr.get("departDelay"))
        fin = tr.get("arrival") not in (None, "-1", "-1.00")
        if not fin:
            unfinished += 1
        rec = od.setdefault(route, {"n": 0, "tt": [], "loss": []})
        rec["n"] += 1
        rec["tt"].append(dur)
        rec["loss"].append(loss)
        allv.append(loss)
    res = {"scenario": sc, "od": {}}
    for r, rec in od.items():
        res["od"][r] = {
            "label": OD_LABEL.get(r, r),
            "n": rec["n"],
            "waktu_tempuh_rata_s": round(statistics.mean(rec["tt"]), 1),
            "waktu_tempuh_p85_s": round(sorted(rec["tt"])[int(0.85 * (len(rec["tt"]) - 1))], 1),
            "tundaan_rata_s": round(statistics.mean(rec["loss"]), 1),
        }
    res["tundaan_rata_semua_s"] = round(statistics.mean(allv), 1) if allv else None
    res["kendaraan_diukur"] = len(allv)
    res["belum_selesai"] = unfinished
    q = [r for r in qlog if WARMUP <= r["t"] < WARMUP + MEASURE]
    for k in ("turun", "naik", "gerlong"):
        vals = [r[k] for r in q]
        res[f"antrean_{k}_rata_m"] = round(statistics.mean(vals), 1)
        res[f"antrean_{k}_maks_m"] = round(max(vals), 1)
        res[f"antrean_{k}_p95_m"] = round(sorted(vals)[int(0.95 * (len(vals) - 1))], 1)
    st = ET.parse(os.path.join(odir, "stats.xml")).getroot()
    tp = st.find("teleports")
    res["teleport"] = int(tp.get("total")) if tp is not None else 0
    return res


def parse_tls(s):
    if not s:
        return None
    return {k: float(v) for k, v in (kv.split("=") for kv in s.split(","))}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--tls")
    ap.add_argument("--tag")
    ap.add_argument("--scale", type=float)
    ap.add_argument("--end", type=float, default=WARMUP + MEASURE)
    a = ap.parse_args()
    s = run(a.scenario, a.seed, a.gui, parse_tls(a.tls), a.tag, a.end, a.scale)
    print(json.dumps(s, indent=1, ensure_ascii=False))
