"""Pengendali perilaku lokal via TraCI (dipakai runner analisis & bridge 3D).

1. Manuver putar balik: lebar jalan ±7 m per arah < kebutuhan radius putar.
   - motor: langsung; mobil/angkot: tambahan 2–6 s (harus mengambil seluruh lebar lajur lawan);
   - truk/bus: manuver maju-mundur 18–35 s, sambil "mengayun" menutup lajur luar arah asal.
   Kendaraan yang berhenti di dalam simpang memblokir semua gerakan yang berpotongan (logika foe SUMO).
2. Angkot ngetem di depan / mulut Gerlong (peluang & durasi acak; dikurangi pada skenario penertiban).
3. Pengukur antrean per koridor (panjang antrean kontinu dari titik hambatan).
"""
import math
import os
import random

if os.environ.get("SIM_LIBSUMO") == "1":
    import libsumo as traci
else:
    import traci

UTURN_DELAY = {  # (min, max) detik tambahan berhenti di dalam gerakan putar balik
    "motor": (0, 0),
    "mobil": (2, 5),
    "angkot": (3, 6),
    "truk": (18, 30), "truk_naik": (18, 30),
    "bus": (20, 35), "bus_naik": (20, 35),
}
HEAVY_TYPES = {"truk", "truk_naik", "bus", "bus_naik"}

# Perilaku angkot per skenario: stopID -> (peluang berhenti, median durasi, durasi maks)
NGETEM = {
    "S0": {"halte_GG": (0.5, 10, 25), "ngetem_NB": (0.5, 15, 60), "ngetem_GER": (0.6, 18, 60)},
    "S1": {"halte_GG": (0.5, 8, 15), "ngetem_GER": (0.3, 6, 10)},
    "S2": {"halte_GG": (0.5, 10, 25), "ngetem_GER": (0.3, 6, 10)},          # penertiban ngetem
    "tahap1": {"halte_GG": (0.5, 10, 25), "ngetem_GER": (0.3, 6, 10)},      # S0 + penertiban
}

# Koridor antrean: daftar edge dari hulu ke hilir. Ujung = titik hambatan utama.
CORRIDORS = {
    "S0": {"turun": ["SB_N_B", "SB_B_G", "SB_G_A"], "naik": ["NB_S_A", "NB_A_G"], "gerlong": ["GER_in"]},
    "S1": {"turun": ["SB_N_B", "SB_B_Gq", "SB_Gq_G"], "naik": ["NB_S_A", "NB_A_G"], "gerlong": ["GER_in"]},
    "S2": {"turun": ["SB_N_B", "SB_B_Fu", "SB_Fu_G", "SB_G_A"], "naik": ["NB_S_Fd", "NB_Fd_A", "NB_A_G"], "gerlong": ["GER_in"]},
}


class Controller:
    def __init__(self, scenario, net, seed=1, uturn_on=True, ngetem_on=True):
        variant = scenario.split("_")[1] if "_" in scenario else None
        scenario = scenario.split("_")[0]
        self.sc = scenario
        self.ngetem_profile = NGETEM.get(variant, NGETEM[scenario])
        self.rng = random.Random(seed)
        self.uturn_on = uturn_on
        self.ngetem_on = ngetem_on
        self.handled = set()
        self.release = {}          # veh -> waktu lepas
        self.swing = {}            # veh -> (lane, kecepatan asli)
        self.swing_count = {}
        # lajur internal gerakan putar balik + lajur luar arah asal (yang tertutup ayunan kendaraan berat)
        self.uturn_lanes = {}
        for e in net.getEdges():
            for conns in e.getOutgoing().values():
                for c in conns:
                    if c.getDirection() in ("t", "T") and c.getViaLaneID():
                        self.uturn_lanes[c.getViaLaneID()] = e.getID() + "_0"
        self.edge_len = {e.getID(): e.getLength() for e in net.getEdges()}
        self.corr = CORRIDORS[scenario]
        self.queue_log = []
        self.lane_speed = {}

    # ------------------------------------------------------------ angkot
    def _on_depart(self, vid):
        if not self.ngetem_on:
            return
        if traci.vehicle.getTypeID(vid) != "angkot":
            return
        route = traci.vehicle.getRoute(vid)
        for stop_id, (p, med, mx) in self.ngetem_profile.items():
            lane = traci.busstop.getLaneID(stop_id)
            edge = lane.rsplit("_", 1)[0]
            if edge in route and self.rng.random() < p:
                dur = min(mx, max(3, self.rng.lognormvariate(math.log(med), 0.6)))
                try:
                    traci.vehicle.setBusStop(vid, stop_id, duration=dur)
                except traci.TraCIException:
                    pass

    # ------------------------------------------------------------ putar balik
    def _uturn(self, t):
        for via, origin_outer in self.uturn_lanes.items():
            for vid in traci.lane.getLastStepVehicleIDs(via):
                if vid in self.handled:
                    continue
                self.handled.add(vid)
                vt = traci.vehicle.getTypeID(vid)
                lo, hi = UTURN_DELAY.get(vt, (2, 5))
                if hi <= 0:
                    continue
                d = self.rng.uniform(lo, hi)
                traci.vehicle.setSpeed(vid, 0.0)
                self.release[vid] = t + d
                if vt in HEAVY_TYPES:
                    # ayunan bodi: lajur luar arah asal ikut tertutup
                    if origin_outer not in self.lane_speed:
                        self.lane_speed[origin_outer] = traci.lane.getMaxSpeed(origin_outer)
                    self.swing_count[origin_outer] = self.swing_count.get(origin_outer, 0) + 1
                    traci.lane.setMaxSpeed(origin_outer, 0.3)
                    self.swing[vid] = origin_outer
        for vid, tr in list(self.release.items()):
            if t >= tr:
                try:
                    traci.vehicle.setSpeed(vid, -1)
                except traci.TraCIException:
                    pass
                del self.release[vid]
                lane = self.swing.pop(vid, None)
                if lane:
                    self.swing_count[lane] -= 1
                    if self.swing_count[lane] <= 0:
                        traci.lane.setMaxSpeed(lane, self.lane_speed[lane])

    # ------------------------------------------------------------ antrean
    def measure_queues(self, t):
        row = {"t": t}
        for name, edges in self.corr.items():
            total = sum(self.edge_len[e] for e in edges)
            vehs = []
            acc = 0.0
            for e in edges:
                for vid in traci.edge.getLastStepVehicleIDs(e):
                    pos = traci.vehicle.getLanePosition(vid)
                    vehs.append((total - (acc + pos), traci.vehicle.getSpeed(vid)))
                acc += self.edge_len[e]
            vehs.sort()
            # Panjang tersendat = jumlah rentang rantai kendaraan lambat (<2 m/s, jarak antar < 25 m),
            # di mana pun letaknya (menangkap antrean di bukaan B maupun di simpang/lampu).
            jam, head, last = 0.0, None, None
            for dist, spd in vehs:
                if spd >= 2.0:
                    continue
                if head is None:
                    head = last = dist
                elif dist - last < 25:
                    last = dist
                else:
                    jam += last - head + 6
                    head = last = dist
            if head is not None:
                jam += last - head + 6
            row[name] = round(jam, 1)
            row[name + "_n"] = len(vehs)
        self.queue_log.append(row)
        return row

    # ------------------------------------------------------------ langkah
    def step(self, t):
        for vid in traci.simulation.getDepartedIDList():
            self._on_depart(vid)
        if self.uturn_on:
            self._uturn(t)
        for vid in traci.simulation.getArrivedIDList():
            self.handled.discard(vid)
