"""Jembatan SUMO ↔ browser (Three.js).

- Menyajikan folder web/ di http://127.0.0.1:8000
- WebSocket ws://localhost:8765 : kirim posisi kendaraan (live), terima perintah & pose kendaraan ego.
- Kendaraan yang dikemudikan pengguna dimasukkan ke SUMO (moveToXY) sehingga kendaraan lain bereaksi.

Jalankan:  python bridge/server.py      lalu buka http://127.0.0.1:8000
"""
import asyncio
import functools
import http.server
import json
import math
import os
import queue
import socketserver
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ["SIM_LIBSUMO"] = "1"

import libsumo as traci  # noqa: E402
import sumo  # noqa: E402
import sumolib  # noqa: E402
from libsumo import constants as tc  # noqa: E402
from websockets.asyncio.server import serve  # noqa: E402

import make_scenario  # noqa: E402
from control import Controller  # noqa: E402

HTTP_PORT, WS_PORT = 8000, 8765
STEP = 0.2
TYPE_CODE = {"motor": 0, "mobil": 1, "angkot": 2, "truk": 3, "truk_naik": 3, "bus": 4, "bus_naik": 4, "ego": 9}
SCENARIOS = {
    "S0": {"base": "S0", "variant": None, "label": "S0 Eksisting (pagar baru, bukaan A & B)"},
    "S0_tahap1": {"base": "S0", "variant": "tahap1", "label": "Tahap 1: larang truk/bus putar balik + tertib angkot"},
    "S1": {"base": "S1", "variant": None, "label": "S1: APILL adaptif + lajur khusus belok kanan"},
    "S2": {"base": "S2", "variant": None, "label": "S2: U-turn layang"},
}
SPAWN = {  # titik muncul kendaraan ego: (calon edge, jarak dari ujung hilir edge)
    "lembang": (["SB_N_B"], 140),
    "bawah": (["NB_S_A", "NB_S_Fd"], 120),
    "gerlong": (["GER_in"], 110),
}
EGO_VTYPES = {"motor", "mobil", "angkot", "truk", "bus"}


