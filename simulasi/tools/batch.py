"""Jalankan semua skenario × seed secara paralel, lalu buat laporan.

python tools/batch.py                 (S0, S0_tahap1, S1, S2 × seed 1..3)
python tools/batch.py --seeds 1 2 --jobs 4
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scen", nargs="*", default=["S0", "S0_tahap1", "S1", "S2"])
    ap.add_argument("--seeds", nargs="*", type=int, default=[1, 2, 3])
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    logs = os.path.join(ROOT, "results", "logs")
    os.makedirs(logs, exist_ok=True)
    todo = [(s, k) for s in a.scen for k in a.seeds]
    running = []
    t0 = time.time()
    while todo or running:
        while todo and len(running) < a.jobs:
            s, k = todo.pop(0)
            tag = f"{s}_seed{k}"
            f = open(os.path.join(logs, tag + ".log"), "w")
            p = subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "run.py"), s, "--seed", str(k), "--tag", tag],
                                 stdout=f, stderr=subprocess.STDOUT, env=env, cwd=ROOT)
            running.append((p, tag, f))
            print(f"[{time.time() - t0:6.0f}s] mulai {tag}", flush=True)
        for item in list(running):
            p, tag, f = item
            if p.poll() is not None:
                f.close()
                running.remove(item)
                print(f"[{time.time() - t0:6.0f}s] selesai {tag} rc={p.returncode}", flush=True)
        time.sleep(3)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "report.py")], env=env, cwd=ROOT)
    print("SEMUA SELESAI", flush=True)
