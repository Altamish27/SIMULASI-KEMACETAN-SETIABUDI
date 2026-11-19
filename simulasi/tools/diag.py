"""Diagnosis: jalankan skenario sampai waktu T lalu tampilkan kendaraan terdepan per edge & isi simpang.

python tools/diag.py S0 600 NB_A_G,NB_S_A,SB_G_A
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import geo  # noqa: E402
import sumo  # noqa: E402
import sumolib  # noqa: E402
import traci  # noqa: E402
from control import Controller  # noqa: E402

sc, T = sys.argv[1], float(sys.argv[2])
edges = sys.argv[3].split(",")
net = sumolib.net.readNet(os.path.join(geo.ROOT, "net", sc, "net.net.xml"), withInternal=True)
traci.start([os.path.join(sumo.SUMO_HOME, "bin", "sumo"), "-c", os.path.join(geo.ROOT, "scenarios", sc, "sim.sumocfg"),
             "--seed", "1", "--no-warnings", "true"])
ctl = Controller(sc, net)
t = 0
while t < T:
    traci.simulationStep()
    t = traci.simulation.getTime()
    ctl.step(t)
print("t =", t, "running", traci.vehicle.getIDCount(), "pending", len(traci.simulation.getPendingVehicles()))
for j in ("A", "G", "B", "Gq", "Fu", "Fd"):
    lanes = [l for l in traci.lane.getIDList() if l.startswith(":" + j + "_")]
    occ = [(l, [(v, traci.vehicle.getTypeID(v), round(traci.vehicle.getSpeed(v), 1), round(traci.vehicle.getWaitingTime(v)))
                for v in traci.lane.getLastStepVehicleIDs(l)]) for l in lanes]
    occ = [o for o in occ if o[1]]
    if occ:
        print("simpang", j, occ)
for e in edges:
    vs = sorted(traci.edge.getLastStepVehicleIDs(e), key=lambda v: -traci.vehicle.getLanePosition(v))[:6]
    print("edge", e, "n", traci.edge.getLastStepVehicleNumber(e), "halt", traci.edge.getLastStepHaltingNumber(e))
    for v in vs:
        print("   ", v, traci.vehicle.getTypeID(v), "lane", traci.vehicle.getLaneIndex(v),
              "pos", round(traci.vehicle.getLanePosition(v), 1), "spd", round(traci.vehicle.getSpeed(v), 2),
              "wait", round(traci.vehicle.getWaitingTime(v)), "leader", traci.vehicle.getLeader(v, 30),
              "route", traci.vehicle.getRoute(v)[-1], "stopped", traci.vehicle.isStopped(v))
traci.close()