class Sim(threading.Thread):
    """Satu thread memegang libsumo (tidak thread-safe)."""

    def __init__(self, out):
        super().__init__(daemon=True)
        self.cmds = queue.Queue()
        self.out = out  # fungsi broadcast(dict)
        self.running = False
        self.paused = False
        self.speed = 1.0
        self.sc = None
        self.ego = None          # dict pose terakhir dari klien
        self.ego_in = False
        self.ids = {}
        self.next_id = 1
        self.vlen = {}

    # -------------------------------------------------------------- perintah
    def post(self, msg):
        self.cmds.put(msg)

    def _start(self, msg):
        if self.running:
            traci.close()
            self.running = False
        key = msg.get("scenario", "S0")
        cfg = SCENARIOS[key]
        scale = float(msg.get("scale", 1.0))
        seed = int(msg.get("seed", 1))
        folder = f"live_{key}"
        make_scenario.make(cfg["base"], scale, cfg["variant"], folder=folder, step=STEP)
        sdir = os.path.join(ROOT, "scenarios", folder)
        traci.start([os.path.join(sumo.SUMO_HOME, "bin", "sumo"), "-c", os.path.join(sdir, "sim.sumocfg"),
                     "--seed", str(seed), "--no-warnings", "true", "--end", "100000"])
        self.net = sumolib.net.readNet(os.path.join(ROOT, "net", cfg["base"], "net.net.xml"), withInternal=True)
        self.ctl = Controller(key, self.net, seed=seed)
        self.sc = key
        self.running = True
        self.paused = False
        self.ids, self.next_id, self.vlen = {}, 1, {}
        self.ego, self.ego_in = None, False
        self.last_stats = -999.0
        self.has_tls = "G" in traci.trafficlight.getIDList()
        spawns = {}
        for k, (edges, back) in SPAWN.items():
            for e in edges:
                try:
                    ed = self.net.getEdge(e)
                except KeyError:
                    continue
                ln = ed.getLanes()[0 if k != "lembang" else 1]
                pos = max(5.0, ln.getLength() - back)
                x, y = sumolib.geomhelper.positionAtShapeOffset(ln.getShape(), pos)
                x2, y2 = sumolib.geomhelper.positionAtShapeOffset(ln.getShape(), pos + 2)
                spawns[k] = {"edge": e, "lane": ln.getIndex(), "pos": pos, "x": x, "y": y,
                             "a": math.degrees(math.atan2(y2 - y, x2 - x))}
                break
        self.spawns = spawns
        self.out({"type": "started", "scenario": key, "label": cfg["label"], "tls": self.has_tls,
                  "spawns": spawns, "scale": scale, "step": STEP})

    def _ego_spawn(self, msg):
        if not self.running:
            return
        vt = msg.get("vtype", "mobil")
        vt = vt if vt in EGO_VTYPES else "mobil"
        at = msg.get("at", "lembang")
        sp = self.spawns[at]
        self._ego_remove()
        rid = f"ego_r_{int(time.time() * 1000)}"
        traci.route.add(rid, [sp["edge"]])
        traci.vehicle.add("ego", rid, typeID=vt, depart="now", departLane=str(sp["lane"]),
                          departPos=str(sp["pos"]), departSpeed="0")
        traci.vehicle.setColor("ego", (230, 30, 60, 255))
        traci.vehicle.setSpeedMode("ego", 0)
        traci.vehicle.setLaneChangeMode("ego", 0)
        self.ego = {"x": sp["x"], "y": sp["y"], "a": sp["a"], "v": 0.0, "edge": sp["edge"], "vtype": vt}
        self.ego_in = True
        self.out({"type": "ego_spawned", "vtype": vt, "pose": sp})

    def _ego_remove(self):
        if self.ego_in:
            try:
                traci.vehicle.remove("ego")
            except traci.TraCIException:
                pass
        self.ego, self.ego_in = None, False

    def _apply_ego(self):
        if not (self.ego and self.ego_in):
            return
        e = self.ego
        nav = 90.0 - e["a"]  # SUMO: 0 = utara, searah jarum jam
        try:
            traci.vehicle.moveToXY("ego", e.get("edge") or "", -1, e["x"], e["y"], nav % 360, keepRoute=2,
                                   matchThreshold=25)
            traci.vehicle.setPreviousSpeed("ego", max(0.0, e["v"]))
        except traci.TraCIException:
            pass

    def handle(self, msg):
        c = msg.get("cmd")
        if c == "start":
            self._start(msg)
        elif c == "pause":
            self.paused = bool(msg.get("value", not self.paused))
        elif c == "speed":
            self.speed = max(0.25, min(20.0, float(msg.get("value", 1))))
        elif c == "ego_spawn":
            self._ego_spawn(msg)
        elif c == "ego":
            if self.ego is not None:
                self.ego.update({k: msg[k] for k in ("x", "y", "a", "v", "edge") if k in msg})
        elif c == "ego_remove":
            self._ego_remove()
            self.out({"type": "ego_gone", "reason": "dihapus"})

    # -------------------------------------------------------------- loop
    def run(self):
        last_send = 0.0
        self.last_stats = -999.0
        t_wall = time.perf_counter()
        while True:
            try:
                while True:
                    self.handle(self.cmds.get_nowait())
            except queue.Empty:
                pass
            if not self.running or self.paused:
                time.sleep(0.03)
                t_wall = time.perf_counter()
                continue
            try:
                last_send = self._step(last_send)
            except Exception as ex:  # satu langkah gagal tidak boleh mematikan simulasi
                import traceback
                traceback.print_exc()
                self.out({"type": "error", "msg": f"{type(ex).__name__}: {ex}"})
            # pacing waktu nyata × kecepatan
            t_wall += STEP / self.speed
            delay = t_wall - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            elif delay < -1.0:
                t_wall = time.perf_counter()

    def _step(self, last_send):
            self._apply_ego()
            traci.simulationStep()
            t = traci.simulation.getTime()
            for vid in traci.simulation.getDepartedIDList():
                traci.vehicle.subscribe(vid, [tc.VAR_POSITION3D, tc.VAR_ANGLE, tc.VAR_SPEED, tc.VAR_SIGNALS])
                self.ids[vid] = self.next_id
                self.next_id += 1
                self.vlen[vid] = (TYPE_CODE.get(traci.vehicle.getTypeID(vid), 1) if vid != "ego" else 9)
            for vid in traci.simulation.getArrivedIDList():
                self.ids.pop(vid, None)
                self.vlen.pop(vid, None)
                if vid == "ego":
                    self.ego, self.ego_in = None, False
                    self.out({"type": "ego_gone", "reason": "keluar area simulasi"})
            self.ctl.step(t)
            now = time.perf_counter()
            if now - last_send >= 1 / 12:
                last_send = now
                subs = traci.vehicle.getAllSubscriptionResults()
                vs = []
                for vid, r in subs.items():
                    if vid not in self.ids:
                        continue
                    pos = r.get(tc.VAR_POSITION3D)
                    if not pos or tc.VAR_ANGLE not in r:
                        continue
                    x, y = pos[0], pos[1]
                    z = pos[2] if len(pos) > 2 else 0.0
                    vs.append([self.ids[vid], self.vlen.get(vid, 1), round(x, 2), round(y, 2), round(z, 2),
                               round(r[tc.VAR_ANGLE], 1), round(r[tc.VAR_SPEED], 2), int(r[tc.VAR_SIGNALS])])
                frame = {"type": "frame", "t": t, "v": vs}
                if self.has_tls:
                    frame["tl"] = traci.trafficlight.getRedYellowGreenState("G")
                if self.ego_in and "ego" in subs:
                    frame["ego"] = {"edge": traci.vehicle.getRoadID("ego"),
                                    "lane": traci.vehicle.getLaneIndex("ego"),
                                    "wait": traci.vehicle.getWaitingTime("ego")}
                self.out(frame)
            if t - self.last_stats >= 5.0:
                self.last_stats = t
                q = self.ctl.measure_queues(t)
                n = traci.vehicle.getIDCount()
                speeds = [r[tc.VAR_SPEED] for r in traci.vehicle.getAllSubscriptionResults().values() if tc.VAR_SPEED in r]
                self.out({"type": "stats", "t": t, "n": n, "pending": len(traci.simulation.getPendingVehicles()),
                          "vmean": round(sum(speeds) / len(speeds) * 3.6, 1) if speeds else 0,
                          "q": {k: q[k] for k in ("turun", "naik", "gerlong")}})
            return last_send


