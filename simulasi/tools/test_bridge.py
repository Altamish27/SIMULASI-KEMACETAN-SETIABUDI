"""Uji protokol jembatan: start skenario, terima frame, spawn ego, kemudikan lurus beberapa detik.

python tools/test_bridge.py S2
"""
import asyncio
import json
import math
import sys

from websockets.asyncio.client import connect


async def main(sc):
    async with connect("ws://127.0.0.1:8765", max_size=2 ** 23) as ws:
        hello = json.loads(await ws.recv())
        print("hello:", list(hello["scenarios"]))
        await ws.send(json.dumps({"cmd": "start", "scenario": sc, "scale": 1.0, "seed": 3}))
        await ws.send(json.dumps({"cmd": "speed", "value": 20}))
        started = None
        frames = stats = 0
        ego_pose = None
        t_end = asyncio.get_event_loop().time() + 40
        spawned_at = None
        x = y = a = None
        while asyncio.get_event_loop().time() < t_end:
            m = json.loads(await ws.recv())
            if m["type"] == "started":
                started = m
                print("started:", m["label"], "spawns:", {k: (round(v["x"], 1), round(v["y"], 1)) for k, v in m["spawns"].items()})
            elif m["type"] == "frame":
                frames += 1
                if frames % 60 == 0:
                    types = {}
                    for v in m["v"]:
                        types[v[1]] = types.get(v[1], 0) + 1
                    print(f"  frame t={m['t']:.0f}s kendaraan={len(m['v'])} jenis={types} tl={m.get('tl')} ego={m.get('ego')}")
                if frames == 150 and spawned_at is None:
                    await ws.send(json.dumps({"cmd": "speed", "value": 1}))
                    await ws.send(json.dumps({"cmd": "ego_spawn", "vtype": "mobil", "at": "lembang"}))
                    spawned_at = m["t"]
                if ego_pose is not None and x is not None:
                    # kemudikan maju 8 m/s ke arah awal
                    x += math.cos(math.radians(a)) * 8 * 0.08
                    y += math.sin(math.radians(a)) * 8 * 0.08
                    await ws.send(json.dumps({"cmd": "ego", "x": x, "y": y, "a": a, "v": 8.0, "edge": ""}))
            elif m["type"] == "stats":
                stats += 1
                print("  stats:", {k: m[k] for k in ("t", "n", "pending", "vmean", "q")})
            elif m["type"] == "ego_spawned":
                ego_pose = m["pose"]
                x, y, a = ego_pose["x"], ego_pose["y"], ego_pose["a"]
                print("ego_spawned:", m["vtype"], {k: round(v, 1) if isinstance(v, float) else v for k, v in ego_pose.items()})
            elif m["type"] == "ego_gone":
                print("ego_gone:", m)
        print(f"selesai: frames={frames} stats={stats}")


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "S0"))