# ------------------------------------------------------------------ WebSocket & HTTP
CLIENTS = set()
LOOP = None


def broadcast(msg):
    data = json.dumps(msg, separators=(",", ":"))
    for ws in list(CLIENTS):
        LOOP.call_soon_threadsafe(asyncio.ensure_future, _send(ws, data))


async def _send(ws, data):
    try:
        await ws.send(data)
    except Exception:
        CLIENTS.discard(ws)


async def handler(ws):
    CLIENTS.add(ws)
    await ws.send(json.dumps({"type": "hello", "scenarios": {k: v["label"] for k, v in SCENARIOS.items()}}))
    try:
        async for raw in ws:
            try:
                SIM.post(json.loads(raw))
            except json.JSONDecodeError:
                pass
    finally:
        CLIENTS.discard(ws)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def http_thread():
    h = functools.partial(QuietHandler, directory=os.path.join(ROOT, "web"))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", HTTP_PORT), h) as httpd:
        httpd.serve_forever()


async def main():
    global LOOP
    LOOP = asyncio.get_running_loop()
    async with serve(handler, "127.0.0.1", WS_PORT, max_size=2 ** 22):
        print(f"Simulasi 3D siap: buka http://127.0.0.1:{HTTP_PORT}  (Ctrl+C untuk berhenti)", flush=True)
        if "--no-browser" not in sys.argv:
            webbrowser.open(f"http://127.0.0.1:{HTTP_PORT}")
        await asyncio.Future()


SIM = Sim(broadcast)

if __name__ == "__main__":
    threading.Thread(target=http_thread, daemon=True).start()
    SIM.start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
